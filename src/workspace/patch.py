
# There is a problem with quota enforcement in swift client.....

# https://github.com/openstack/python-swiftclient/blob/e65070964c7b1e04119c87e5f344d39358780d18/swiftclient/service.py#L2235
# content-length is only set if we upload a local file from a path on the file system.....
# any source will take the other code-path where, content-length get's set to None.

# Additionally, swiftclient.utils.LengthWrapper tests if a stream is seekable,
# however this test fails on non seekable io.BufferedReader, because it checks
# just for 'seek' attribute availability instead of calling 'seekable' on io.XXX object.

# There are probably a couple of ways to fix this:
# - patch as it is (requires user to wrap file like object in LengthWrapper)
# - respect 'Content-Length' header option  (may require this code to wrap
#      file like object in LengthWrapper if content-length is available,
#      because my file-like object doesn't close automatically, even if there is no more data incoming)

# Use case:
#   pass web request.body_file on directly to swift. this body_file doesn't get closed by the client,
#   so we need some iterator, that stops after content-length bytes. (ReadableIterator, doesn't work here,
#   and will hang forever waiting for more bytes.)

# Patch it here four our use case only...

from errno import ENOENT
from os.path import (
    getmtime, getsize
)
from time import time
from six import text_type
from six.moves.urllib.parse import quote

from swiftclient.utils import (
    config_true_value, ReadableToIterable, LengthWrapper,
    report_traceback
)
from swiftclient.exceptions import ClientException

from swiftclient.service import (
    logger, split_headers, interruptable_as_completed,
    DISK_BUFFER, SwiftError
)
from swiftclient.service import SwiftService


def _upload_object_job(self, conn, container, source, obj, options,
                       results_queue=None):
    if obj.startswith('./') or obj.startswith('.\\'):
        obj = obj[2:]
    if obj.startswith('/'):
        obj = obj[1:]
    res = {
        'action': 'upload_object',
        'container': container,
        'object': obj
    }
    if hasattr(source, 'read'):
        stream = source
        path = None
    else:
        path = source
    res['path'] = path
    try:
        if path is not None:
            put_headers = {'x-object-meta-mtime': "%f" % getmtime(path)}
        else:
            put_headers = {'x-object-meta-mtime': "%f" % round(time())}
        res['headers'] = put_headers
        # We need to HEAD all objects now in case we're overwriting a
        # manifest object and need to delete the old segments
        # ourselves.
        old_manifest = None
        old_slo_manifest_paths = []
        new_slo_manifest_paths = set()
        segment_size = int(0 if options['segment_size'] is None
                           else options['segment_size'])
        if (options['changed'] or options['skip_identical']
                or not options['leave_segments']):
            try:
                headers = conn.head_object(container, obj)
                is_slo = config_true_value(
                    headers.get('x-static-large-object'))
                if options['skip_identical'] or (
                        is_slo and not options['leave_segments']):
                    chunk_data = self._get_chunk_data(
                        conn, container, obj, headers)

                if options['skip_identical'] and self._is_identical(
                        chunk_data, path):
                    res.update({
                        'success': True,
                        'status': 'skipped-identical'
                    })
                    return res
                cl = int(headers.get('content-length'))
                mt = headers.get('x-object-meta-mtime')
                if (path is not None and options['changed']
                        and cl == getsize(path)
                        and mt == put_headers['x-object-meta-mtime']):
                    res.update({
                        'success': True,
                        'status': 'skipped-changed'
                    })
                    return res
                if not options['leave_segments']:
                    old_manifest = headers.get('x-object-manifest')
                    if is_slo:
                        for old_seg in chunk_data:
                            seg_path = old_seg['name'].lstrip('/')
                            if isinstance(seg_path, text_type):
                                seg_path = seg_path.encode('utf-8')
                            old_slo_manifest_paths.append(seg_path)
            except ClientException as err:
                if err.http_status != 404:
                    traceback, err_time = report_traceback()
                    logger.exception(err)
                    res.update({
                        'success': False,
                        'error': err,
                        'traceback': traceback,
                        'error_timestamp': err_time
                    })
                    return res
        # Merge the command line header options to the put_headers
        put_headers.update(split_headers(
            options['meta'], 'X-Object-Meta-'))
        put_headers.update(split_headers(options['header'], ''))
        # Don't do segment job if object is not big enough, and never do
        # a segment job if we're reading from a stream - we may fail if we
        # go over the single object limit, but this gives us a nice way
        # to create objects from memory
        if (path is not None and segment_size
                and (getsize(path) > segment_size)):
            res['large_object'] = True
            seg_container = container + '_segments'
            if options['segment_container']:
                seg_container = options['segment_container']
            full_size = getsize(path)
            segment_futures = []
            segment_pool = self.thread_manager.segment_pool
            segment = 0
            segment_start = 0
            while segment_start < full_size:
                if segment_start + segment_size > full_size:
                    segment_size = full_size - segment_start
                if options['use_slo']:
                    segment_name = '%s/slo/%s/%s/%s/%08d' % (
                        obj, put_headers['x-object-meta-mtime'],
                        full_size, options['segment_size'], segment
                    )
                else:
                    segment_name = '%s/%s/%s/%s/%08d' % (
                        obj, put_headers['x-object-meta-mtime'],
                        full_size, options['segment_size'], segment
                    )
                seg = segment_pool.submit(
                    self._upload_segment_job, path, container,
                    segment_name, segment_start, segment_size, segment,
                    obj, options, results_queue=results_queue
                )
                segment_futures.append(seg)
                segment += 1
                segment_start += segment_size

            segment_results = []
            errors = False
            exceptions = []
            for f in interruptable_as_completed(segment_futures):
                try:
                    r = f.result()
                    if not r['success']:
                        errors = True
                    segment_results.append(r)
                except Exception as err:
                    traceback, err_time = report_traceback()
                    logger.exception(err)
                    errors = True
                    exceptions.append((err, traceback, err_time))
            if errors:
                err = ClientException(
                    'Aborting manifest creation '
                    'because not all segments could be uploaded. %s/%s'
                    % (container, obj))
                res.update({
                    'success': False,
                    'error': err,
                    'exceptions': exceptions,
                    'segment_results': segment_results
                })
                return res
            res['segment_results'] = segment_results

            if options['use_slo']:
                response = self._upload_slo_manifest(
                    conn, segment_results, container, obj, put_headers)
                res['manifest_response_dict'] = response
                new_slo_manifest_paths = {
                    seg['segment_location'] for seg in segment_results}
            else:
                new_object_manifest = '%s/%s/%s/%s/%s/' % (
                    quote(seg_container.encode('utf8')),
                    quote(obj.encode('utf8')),
                    put_headers['x-object-meta-mtime'], full_size,
                    options['segment_size'])
                if old_manifest and old_manifest.rstrip('/') == \
                        new_object_manifest.rstrip('/'):
                    old_manifest = None
                put_headers['x-object-manifest'] = new_object_manifest
                mr = {}
                conn.put_object(
                    container, obj, '', content_length=0,
                    headers=put_headers,
                    response_dict=mr
                )
                res['manifest_response_dict'] = mr
        elif options['use_slo'] and segment_size and not path:
            segment = 0
            results = []
            while True:
                segment_name = '%s/slo/%s/%s/%08d' % (
                    obj, put_headers['x-object-meta-mtime'],
                    segment_size, segment
                )
                seg_container = container + '_segments'
                if options['segment_container']:
                    seg_container = options['segment_container']
                ret = self._upload_stream_segment(
                    conn, container, obj,
                    seg_container,
                    segment_name,
                    segment_size,
                    segment,
                    put_headers,
                    stream
                )
                if not ret['success']:
                    return ret
                if (ret['complete'] and segment == 0) or\
                        ret['segment_size'] > 0:
                    results.append(ret)
                if results_queue is not None:
                    # Don't insert the 0-sized segments or objects
                    # themselves
                    if ret['segment_location'] != '/%s/%s' % (
                            container, obj) and ret['segment_size'] > 0:
                        results_queue.put(ret)
                if ret['complete']:
                    break
                segment += 1
            if results[0]['segment_location'] != '/%s/%s' % (
                    container, obj):
                response = self._upload_slo_manifest(
                    conn, results, container, obj, put_headers)
                res['manifest_response_dict'] = response
                new_slo_manifest_paths = {
                    r['segment_location'] for r in results}
                res['large_object'] = True
            else:
                res['response_dict'] = ret
                res['large_object'] = False
        else:
            res['large_object'] = False
            obr = {}
            fp = None
            try:
                if path is not None:
                    content_length = getsize(path)
                    fp = open(path, 'rb', DISK_BUFFER)
                    contents = LengthWrapper(fp,
                                             content_length,
                                             md5=options['checksum'])
                # TODO: patch here ... check if stream is already a LengthWrapper,
                #       and use it.
                elif isinstance(stream, LengthWrapper):
                    content_length = stream._length
                    contents = stream
                # TODO: patch end
                else:
                    content_length = None
                    contents = ReadableToIterable(stream,
                                                  md5=options['checksum'])
                etag = conn.put_object(
                    container, obj, contents,
                    content_length=content_length, headers=put_headers,
                    response_dict=obr
                )
                res['response_dict'] = obr
                if (options['checksum'] and
                        etag and etag != contents.get_md5sum()):
                    raise SwiftError(
                        'Object upload verification failed: '
                        'md5 mismatch, local {0} != remote {1} '
                        '(remote object has not been removed)'
                        .format(contents.get_md5sum(), etag))
            finally:
                if fp is not None:
                    fp.close()
        if old_manifest or old_slo_manifest_paths:
            drs = []
            delobjsmap = {}
            if old_manifest:
                scontainer, sprefix = old_manifest.split('/', 1)
                sprefix = sprefix.rstrip('/') + '/'
                delobjsmap[scontainer] = []
                for part in self.list(scontainer, {'prefix': sprefix}):
                    if not part["success"]:
                        raise part["error"]
                    delobjsmap[scontainer].extend(
                        seg['name'] for seg in part['listing'])
            if old_slo_manifest_paths:
                for seg_to_delete in old_slo_manifest_paths:
                    if seg_to_delete in new_slo_manifest_paths:
                        continue
                    scont, sobj = \
                        seg_to_delete.split(b'/', 1)
                    delobjs_cont = delobjsmap.get(scont, [])
                    delobjs_cont.append(sobj)
                    delobjsmap[scont] = delobjs_cont
            del_segs = []
            for dscont, dsobjs in delobjsmap.items():
                for dsobj in dsobjs:
                    del_seg = self.thread_manager.segment_pool.submit(
                        self._delete_segment, dscont, dsobj,
                        results_queue=results_queue
                    )
                    del_segs.append(del_seg)
            for del_seg in interruptable_as_completed(del_segs):
                drs.append(del_seg.result())
            res['segment_delete_results'] = drs

        # return dict for printing
        res.update({
            'success': True,
            'status': 'uploaded',
            'attempts': conn.attempts})
        return res
    except OSError as err:
        traceback, err_time = report_traceback()
        logger.exception(err)
        if err.errno == ENOENT:
            error = SwiftError('Local file %r not found' % path, exc=err)
        else:
            error = err
        res.update({
            'success': False,
            'error': error,
            'traceback': traceback,
            'error_timestamp': err_time
        })
    except Exception as err:
        traceback, err_time = report_traceback()
        logger.exception(err)
        res.update({
            'success': False,
            'error': err,
            'traceback': traceback,
            'error_timestamp': err_time
        })
    return res


SwiftService._upload_object_job = _upload_object_job

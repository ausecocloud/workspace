FROM python:3.6

COPY . /code/workspace/

RUN cd /code \
 && pip install --upgrade pip setuptools \
 && pip install --upgrade https://github.com/p1c2u/openapi-core/archive/master.zip \
 && pip install --upgrade https://github.com/ausecocloud/pyramid_oidc/archive/master.zip \
 && pip install --upgrade https://github.com/ausecocloud/pyramid_cors/archive/master.zip \
 && pip install --upgrade https://github.com/ausecocloud/pyramid_openapi/archive/master.zip \
 && pip install -e workspace \
 && pip install ipdb \
                pyramid_debugtoolbar \
                pyramid_debugtoolbar_dogpile \
                waitress \
                redis

CMD pserve /code/workspace/development.ini --reload

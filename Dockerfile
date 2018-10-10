FROM python:3.6

RUN pip install --no-cache --upgrade pip setuptools \
 && pip install --no-cache --upgrade \
     gunicorn \
     PasteScript \
     openapi-core==0.6.0 \
     https://github.com/ausecocloud/pyramid_oidc/archive/225cf893df5ad21c73c4a4d4032359c7d149e34e.zip \
     https://github.com/ausecocloud/pyramid_cors/archive/05ce90ce730e5b462731c2bb90cb73b75b55bb51.zip \
     https://github.com/ausecocloud/pyramid_openapi/archive/5a6efa41128c8b1fe708398af14a0f3bbb66c88f.zip \
     https://github.com/ausecocloud/workspace/archive/84c989e33ccd32700978a5e25b1c4aa1001a8fa5.zip

CMD ["gunicorn", "--paste", "/etc/workspace/production.ini"]

FROM python:3.6

RUN pip install --no-cache --upgrade pip setuptools \
 && pip install --no-cache --upgrade \
     gunicorn \
     PasteScript \
     openapi-core==0.6.0 \
     https://github.com/ausecocloud/pyramid_oidc/archive/76e8ad10fdc49d19df2e6a0a50c7b3e36d728c6b.zip \
     https://github.com/ausecocloud/pyramid_cors/archive/05ce90ce730e5b462731c2bb90cb73b75b55bb51.zip \
     https://github.com/ausecocloud/pyramid_openapi/archive/5a6efa41128c8b1fe708398af14a0f3bbb66c88f.zip \
     https://github.com/ausecocloud/workspace/archive/2e2eac33dc961a4092c1c84b7033e4f23ec46854.zip

CMD ["gunicorn", "--paste", "/etc/workspace/production.ini"]

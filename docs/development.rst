
Build:
======

This step is optional, because docker-compose should run ``build`` automatically.

.. code:: bash

    docker-compose build


Create .env file:
=================

.. code:: bash

    # all these settings can be found in your openstack.rc file
    OS_AUTH_URL=
    OS_USERNAME=
    OS_PASSWORD=
    OS_AUTH_TYPE=
    OS_PROJECT_ID=
    OS_PROJECT_NAME=
    OS_USER_DOMAIN_NAME=
    OS_PROJECT_DOMAIN_NAME=
    OS_REGION_NAME=
    OS_INTERFACE=
    OS_IDENTITY_API_VERSION=
    # set this if the discovered storage url does'nt suite.
    OS_STORAGE_URL=

    # Workspace app settings
    # the container name to use
    WORKSPACE_CONTAINER=
    # pwgen -cns 32
    WORKSPACE_TEMP_URL_KEY=

    # Openid Connect and OAuth settings
    OAUTHLIB_INSECURE_TRANSPORT=1
    OIDC_ISSUER=
    OIDC_CLIENT_ID=
    OIDC_CLIENT_SECRET=

    # Session secret is optional, there is a default in the ini file that's ok to
    # use for development
    # pwgen -cns 64
    SESSION_SECRET=

First time:
===========

.. code:: bash

    docker-compose run --rm workspace pip install -e /code/workspace

Start service:
==============

.. code:: bash

    docker-compose up

or

.. code:: bash

    docker-compose run --rm --service-ports workspace bash

    pserve /code/workspace/development.ini --reload


Access:
=======

    http://localhost:6543/

    http://localhost:6543/swagger

    http://localhost:6543/redoc




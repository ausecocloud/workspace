
# ecocloud Workspace API

**Requirements**
 - PIP
 - Docker (docker-compose)


## Development deployment
Clone workspace repo

Create .env file from below, filling in the blanks

```
### all these settings can be found in your openstack.rc file

### downloadable from [https://dashboard.rc.nectar.org.au/project/access_and_security/](https://dashboard.rc.nectar.org.au/project/access_and_security/)
OS_AUTH_URL=###
OS_AUTH_TYPE=password
OS_USERNAME=###
OS_PROJECT_ID=###
OS_PROJECT_NAME=###
OS_USER_DOMAIN_NAME=Default
OS_PROJECT_DOMAIN_NAME=Default

OS_PASSWORD=MWRmZWIwYjNlODk3OWMx
OS_STORAGE_URL=https://swift.rc.nectar.org.au/v1/AUTH_[### OS_PROJECT_ID]
OS_REGION_NAME=###
OS_INTERFACE=public
OS_IDENTITY_API_VERSION=3

# workspace
WORKSPACE_CONTAINER=ecocloud_dev
# openssl rand 32 -hex
WORKSPACE_TEMP_URL_KEY=[use command above to generate a key]

# OpenID Connect and OAuth Settings
OAUTHLIB_INSECURE_TRANSPORT=1
OAUTHLIB_RELAX_TOKEN_SCOPE=1
OIDC_ISSUER=[can be found at *link to tpm*]
OIDC_CLIENT_ID=local
OIDC_CLIENT_SECRET=[can be found at *link to tpm*]

# Session secret is optional
# openssl rand 32 -hex
SESSION_SECRET=[use command above to generate a key]

```

First time setup
```sh
docker-compose run workspace bash

pip install -e /code/workspace

exit
```

To start services
```sh
docker-compose up
```
Visit [http://localhost:6543/swagger](http://localhost:6543/swagger) to confirm working service/api

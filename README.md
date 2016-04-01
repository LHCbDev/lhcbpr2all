# LHCbPR service


## Installation

1. `git clone ssh://git@gitlab.cern.ch:7999/lhcb-core/LHCbPR2BE`
1. `cd LHCbPR2BE`
1. `cp site/settings/private.default.py site/settings/private.py`
1. Setup and activate virtual environment (see below)
1. Run dev server: `./scripts/runserver`  (at local server)

### Virtual environment

Site is tested only with python2, so you need to setup only python virtual environment 


```sh
virtualenv venv # at LHCbPR2BE folder. Use -p option if you need to select python executable
source venv/bin/activate
```


## Configuration

`./scripts/runserver <YOURENV> ` if it exists the file ./envs/YOURENV.env then the configuration is loaded from this file.

** Default configuration **

```DJANGO_SECRET_KEY=PutYourKey
DJANGO_STATIC_URL=/api/static/

DJANGO_HTTP_PORT=8080
DJANGO_LOG_LEVEL=INFO

DB_ENGINE=django.db.backends.sqlite3
DB_HOST=
DB_USER=
DB_PASSWORD=
DB_DATABASE=lhcbprdev
DB_PORT=

DATA_ROOT=data
```

* `DB_*`` parameters corresponds to the standart DJANGO database configuraiton
* `DATA_ROOT` points to the folder with jobs output files.


## Import zip files
Zip files contains [handlers' results](https://gitlab.cern.ch/lhcb-core/LHCbPR2HD). You can import them by using the followinf command:

`./site/manage.py lhcbpr_import /path/to/directory/with/zips`


# LHCbPR service

## Installation

1. `git clone ssh://git@gitlab.cern.ch:7999/lhcb-core/LHCbPR2BE`
1. `cd LHCbPR2BE`
1. `cp site/settings/private.default.py site/settings/private.py`
1. Configure  private.py (set db connection,...)
1. Set settings module in site/manage.py
1. Update settings module (set static url)
1. Setup and activate virtual environment (see below)
1. Run server: `python site/manage.py runserver`  (at local server)

### Virtual environment

Site is tested only with python2, so you need to setup only python virtual anvironment


```sh
virtualenv venv # at local server
virtualenv -p /afs/cern.ch/sw/lcg/external/Python/2.7.3/x86_64-slc5-gcc47-opt/bin/python venv # at lxplus
source venv/bin/activate
pip install -r requirements.txt
```

At lxplus don't forget to change python path at fcgi/lhcb-api.fcgi

At the developer's servers you can populate the database by executing the following commands:

1. `python site/manage.py migrate`
1. `python manage.py populate` (optional, fill empty database with test data)

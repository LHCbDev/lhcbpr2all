#!/afs/cern.ch/user/a/amazurov/www/lhcbpr-api/venv/bin/python
import sys, os

sys.path.insert(0, "/afs/cern.ch/sw/lcg/external/pytools/1.8_python2.7/x86_64-slc5-gcc47-opt/lib/python2.7/site-packages")
sys.path.insert(0, "/afs/cern.ch/user/a/amazurov/www/lhcbpr-api/site")

os.environ['DJANGO_SETTINGS_MODULE'] = "settings.lxplus"

from django.core.servers.fastcgi import runfastcgi
runfastcgi(method="threaded", daemonize="false")

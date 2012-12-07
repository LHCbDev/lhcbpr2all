#!/usr/bin/env python
import LbUtils.Log
LbUtils.Log._default_log_format = '%(asctime)s:' + LbUtils.Log._default_log_format

from LHCbNightlies2.StackCheckout import Script
import sys
sys.exit(Script().run())

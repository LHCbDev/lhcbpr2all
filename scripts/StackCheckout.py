#!/usr/bin/env python
import LbUtils.Log
import logging
LbUtils.Log._default_log_format = '%(asctime)s:' + logging.BASIC_FORMAT

from LHCbNightlies2.StackCheckout import Script
import sys
sys.exit(Script().run())

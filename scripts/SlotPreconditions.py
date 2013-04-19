#!/usr/bin/env python
import LbUtils.Log
LbUtils.Log._default_log_format = '%(asctime)s:' + LbUtils.Log._default_log_format

from LbNightlyTools.SlotPreconditions import Script
import sys
sys.exit(Script().run())

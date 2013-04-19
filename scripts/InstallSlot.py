#!/usr/bin/env python
import LbUtils.Log
LbUtils.Log._default_log_format = '%(asctime)s:' + LbUtils.Log._default_log_format

from LbNightlyTools.InstallSlot import Script
import sys
sys.exit(Script().run())

###############################################################################
# (c) Copyright 2014 CERN                                                     #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################

SRCS=$(wildcard *.rst)
TARGETS=$(SRCS:.rst=.html)

all: $(TARGETS)

# Generic rule for rst2html
%.html: %.rst
	rst2html $^ > $@

clean:
	$(RM) $(TARGETS)

.PHONY: all clean

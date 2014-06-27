###############################################################################
# (c) Copyright 2013 CERN                                                     #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
'''
Common utility functions used in scripts.
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

def addBasicOptions(parser):
    '''
    Add some basic (common) options to the option parser (optparse.OptionParser
    instance).
    '''
    parser.add_option('--build-id',
                      action='store',
                      help='string to add to the tarballs of the build to '
                           'distinguish them from others, the string can '
                           'be a format string using the parameter '
                           '"slot" [default: %default]')

    parser.add_option('--artifacts-dir',
                      action='store', metavar='DIR',
                      help='directory where to store the artifacts')

    parser.add_option('--projects',
                      action='store',
                      help='comma-separated list of projects to consider'
                           ' [default: all]')

    parser.set_defaults(build_id='{slot}',
                        artifacts_dir='artifacts')
    return parser


def addDashboardOptions(parser):
    '''
    Add dashboard-related options to the option parser (optparse.OptionParser
    instance).
    '''
    from optparse import OptionGroup
    group = OptionGroup(parser, "Dashboard Options")

    group.add_option('--submit',
                     action='store_true',
                     help='submit the results to Dashboard server')

    group.add_option('--no-submit',
                     action='store_false', dest='submit',
                     help='do not submit the results to Dashboard server '
                          '(default)')

    group.add_option('--flavour',
                     help='which build server to use (build flavour)')

    parser.add_option_group(group)
    parser.set_defaults(submit=False, flavour='nightly')
    return parser

def expandTokensInOptions(options, opt_names, **kwargs):
    '''
    Given an options instance, the list of option names, and the list of
    keywords to replace, replace the options with the correct expanded stings.

    >>> from optparse import Values
    >>> options = Values()
    >>> options.name = '{token}'
    >>> expandTokensInOptions(options, ['name'], token='Hello')
    >>> options.name
    'Hello'
    '''
    for opt_name in opt_names:
        val = getattr(options, opt_name)
        if val:
            setattr(options, opt_name, val.format(**kwargs))

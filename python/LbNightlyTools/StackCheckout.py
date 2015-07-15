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
Module containing the classes and functions used to checkout a set of projects,
fixing their dependencies to produce a consistent set.
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import logging
import os
import json
import codecs
from itertools import chain
from datetime import date
from os.path import join
from LbNightlyTools.Utils import chdir, pack
from LbNightlyTools.HTMLUtils import XTerm2HTML
from LbNightlyTools.Configuration import DataProject

__log__ = logging.getLogger(__name__)


from LbNightlyTools.ScriptsCommon import BaseScript
class Script(BaseScript):
    '''
    Script to checkout a consistent set of projects as described in a
    configuration file.

    The configuration file must be in JSON format containing an object with the
    attribute 'projects', a list of objects with defining the projects to be
    checked out.

    For example::
        {"projects": [{"name": "Gaudi",
                       "version": "v23r5",
                       "checkout": "specialCheckoutFunction"},
                      {"name": "LHCb",
                       "version": "v32r5",
                       "overrides": {"GaudiObjDesc": "HEAD",
                                     "GaudiPython": "v12r4",
                                     "Online/RootCnv": null}}]}
    '''

    def defineOpts(self):
        """ User options -- has to be overridden """
        from LbNightlyTools.ScriptsCommon import (addBasicOptions,
                                                  addDashboardOptions,
                                                  addDeploymentOptions)
        addBasicOptions(self.parser)
        addDashboardOptions(self.parser)
        addDeploymentOptions(self.parser)

        self.parser.add_option('--ignore-checkout-errors',
                               action='store_true',
                               dest='ignore_checkout_errors',
                               help='continue to checkout if there is a '
                                    'failure (default)')
        self.parser.add_option('--no-ignore-checkout-errors',
                               action='store_false',
                               dest='ignore_checkout_errors',
                               help='stop the checkout if there is a failure')
        self.parser.set_defaults(ignore_checkout_errors=True)

    def packname(self, element):
        '''
        Return the filename of the archive (package) of the given project.
        '''
        packname = [element.name.replace('/', '_'), element.version]
        if self.options.build_id:
            packname.append(self.options.build_id)
        packname.append('src')
        packname.append('tar.bz2')
        return '.'.join(packname)

    def main(self):
        """ Main logic of the script """
        self._setup(build_dir=join('tmp', 'checkout'),
                    json_type='slot-config')

        opts = self.options
        slot = self.slot

        # prepare special environment, if needed
        os.environ.update(slot.environment())

        # Prepare JSON doc for the database
        cfg = slot.toDict()
        cfg['date'] = os.environ.get('DATE', date.today().isoformat())
        cfg['started'] = self.starttime.isoformat()
        platforms = os.environ.get('platforms', '').strip().split()
        if platforms:
            cfg['platforms'] = platforms

        # publish the configuration before the checkout
        # (but we have to update it later)
        self.dump_json(cfg)

        with chdir(self.build_dir):
            slot.checkout(projects=opts.projects,
                          ignore_errors=opts.ignore_checkout_errors)

            if not cfg.get('no_patch'):
                with open(join(self.artifacts_dir,
                               '.'.join([opts.build_id or 'slot', 'patch'])),
                          'w') as patchfile:
                    slot.patch(patchfile)
            else:
                self.log.info('not patching the sources')

        # write the checkout log of projects to dedicated files
        for project in slot.projects:
            if hasattr(project, 'checkout_log'):
                __log__.debug('writing checkout log for %s', project)
                co_logfile = join(self.artifacts_dir,
                                  '.'.join((project.name, 'checkout.log')))
                with open(co_logfile, 'w') as co_log:
                    co_log.write(project.checkout_log)
                with open(co_logfile + '.html', 'w') as co_log:
                    conv = XTerm2HTML(show_line_no=True)
                    co_log.write(conv.head(title=os.path.basename(co_logfile)))
                    co_log.write(conv.process(project.checkout_log))
                    co_log.write(conv.tail())

        def containers():
            '''
            Generator for the container projects in the slot.
            '''
            for cont in slot.projects:
                if isinstance(cont, DataProject):
                    yield cont

        packages = list(chain.from_iterable(cont.packages
                                            for cont in containers()))

        for element in chain(slot.projects, packages):
            # ignore missing directories
            # (the project may not have been checked out)
            if not os.path.exists(join(self.build_dir, element.baseDir)):
                self.log.warning('no sources for %s, skip packing', element)
                continue
            if isinstance(element, DataProject):
                continue # ignore DataProjects, because we pack packages

            self.log.info('packing %s %s...', element.name, element.version)

            pack([element.baseDir], join(self.artifacts_dir,
                                         self.packname(element)),
                 cwd=self.build_dir, checksum='md5')
        for container in containers():
            container = container.name
            self.log.info('packing %s (links)...', container)
            contname = [container]
            if self.options.build_id:
                contname.append(self.options.build_id)
            contname.append('src.tar.bz2')
            pack([container], join(self.artifacts_dir, '.'.join(contname)),
                 cwd=self.build_dir, checksum='md5', dereference=False,
                 exclude=[p.baseDir for p in packages])

        from datetime import datetime
        donetime = datetime.now()
        cfg['completed'] = donetime.isoformat()

        # Save a copy as metadata for tools like lbn-install
        with codecs.open(join(self.artifacts_dir, 'slot-config.json'),
                         'w', 'utf-8') as config_dump:
            data = dict(self.json_tmpl)
            data.update(cfg)
            json.dump(data, config_dump, indent=2)

        # publish the updated configuration JSON
        self.dump_json(cfg)

        self.deploy_artifacts()

        self.log.info('sources ready for build (time taken: %s).',
                      donetime - self.starttime)

        return 0

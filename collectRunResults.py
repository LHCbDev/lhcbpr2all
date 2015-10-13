#!/usr/bin/env python

import os
import sys
import subprocess
import inspect
import json
import logging
import uuid
import zipfile
import ntpath
import sendToDB
import argparse
from datetime import (timedelta, datetime, tzinfo)


class FixedOffset(tzinfo):

    """Fixed offset in minutes: `time = utc_time + utc_offset`."""

    def __init__(self, offset):
        self.__offset = timedelta(minutes=offset)
        hours, minutes = divmod(offset, 60)
        # NOTE: the last part is to remind about deprecated POSIX GMT+h timezones
        #  that have the opposite sign in the name;
        #  the corresponding numeric value is not used e.g., no minutes
        self.__name = '<%+03d%02d>%+d' % (hours, minutes, -hours)

    def utcoffset(self, dt=None):
        return self.__offset

    def tzname(self, dt=None):
        return self.__name

    def dst(self, dt=None):
        return timedelta(0)

    def __repr__(self):
        return 'FixedOffset(%d)' % (self.utcoffset().total_seconds() / 60)


def mkdatetime(datestr):
    naive_date_str, _, offset_str = datestr.rpartition(' ')
    naive_dt = datetime.strptime(naive_date_str, '%Y-%m-%d %H:%M:%S')
    offset = int(offset_str[-4:-2]) * 60 + int(offset_str[-2:])
    if offset_str[0] == "-":
        offset = -offset
    dt = naive_dt.replace(tzinfo=FixedOffset(offset))
    return dt


def JobDictionary(hostname, starttime, endtime, cmtconfig, appname, appversion,
                  appversiondatetime, optname, optcontent, optstandalone, setupname, setupcontent):
    """
    This method creates a dictionary with information about the job (like time_start/end etc)
    which will be added to json_results along with the execution results
    """

    hostDict = {'hostname': hostname, 'cpu_info': '', 'memoryinfo': ''}
    cmtconfigDict = {'platform': cmtconfig}
    DataDict = {
        'HOST': hostDict,
        'CMTCONFIG': cmtconfigDict,
        'time_start': starttime,
        'time_end': endtime,
        'status': '',
        'app_name': appname,
        'app_version': appversion,
        'app_version_datetime': appversiondatetime,
        'opt_name': optname,
        'opt_content': optcontent,
        'opt_standalone': optstandalone,
        'setup_name': setupname,
        'setup_content': setupcontent
    }

    return DataDict


def main():
    """The collectRunResults scripts creates the json_results file which contains information about the
    the runned job(platform,host,status etc) along with the execution results, the output(logs, root files,xml files)
     of a job are collected by handlers. Each handler knows which file must parse, so this script imports dynamically
     each handler(from the input handler list, --list-handlers option) and calls the collectResults function, of each handler, and
     passes to the function the directory(the default is the . <-- current directory) to the results(output of the runned job)"""
    # this is used for checking
    outputfile = 'json_results'
    needed_options = 12

    description = """The program needs all the input arguments(options in order to run properly)"""
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-r', '--results', default=".",
                        help='Directory which contains results, default is the current directory')

    parser.add_argument('--app-name',
                        help='Application name (Brunel, Gauss, Moore, ...)',
                        required=True)
    parser.add_argument('--app-version',
                        help='Application release/build version (v42r0, lhcb-gaudi-header-111,...)',
                        required=True)
    parser.add_argument('--app-version-datetime',
                        help='Application release/build creation time (2015-10-13 11:00:00 +0200)',
                        type=mkdatetime,
                        required=True)
    parser.add_argument('--opt-name',
                        help='Option name (PRTEST-COLLISION12-1000, PRTEST-Callgrind-300evts,...)',
                        required=True)
    parser.add_argument('--opt-content',
                        help='Option content ("${PRCONFIGOPTS}/Moore/PRTEST-Callgrind-300evts.py",...)',
                        required=True)
    parser.add_argument('--opt-standalone', action='store_true',
                        help='Set flag if option is shell script and not job option',
                        default=False)
    parser.add_argument('--setup-name',
                        help='Setup name (UsePRConfig, UserAreaPRConfig, ...)',
                        required=True)
    parser.add_argument('--setup-content',
                        help='Setup content ("--no-user-area --use PRConfig", "--use PRConfig", ...)',
                        required=True)

    parser.add_argument('-s', '--start-time',
                        dest='startTime', help='The start time of the job.',
                        required=True)
    parser.add_argument('-e', '--end-time',
                        dest="endTime", help="The end time of the job.",
                        required=True)
    parser.add_argument("-p", "--hostname",
                        dest="hostname", help="The name of the host who runned the job.",
                        required=True)
    parser.add_argument("-c", "--platform",
                        dest="platform", help="The platform(cmtconfig) of the job.",
                        required=True)
    parser.add_argument("-l", "--list-handlers",
                        dest="handlers", help="The list of handlers(comma separated.")
    parser.add_argument("-q", "--quiet", action="store_true",
                        dest="ssss", default=False,
                        help="Just be quiet (do not print info from logger)")
    parser.add_argument("-a", "--auto-send-results", action="store_true",
                        dest="send", default=False,
                        help="Automatically send the zip results to the database.")

    options = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)

    if not options.ssss:
        logging.root.setLevel(logging.INFO)

    logger = logging.getLogger('collectRunResults.py')

    dataDict = JobDictionary(
        options.hostname,
        options.startTime,
        options.endTime,
        options.platform,
        options.app_name,
        options.app_version,
        str(options.app_version_datetime),
        options.opt_name,
        options.opt_content,
        options.opt_standalone,
        options.setup_name,
        options.setup_content
    )

    jobAttributes = []
    handlers_result = []

    # for each handler in the handlers list
    for handler in options.handlers.split(','):
        module = ''.join(['handlers', '.', handler])
        # import the current handler
        try:
            mod = __import__(module, fromlist=[module])
        except ImportError, e:
            logger.exception(
                'Please check your script or your LHCbPRHandlers directory')
        else:
            # create an instance of a the current handler
            klass = getattr(mod, handler)
            currentHandler = klass()

            try:
                # collect results from the given directory(--results-directory,
                # -r)
                currentHandler.collectResults(options.results)
            except Exception, e:
                # if any error occurs and the handler fails, inform the user using the logger
                # and save that the current handler failed
                logger.exception('Handler exception:')
                handlers_result.append(
                    {'handler': handler, 'successful': False})
            else:
                # in case everything is fine , save that the current handler
                # worked successfully
                jobAttributes.extend(currentHandler.getResults())
                handlers_result.append(
                    {'handler': handler, 'successful': True})

    if not jobAttributes:
        logger.warning(
            'All handlers failed, no results were collected. Aborting...')
        exit(1)

    unique_results_id = str(uuid.uuid1())
    zipper = zipfile.ZipFile(unique_results_id + '.zip', mode='w')

    for i in range(len(jobAttributes)):
        if jobAttributes[i]['type'] == 'File':
            head, tail = ntpath.split(jobAttributes[i]['filename'])

            try:
                # write to the zip file the root file with a unique name
                zipper.write(jobAttributes[i]['filename'], tail)
            except Exception:
                pass

            # update in the json_results the uuid new filename
            jobAttributes[i]['filename'] = tail

    dataDict['results_id'] = unique_results_id

    # add the collected results and the handlers' information to the final
    # data dictionary
    dataDict['JobAttributes'] = jobAttributes
    dataDict['handlers_info'] = handlers_result

    f = open(outputfile, 'w')
    f.write(json.dumps(dataDict))
    f.close()

    # add to the zip results file the json_result file
    zipper.write(outputfile)

    # close the zipfile object
    zipper.close()

    logger.info(unique_results_id + '.zip')

    if options.send:
        logger.info(
            'Automatically sending the zip results file to the database...')
        sendToDB.run(unique_results_id + '.zip', False)

if __name__ == '__main__':
    main()

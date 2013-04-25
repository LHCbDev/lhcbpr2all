#!/usr/bin/env python

import sys, json, logging, zipfile, shutil, os
from optparse import OptionParser
from optparse import Option, OptionValueError

logger = logging.getLogger('sendToDB.py')

diracStorageElementName = 'StatSE'

diracStorageElementFolder = 'uploaded'

def sendViaDiracStorageElement(zipFile):
    head, tailzipFile = os.path.split(zipFile)
    
    from DIRAC.Core.Base.Script import parseCommandLine, initialize
    initialize(ignoreErrors = True, enableCommandLine = False)
    
    from DIRAC.Resources.Storage.StorageElement import StorageElement
    statSE = StorageElement(diracStorageElementName)
    
    log = statSE.putFile({ os.path.join(diracStorageElementFolder, tailzipFile) : zipFile})
    logger.info('{0}'.format(log))
    
def run(zipFile, ssss):
    if not ssss:
        logging.root.setLevel(logging.INFO)
    
    if not zipfile.is_zipfile(zipFile):
        logger.error('Given object is not a valid zip file, please give a valid one, aborting...')
        return
    
    #checking if the zip contains what it should contains
    try:
        unzipper = zipfile.ZipFile(zipFile)
        dataDict = json.loads(unzipper.read('json_results'))
        
        for atr in dataDict['JobAttributes']:
            if atr['type'] == 'File':
                unzipper.read(atr['filename'])
            
    except Exception, e:
        logger.error(e)
        logger.error('Aborting...')
        return
    
    logger.info('Given zip file is valid, sending to database...')

    sendViaDiracStorageElement(zipFile)
    return

def main():
    #this is used for checking
    needed_options = 3
    
    description = """The program needs all the input arguments(options in order to run properly)"""
    parser = OptionParser(usage='usage: %prog [options]',
                          description=description)
    parser.add_option('-s', '--send-results', 
                      action='store', type='string',
                      dest='zipFile', help='Zip file with results to be pushed to database')
    parser.add_option("-q", "--quiet", action="store_true",
                      dest="ssss", default=False,
                      help="Just be quiet (do not print info from logger), optional")

    if len(sys.argv) < needed_options:
        parser.parse_args(['--help'])
        return
        

    options, args = parser.parse_args()
    
    logging.basicConfig(level=logging.WARNING)
    
    run(options.zipFile, options.ssss)
    
if __name__ == '__main__':
    main()
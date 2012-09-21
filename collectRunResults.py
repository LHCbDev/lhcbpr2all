#!/usr/bin/env python

import os, sys, subprocess, inspect, json, logging, uuid, zipfile, ntpath, sendToDB
from optparse import OptionParser
from optparse import Option, OptionValueError

def JobDictionary(hostname,starttime,endtime,cmtconfig,jodDesId):
    """
    This method creates a dictionary with information about the job (like time_start/end etc)
    which will be added to json_results along with the execution results
    """
    
    hostDict = { 'hostname': hostname, 'cpu_info': '', 'memoryinfo': ''}
    cmtconfigDict = {'platform': cmtconfig}
    DataDict = {
                'HOST': hostDict,
                'CMTCONFIG': cmtconfigDict,
                'time_start': starttime,
                'time_end': endtime,
                'status': '',
                'id_jobDescription': jodDesId
                }
    
    return DataDict

def main():
    """The collectRunResults scripts creates the json_results file which contains information about the 
    the runned job(platform,host,status etc) along with the execution results, the output(logs, roots file,xmls)
     of a job are collected by handlers. Each handler knows which file must parse, so this script imports dynamically 
     each handler(from the input handler list, --list-handlers option) and calls the collectResults ,of each handler, and 
     passes to the method the directory(the default is the . <-- current directory) to the results(output of the runned job)"""
    #this is used for checking
    outputfile = 'json_results'
    needed_options = 12
    
    description = """The program needs all the input arguments(options in order to run properly)"""
    parser = OptionParser(usage='usage: %prog [options]',
                          description=description)
    parser.add_option('-r', '--results-directory', 
                      action='store', type='string',
                      dest='results', default=".", 
                      help='Directory which contains results')
    parser.add_option( '-s' , '--start-time' , action='store', type='string' , 
                    dest='startTime' , help='The start time of the job.') 
    parser.add_option( '-e' , '--end-time' , action='store', type='string' , 
                    dest="endTime" , help="The end time of the job.") 
    parser.add_option( "-p" , "--hostname" , action="store", type="string" , 
                    dest="hostname" , help="The name of the host who runned the job.")
    parser.add_option( "-c" , "--cmtconfig" , action="store", type="string" , 
                    dest="cmtconfig" , help="The cmtconfig of the job.")  
    parser.add_option( "-j" , "--jobDescription-id" , action="store", type="string" , 
                    dest="jobDescription_id" , help="The job description unique id.")
    parser.add_option("-l" , "--list-handlers" , action="store", type="string" ,
                    dest="handlers" , help="The list of handlers(comma separated.")
    parser.add_option("-q", "--quiet", action="store_true",
                      dest="ssss", default=False,
                      help="Just be quiet (do not print info from logger)")
    parser.add_option("-a", "--auto-send-results", action="store_true",
                      dest="send", default=False,
                      help="Automatically send the zip results to the database.")
    
    #check if all  the options were given
    if len(sys.argv) < needed_options:
        parser.parse_args(['--help'])
        return

    options, args = parser.parse_args()
    
    logging.basicConfig(level=logging.WARNING)

    if not options.ssss:
        logging.root.setLevel(logging.INFO)
        
    logger = logging.getLogger('collectRunResults.py')
    
    dataDict = JobDictionary(options.hostname,options.startTime,options.endTime,
                       options.cmtconfig,options.jobDescription_id)
    
    jobAttributes = []
    handlers_result = []

    #for each handler in the handlers list
    for handler in options.handlers.split(','):
        module = ''.join(['handlers','.',handler])
        #import the current handler
        try:
            mod = __import__(module, fromlist=[module])
        except ImportError, e:
            logger.error(str(e)+', please check your script or your LHCbPRHandlers directory')
        else:
            #create an instance of a the current handler
            klass = getattr(mod, handler)
            currentHandler = klass()
            
            try:
                #collect results from the given directory(--results-directory, -r)
                currentHandler.collectResults(options.results)
            except Exception,e:
                #if any error occurs and the handler fails, inform the user using the logger
                #and save that the current handler failed
                logger.error('A handler failed:')
                logger.error(e)
                handlers_result.append({ 'handler' : handler, 'successful' : False })
            else:
                #in case everything is fine , save that the current handler worked successfully
                jobAttributes.extend(currentHandler.getResults())
                handlers_result.append({ 'handler' : handler, 'successful' : True })
    
    if not jobAttributes:
        logger.warning('All handlers failed, no results were collected.')
    
    unique_results_id = str(uuid.uuid1())
    zipper = zipfile.ZipFile(unique_results_id+'.zip', mode='w')
    
    for i in range(len(jobAttributes)):
        if jobAttributes[i]['type'] == 'File':
            head, tail = ntpath.split(jobAttributes[i]['filename'])
            
            try:
                #write to the zip file the root file with a unique name
                zipper.write(jobAttributes[i]['filename'], tail)
            except Exception:
                pass
            
            #update in the json_results the uuid new filename
            jobAttributes[i]['filename'] = tail

    dataDict['results_id'] = unique_results_id
    
    #add the collected results and the handlers' information to the final
    #data dictionary       
    dataDict['JobAttributes'] = jobAttributes
    dataDict['handlers_info'] = handlers_result
    
    f = open(outputfile,'w')
    f.write(json.dumps(dataDict))
    f.close()
    
    #add to the zip results file the json_result file
    zipper.write(outputfile)
    
    #close the zipfile object
    zipper.close()
    
    logger.info('Zip file containing the results produced.')
    
    if options.send:
        logger.info('Automatically sending the zip results file to the database...')
        sendToDB.run(unique_results_id+'.zip' ,False)

if __name__ == '__main__':
    main()

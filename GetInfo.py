# Get information from Jira installed plugins
# Requires .netrc file for authentication
#
# 22.1.2019 mika.nokka1@gmail.com  Initial version

import datetime 
import time
import argparse
import sys
import netrc
import requests, os
from requests.auth import HTTPBasicAuth
# We don't want InsecureRequest warnings:
import requests
requests.packages.urllib3.disable_warnings()
import itertools, re, sys
from jira import JIRA
import json
import pprint
from datetime import date
import logging


__version__ = "0.9"
thisFile = __file__

    
def main(argv):

    JIRASERVICE=""
    JIRAPROJECT=""
    JIRASUMMARY=""
    JIRADESCRIPTION=""
    
    logger = logging.getLogger(thisFile)
    #logger.setLevel(logging.DEBUG) #info
    
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    #ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)
    
    parser = argparse.ArgumentParser(usage="""
    {1}    Version:{0}     -  mika.nokka1@gmail.com
    
    .netrc file used for authentication. Remember chmod 600 protection
    Gets info for installed plugins in Jira
    
    
    EXAMPLE: python {1}  -j http://jira.test.com 
    
    debugmode: -d ON
    developer debug mode: -l ON
    
    Set days limit before alarming -t 20
    (marks all license expr days in next 20 days as failed)
    Default value is 30days
    
    Return values: 1=black, 2=red,3=yellow, 0=green, 5=tool issues


    """.format(__version__,sys.argv[0]))

    #parser.add_argument('-p','--project', help='<JIRA project key>')
    parser.add_argument('-j','--jira', help='<Target JIRA address>')
    parser.add_argument('-d','--debug', help='<Debug Mode>')
    parser.add_argument('-l','--development', help='<Development debug mode>')
    parser.add_argument('-v','--version', help='<Version>', action='store_true')
    parser.add_argument('-t','--threshold', help='<Expr days threshold limit>')
  
    
    args = parser.parse_args()
    
    JIRASERVICE = args.jira or ''
    DEBUG=args.debug or False 
    THRDAYS=args.threshold or 30
    DEVDEBUG=args.development or False 
  
        
    if (DEBUG or DEVDEBUG):
        logger.setLevel(logging.DEBUG) #info
        ch.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO) #info
        ch.setLevel(logging.INFO) 
    
    if args.version:
        logger.info( 'Tool version: %s'  % __version__)
        sys.exit(5)    
         

    
  
    
  
    # quick old-school way to check needed parameters
    if (JIRASERVICE=='' ):
        parser.print_help()
        logger.error("Check used parameters")
        sys.exit(5)

    logger.info("Using failure threshold:{0} days".format(THRDAYS))
    
    user, PASSWORD = Authenticate(JIRASERVICE,DEBUG,logger)
    jira= DoJIRAStuff(user,PASSWORD,JIRASERVICE,logger)
    #CreateIssue(jira,JIRAPROJECT,JIRASUMMARY,JIRADESCRIPTION)
    GetStepInfo(jira,JIRASERVICE,user,PASSWORD,DEBUG,logger,THRDAYS,DEVDEBUG)    
####################################################################################################    
def Authenticate(JIRASERVICE,DEBUG,logger):
    host=JIRASERVICE
    credentials = netrc.netrc()
    auth = credentials.authenticators(host)
    if auth:
        user = auth[0]
        PASSWORD = auth[2]
        logger.info("Got .netrc OK")
    else:
        logger.error(".netrc file problem (Server:{0}) . EXITING!".format(host))
        sys.exit(1)

    f = requests.get(host,auth=(user, PASSWORD))
         
    # CHECK WRONG AUTHENTICATION    
    header=str(f.headers)
    HeaderCheck = re.search( r"(.*?)(AUTHENTICATION_DENIED|AUTHENTICATION_FAILED)", header)
    if HeaderCheck:
        CurrentGroups=HeaderCheck.groups()    
        logger.info("Group 1: %s" % CurrentGroups[0]) 
        logger.info("Group 2: %s" % CurrentGroups[1]) 
        logger.info("Header: %s" % header)         
        logger.error("Authentication FAILED - HEADER: {0}".format(header)) 
        logger.error("Apparantly user authentication gone wrong. EXITING!")
        sys.exit(1)
    else:
        logger.info("Authentication OK")
        if (DEBUG):
            logger.info("HEADER: {0}".format(header))    
    print "---------------------------------------------------------"
    return user,PASSWORD

###################################################################################    
def DoJIRAStuff(user,PASSWORD,JIRASERVICE,logger):
 jira_server=JIRASERVICE
 try:
     print("Connecting to JIRA: %s" % jira_server)
     jira_options = {'server': jira_server}
     jira = JIRA(options=jira_options,basic_auth=(user,PASSWORD))
     logger.info("JIRA Authorization OK")
 except Exception,e:
    logger.error("Failed to connect to JIRA: %s" % e)
    sys.exit(1)
 return jira   
    
####################################################################################
def CreateIssue(jira,JIRAPROJECT,JIRASUMMARY,JIRADESCRIPTION,logger):
    jiraobj=jira
    project=JIRAPROJECT
    logger.info( "Creating issue for JIRA project: {0}".format(project))
    issue_dict = {
    'project': {'key': JIRAPROJECT},
    'summary': JIRASUMMARY,
    'description': JIRADESCRIPTION,
    'issuetype': {'name': 'Task'},
    }

    try:
        new_issue = jiraobj.create_issue(fields=issue_dict)
    except Exception,e:
        logger.error(("Failed to create JIRA project, error: %s" % e))
        sys.exit(1)

####################################################################################
def GetStepInfo(jira,JIRASERVICE,user,PASSWORD,DEBUG,logger,THRDAYS,DEVDEBUG):
    
    logger.info( "Debug status:{0}".format(DEBUG))
    
    headers = {'Content-Type': 'application/json'}
    # URL="{0}/rest/plugins/applications/1.0/installed/jira-software/license".format(JIRASERVICE)  # server license info
    URL="{0}/rest/plugins/1.0/".format(JIRASERVICE) # get plugins
    #URL="{0}/rest/api/2/".format(JIRASERVICE)
    r=requests.get(URL, headers,  auth=(user, PASSWORD))
 
    if (DEBUG):
        logger.info("Headers:{0}".format(r.headers))
        logger.info("Message:{0}".format((r.text).encode('utf-8')))
    
    if (r.status_code == requests.codes.ok):
        logger.info("ok reply")
        data = json.loads(r.text)
        if (DEVDEBUG):
            logger.debug( "PLUGIN RAW DATA:{0}".format(data))
            logger.debug("*********************")
            logger.debug("SORTED DATA:")
            logger.debug((json.dumps(data, indent=4, sort_keys=True)))

        sorted_data = sorted(data["plugins"], key=lambda k: k['name'])
        if (DEVDEBUG):
            logger.debug("PLUGIN NAME SORTED_DATA:")
            logger.debug((json.dumps(sorted_data, indent=4, sort_keys=True)))
            #pprint.pprint(data) # jsut tested pprint library
        
        EXPIRED={} #record issutypes
        OKEXPIRATION={}
        ALARMNEXPIRATION={}
        for item in sorted_data:
           

            if (item["enabled"] and item["userInstalled"] and item["usesLicensing"]): 
                pluginkey = item["key"]
                URL="{0}/rest/plugins/1.0/{1}-key/license".format(JIRASERVICE,pluginkey) # license info for one plugin (key)
                r=requests.get(URL, headers,  auth=(user, PASSWORD))
                if (DEBUG):
                    logger.debug("Headers:{0}".format(r.headers))
                    logger.debug("Message:{0}".format((r.text).encode('utf-8')))
                
                # TODO: SHOULD CHECK FAIL
                licenseinfo = json.loads(r.text)
                if (DEVDEBUG):
                    logger.debug((json.dumps(licenseinfo, indent=4, sort_keys=True)))
                
                logger.info( "PLUGIN:{0:35s} VERSION:{1:10s} KEY:{2:40s}".format(item["name"],item["version"],pluginkey))
                pluginname=item["name"]
                
                if "maintenanceExpiryDate" in licenseinfo:
                    #ExpDate=licenseinfo["maintenanceExpiryDate"] # the mystical number string
                    ExpDate=licenseinfo["maintenanceExpiryDateString"]
                    logger.info( "EXPIRATION DATE:{0}".format(ExpDate))
                    Converdate = datetime.datetime.strptime(ExpDate, '%d/%b/%y')
                    #Twoweeks = datetime.datetime.now() - datetime.timedelta(weeks=2)
                    if (datetime.datetime.now() < Converdate):
                        Exprdelta=(Converdate - datetime.datetime.now()).days
                        logger.info("--> LICENCE IS VALID ---> TO BE EXPIRED IN:{0} DAYS".format(Exprdelta))
                        #logger.info("--> THRDAYS:{0} DAYS".format(THRDAYS))
                        #calc=int(Exprdelta)-int(THRDAYS)
                        #logger.info("--> calc:{0} DAYS".format(calc))
                        if (int(Exprdelta) < int(THRDAYS) ): #in some date format -> convert int
                            logger.debug( "TRESHOLD EXP DATE")
                            if (pluginname in ALARMNEXPIRATION):
                                value=ALARMNEXPIRATION.get(pluginname,"10000") # 1000 is default value
                                value=value+1 
                                ALARMNEXPIRATION[pluginname]=value
                                logger.debug( "Addded FAILED threshold expr plugin enrty: {0}".format(pluginname))
                            else:
                                ALARMNEXPIRATION[pluginname]=1 # first issue attachment, create entry for dictionary
                                logger.debug("Created FAILED threshold expr plugin entry: {0}".format(pluginname))
                        else:
                            logger.debug( "OK VALIDITY")
                            if (pluginname in OKEXPIRATION):
                                value=OKEXPIRATION.get(pluginname,"10000") # 1000 is default value
                                value=value+1 
                                OKEXPIRATION[pluginname]=value
                                logger.debug("Addded OK threshold expr plugin enrty: {0}".format(pluginname))
                            else:
                                OKEXPIRATION[pluginname]=1 # first issue attachment, create entry for dictionary
                                logger.debug("Created OK threshold expr plugin entry: {0}".format(pluginname))
                            
                        
                    if(datetime.datetime.now() > Converdate):
                        logger.error( "--> ERROR: LICENCE EXPIRED. ARGH")
                        #use dictionary to keep record of failed licenes
                        if (pluginname in EXPIRED):
                            value=EXPIRED.get(pluginname,"10000") # 1000 is default value
                            value=value+1 
                            EXPIRED[pluginname]=value
                            logger.debug( "Addded failed plugin: {0}".format(pluginname))
                        else:
                            EXPIRED[pluginname]=1 # first issue attachment, create entry for dictionary
                            logger.debug ( "Created failed plugin entry: {0}".format(pluginname))
                      
                        
                else:
                    ExpDate="NONENONE" # dead code
                logger.info( "----------------------------------------------------------------------------------------------------")
            
        #TODO return either green,yellow or red 
            #print "-------------------------------------------------------------------------"
    
    
   
    
    else:
        logger.error("Failed to get license information")
        logger.info("Headers:{0}".format(r.headers))
        logger.info("Message:{0}".format((r.text).encode('utf-8')))
        sys.exit(1)
    
    OKEXPR=0
    ALARMEXPR=0
    FAILEDEXPR=0
    
    #value is 1 for each plugin, dictionary used for convience
    logger.debug( "***********************************************************")
    for key,value in OKEXPIRATION.items():
        logger.debug( "PLUGIN:{0}  => OK Expiration date in future".format(key) )
        OKEXPR=OKEXPR+1
        
    logger.debug( "***********************************************************")
    for key,value in ALARMNEXPIRATION.items():
        logger.debug("PLUGIN:{0}  => ALARM Expiration date is coming soon".format(key) )
        ALARMEXPR=ALARMEXPR+1
        
    logger.debug( "***********************************************************")
    for key,value in EXPIRED.items():
        logger.debug( "PLUGIN:{0}  => FAIL License expired".format(key))
        FAILEDEXPR=FAILEDEXPR+1
        
    
    #print the traffic lights summary 
    logger.info("")
    logger.info( "***** STATUS SUMMARY FOR:{0} **************".format(JIRASERVICE))
    logger.info( "Plugins with OK Expiration date in future:{0}".format(OKEXPR) )
    logger.info( "Plugins with ALARM Expiration:{0} ".format(ALARMEXPR) )
    logger.info( "Plugins with FAILED Expiration:{0} ".format(FAILEDEXPR) )
    if (FAILEDEXPR >0):
        logger.info("==> STATUS: RED")
    elif (ALARMEXPR >0 and FAILEDEXPR==0):   
        logger.info("==> STATUS: YELLOW")
    elif (ALARMEXPR==0 and FAILEDEXPR==0 and OKEXPR >0 ):   
        logger.info("==> STATUS: GREEN")   
    else:
        logger.info("==> STATUS: SYNTAX ERROR? NO IDEA WHAATSUP!!")
        
if __name__ == "__main__":
        main(sys.argv[1:])
        
        

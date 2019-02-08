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
    logger.setLevel(logging.INFO)
    
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

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
    
    Return values: 1=black, 2=red,3=yellow, 0=green, 5=tool issues


    """.format(__version__,sys.argv[0]))

    #parser.add_argument('-p','--project', help='<JIRA project key>')
    parser.add_argument('-j','--jira', help='<Target JIRA address>')
    parser.add_argument('-d','--debug', help='<Debug Mode>')
    parser.add_argument('-v','--version', help='<Version>', action='store_true')
  
    
    args = parser.parse_args()
        
    
    if args.version:
        logger.info( 'Tool version: %s'  % __version__)
        sys.exit(5)    
         

    JIRASERVICE = args.jira or ''
    DEBUG=args.debug or False 
  
  
    # quick old-school way to check needed parameters
    if (JIRASERVICE=='' ):
        parser.print_help()
        logger.error("Check used parameters")
        sys.exit(5)

    user, PASSWORD = Authenticate(JIRASERVICE,DEBUG,logger)
    jira= DoJIRAStuff(user,PASSWORD,JIRASERVICE,logger)
    #CreateIssue(jira,JIRAPROJECT,JIRASUMMARY,JIRADESCRIPTION)
    GetStepInfo(jira,JIRASERVICE,user,PASSWORD,DEBUG,logger)    
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
    print "Creating issue for JIRA project: {0}".format(project)
    issue_dict = {
    'project': {'key': JIRAPROJECT},
    'summary': JIRASUMMARY,
    'description': JIRADESCRIPTION,
    'issuetype': {'name': 'Task'},
    }

    try:
        new_issue = jiraobj.create_issue(fields=issue_dict)
    except Exception,e:
        print("Failed to create JIRA project, error: %s" % e)
        sys.exit(1)

####################################################################################
def GetStepInfo(jira,JIRASERVICE,user,PASSWORD,DEBUG,logger):
    
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
        if (DEBUG):
            logger.info( "PLUGIN RAW DATA:{0}".format(data))
            logger.info("*********************")
            logger.info("SORTED DATA:")
            logger.info((json.dumps(data, indent=4, sort_keys=True)))

        sorted_data = sorted(data["plugins"], key=lambda k: k['name'])
        if (DEBUG):
            logger.info("PLUGIN NAME SORTED_DATA:")
            logger.info((json.dumps(sorted_data, indent=4, sort_keys=True)))
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
                    logger.info("Headers:{0}".format(r.headers))
                    logger.info("Message:{0}".format((r.text).encode('utf-8')))
                
                # TODO: SHOULD CHECK FAIL
                licenseinfo = json.loads(r.text)
                if (DEBUG):
                    logger.info((json.dumps(licenseinfo, indent=4, sort_keys=True)))
                
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
                        if (Exprdelta < 10  ):
                            print "TRESHOLD EXP DATE"
                            if (pluginname in ALARMNEXPIRATION):
                                value=ALARMNEXPIRATION.get(pluginname,"10000") # 1000 is default value
                                value=value+1 
                                ALARMNEXPIRATION[pluginname]=value
                                print "Addded FAILED threshold expr plugin enrty: {0}".format(pluginname)
                            else:
                                ALARMNEXPIRATION[pluginname]=1 # first issue attachment, create entry for dictionary
                                print "Created FAILED threshold expr plugin entry: {0}".format(pluginname)
                        else:
                            print "OK VALIDITY" 
                            if (pluginname in OKEXPIRATION):
                                value=OKEXPIRATION.get(pluginname,"10000") # 1000 is default value
                                value=value+1 
                                OKEXPIRATION[pluginname]=value
                                print "Addded OK threshold expr plugin enrty: {0}".format(pluginname)
                            else:
                                OKEXPIRATION[pluginname]=1 # first issue attachment, create entry for dictionary
                                print "Created OK threshold expr plugin entry: {0}".format(pluginname)
                            
                        
                    if(datetime.datetime.now() > Converdate):
                        logger.error( "--> ERROR: LICENCE EXPIRED. ARGH")
                        #use dictionary to keep record of failed licenes
                        if (pluginname in EXPIRED):
                            value=EXPIRED.get(pluginname,"10000") # 1000 is default value
                            value=value+1 
                            EXPIRED[pluginname]=value
                            print "Addded failed plugin: {0}".format(pluginname)
                        else:
                            EXPIRED[pluginname]=1 # first issue attachment, create entry for dictionary
                            print "Created failed plugin entry: {0}".format(pluginname)
                      
                        
                else:
                    ExpDate="NONENONE" # dead code
                print "------------------------------------------------------------------------------------------"
            
        #TODO return either green,yellow or red 
            #print "-------------------------------------------------------------------------"
    
    
   
    
    else:
        logger.error("Failed to get license information")
        logger.info("Headers:{0}".format(r.headers))
        logger.info("Message:{0}".format((r.text).encode('utf-8')))
        sys.exit(1)
    
    print "***********************************************************"
    for key,value in OKEXPIRATION.items():
        print "PLUGIN:{0}  => OK Expiration date in future {1}".format(key,value) 
    print "***********************************************************"
    for key,value in ALARMNEXPIRATION.items():
        print "PLUGIN:{0}  => ALARM Expiration date too near{1}".format(key,value) 
    print "***********************************************************"
    for key,value in EXPIRED.items():
        print "PLUGIN:{0}  => FAIL expired {1}".format(key,value)
    
        
if __name__ == "__main__":
        main(sys.argv[1:])
        
        

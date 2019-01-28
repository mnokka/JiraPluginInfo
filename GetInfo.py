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


__version__ = "0.9"
thisFile = __file__

    
def main(argv):

    JIRASERVICE=""
    JIRAPROJECT=""
    JIRASUMMARY=""
    JIRADESCRIPTION=""
    
    
    parser = argparse.ArgumentParser(usage="""
    {1}    Version:{0}     -  mika.nokka1@gmail.com
    
    .netrc file used for authentication. Remember chmod 600 protection
    Gets info for installed plugins in Jira
    
    
    EXAMPLE: python {1}  -j http://jira.test.com 
    
    debugmode: -d ON


    """.format(__version__,sys.argv[0]))

    #parser.add_argument('-p','--project', help='<JIRA project key>')
    parser.add_argument('-j','--jira', help='<Target JIRA address>')
    parser.add_argument('-d','--debug', help='<Debug Mode>')
    parser.add_argument('-v','--version', help='<Version>', action='store_true')
  
    
    args = parser.parse_args()
        
    
    if args.version:
        print 'Tool version: %s'  % __version__
        sys.exit(2)    
         

    JIRASERVICE = args.jira or ''
    DEBUG=args.debug or False 
  
  
    # quick old-school way to check needed parameters
    if (JIRASERVICE=='' ):
        parser.print_help()
        sys.exit(2)

    user, PASSWORD = Authenticate(JIRASERVICE,DEBUG)
    jira= DoJIRAStuff(user,PASSWORD,JIRASERVICE)
    #CreateIssue(jira,JIRAPROJECT,JIRASUMMARY,JIRADESCRIPTION)
    GetStepInfo(jira,JIRASERVICE,user,PASSWORD,DEBUG)    
####################################################################################################    
def Authenticate(JIRASERVICE,DEBUG):
    host=JIRASERVICE
    credentials = netrc.netrc()
    auth = credentials.authenticators(host)
    if auth:
        user = auth[0]
        PASSWORD = auth[2]
        print "Got .netrc OK"
    else:
        print "ERROR: .netrc file problem (Server:{0} . EXITING!".format(host)
        sys.exit(1)

    f = requests.get(host,auth=(user, PASSWORD))
         
    # CHECK WRONG AUTHENTICATION    
    header=str(f.headers)
    HeaderCheck = re.search( r"(.*?)(AUTHENTICATION_DENIED|AUTHENTICATION_FAILED)", header)
    if HeaderCheck:
        CurrentGroups=HeaderCheck.groups()    
        print ("Group 1: %s" % CurrentGroups[0]) 
        print ("Group 2: %s" % CurrentGroups[1]) 
        print ("Header: %s" % header)         
        print "Authentication FAILED - HEADER: {0}".format(header) 
        print "--> ERROR: Apparantly user authentication gone wrong. EXITING!"
        sys.exit(1)
    else:
        print "Authentication OK"
        if (DEBUG):
          print"HEADER: {0}".format(header)    
    print "---------------------------------------------------------"
    return user,PASSWORD

###################################################################################    
def DoJIRAStuff(user,PASSWORD,JIRASERVICE):
 jira_server=JIRASERVICE
 try:
     print("Connecting to JIRA: %s" % jira_server)
     jira_options = {'server': jira_server}
     jira = JIRA(options=jira_options,basic_auth=(user,PASSWORD))
     print "JIRA Authorization OK"
 except Exception,e:
    print("Failed to connect to JIRA: %s" % e)
 return jira   
    
####################################################################################
def CreateIssue(jira,JIRAPROJECT,JIRASUMMARY,JIRADESCRIPTION):
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
def GetStepInfo(jira,JIRASERVICE,user,PASSWORD,DEBUG):
    
    print "Debug:{0}".format(DEBUG)
    
    headers = {'Content-Type': 'application/json'}
    # URL="{0}/rest/plugins/applications/1.0/installed/jira-software/license".format(JIRASERVICE)  # server license info
    URL="{0}/rest/plugins/1.0/".format(JIRASERVICE) # get plugins
    #URL="{0}/rest/api/2/".format(JIRASERVICE)
    r=requests.get(URL, headers,  auth=(user, PASSWORD))
 
    if (DEBUG):
        print "Headers:{0}".format(r.headers)
        print "VIESTI:{0}".format((r.text).encode('utf-8'))
    
    if (r.status_code == requests.codes.ok):
        print ("ok")
        data = json.loads(r.text)
        if (DEBUG):
            print "PLUGIN RAW DATA:{0}".format(data)
            print "*********************"
            print "SORTED DATA:"
            print(json.dumps(data, indent=4, sort_keys=True))

        sorted_data = sorted(data["plugins"], key=lambda k: k['name'])
        if (DEBUG):
            print "PLUGIN NAME SORTED_DATA:"
            print(json.dumps(sorted_data, indent=4, sort_keys=True))
            pprint.pprint(data) # jsut tested pprint library
        
        for item in sorted_data:
           

            if (item["enabled"] and item["userInstalled"] and item["usesLicensing"]): 
                pluginkey = item["key"]
                URL="{0}/rest/plugins/1.0/{1}-key/license".format(JIRASERVICE,pluginkey) # license info for one plugin (key)
                r=requests.get(URL, headers,  auth=(user, PASSWORD))
                if (DEBUG):
                    print "Headers:{0}".format(r.headers)
                    print "VIESTI:{0}".format((r.text).encode('utf-8'))
                
                # TODO: SHOULD CHECK FAIL
                licenseinfo = json.loads(r.text)
                if (DEBUG):
                    print(json.dumps(licenseinfo, indent=4, sort_keys=True))
                
                print "PLUGIN:{0:35s} VERSION:{1:10s} KEY:{2:40s}".format(item["name"],item["version"],pluginkey)
                
                if "maintenanceExpiryDate" in licenseinfo:
                    #ExpDate=licenseinfo["maintenanceExpiryDate"] # the mystical number string
                    ExpDate=licenseinfo["maintenanceExpiryDateString"]
                    print "EXPIRATION DATE:{0}".format(ExpDate)
                    Converdate = datetime.datetime.strptime(ExpDate, '%d/%b/%y')
                    #Twoweeks = datetime.datetime.now() - datetime.timedelta(weeks=2)
                    if (datetime.datetime.now() < Converdate):
                        Exprdelta=(Converdate - datetime.datetime.now()).days
                        print "--> LICENCE IS VALID ---> TO BE EXPIRED IN:{0} DAYS".format(Exprdelta)
                    if(datetime.datetime.now() > Converdate):
                        print "--> ERROR: LICENCE EXPIRED. ARGH"
                        
                else:
                    ExpDate="NONENONE" # dead code
                print "------------------------------------------------------------------------------------------"
            
            #print "-------------------------------------------------------------------------"
    else:
        print ("FAIL")
    
        
if __name__ == "__main__":
        main(sys.argv[1:])
        
        

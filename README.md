
**Description**

Jira Plugin Info Tol

* Getting info from  Jira installed plugins 


**Requirements**

* Python 2.7
* Use pip install -r requirements.txt to install needed libraries
* Recommending usage of Python virtual env


**Authentication**

* .netrc file used to provide logging credentials (lives in home directory)
* Remember .netrc file protection!  (chmod 600 .netrc )
* .netrc content example

```python
machine jira.mycompany.com
	
login myadmin_account
	
password mypassword
```

**Usage**

```python
  python GetInfo.py -j https://jira.mycompany.com   (default 30days expr limit)
  python GetInfo.py -j https://jira.mycompany.com  -t 50 (marks all license expr days in next 50 days as an alarm))
  
  with trafic and header info: python GetInfo.py -j https://jira.mycompany.com -d ON
  developerdebug mode: GetInfo.py -j https://jira.mycompany.com -l ON
    
    Return values: 
    300=black (auth or connection issues, no RESTAPI connection made)
    301=red (expired plugins)
    302=yellow (plugins to be expired inside given days limit found)
    303=green (all plugins with valid licenses)
    304= (tool/auth issues)
  
  Example summary info:

2019-03-05 08:05:38,880:GetInfo.py:INFO:***** STATUS SUMMARY FOR:https://<server-name> **************
2019-03-05 08:05:38,880:GetInfo.py:INFO:Plugins with OK Expiration date in future:1
2019-03-05 08:05:38,880:GetInfo.py:INFO:Plugins with ALARM Expiration:2 
2019-03-05 08:05:38,880:GetInfo.py:INFO:Plugins with FAILED Expiration:46 
2019-03-05 08:05:38,880:GetInfo.py:INFO:==> STATUS: RED
  
  
```

**Author**
mika.nokka1@gmail.com

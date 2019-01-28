
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


  python GetInfo.py -j https://jira.mycompany.com
  with trafic and header info: python GetInfo.py -j https://jira.mycompany.com -d ON


**Author**
mika.nokka1@gmail.com

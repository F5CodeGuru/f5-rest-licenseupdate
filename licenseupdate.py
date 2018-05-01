from datetime import datetime, timedelta
import os, sys
import requests
import json

#curl -k -u admin:bigip123 -X GET https://192.168.8.253/mgmt/tm/sys/license
#Globals, should be configured to match your environment
adminUser = 'admin'
adminPass = 'bigip123'
scheme = 'https://'
path = '/mgmt/tm/sys/license'
daysTillLicenseRenew = 15
licenseFileExtenstion = '.txt'

restHeaders = {
    'Accept': 'application/json',
    'Content-Type': 'application/json; charset=UTF-8'
}

platformList = [ 'Z100' ]

def createRegKeyFiles():

	for platformID in platformList:

		REGKEYFILE = platformID + licenseFileExtenstion

		if not os.path.exists(REGKEYFILE):
		
			REGKEYFILEHANDLE = open(REGKEYFILE,'w')
			REGKEYFILEHANDLE.close

createRegKeyFiles()

#List (python array) to store ips from file
bigipList = []

if len(sys.argv) < 1:
    sys.exit('Usage: %s <bigip IP>' % sys.argv[0])

if not os.path.exists(sys.argv[1]):
    sys.exit('ERROR: File %s was not found!' % sys.argv[1])

#file with bigip ip list is the command line argument
bigipList = [line.rstrip() for line in open(sys.argv[1], 'r')]
    

    


#Http connection
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

#licenseFileList = []

#with open('ve.lic', 'r') as f:
#    licenseFileList = f.readlines()
    

#iterate through list of bigip ips and run run the change against each one
for bigip in bigipList:

	body = ''
	uri = scheme + bigip + path
	
	print ("Contacting bigip: " + uri)

	r = requests.get(uri,headers=restHeaders,auth=(adminUser,adminPass),verify=False)
	print(r.status_code)
	
        
	#Convert json data into python dictionary (hash/associative array)
	licenseData = json.loads(r.text)
	
	licenseEndDate = licenseData['entries']['https://localhost/mgmt/tm/sys/license/0']['nestedStats']['entries']['licenseEndDate']['description']
	platformID = licenseData['entries']['https://localhost/mgmt/tm/sys/license/0']['nestedStats']['entries']['platformId']['description']
	print(platformID)
	licenseEndDateObject = datetime.strptime(licenseEndDate, "%Y/%m/%d")
	print(licenseEndDateObject)	
	
	#curl -k -u admin:bigip123 https://192.168.8.253/mgmt/tm/sys/hardware | sed 's/,/\'$'\n/g'
	
	if ((licenseEndDateObject - datetime.now()) < timedelta(days=daysTillLicenseRenew)):
		
		regKeyFilename = platformID + licenseFileExtenstion
		
		print("License is old: " + regKeyFilename)

		if os.path.exists(regKeyFilename) and (os.path.getsize(regKeyFilename) > 0):
		
			print("Z100 key file ok")

			regKeyList = [line.rstrip() for line in open(regKeyFilename, 'r')]
			regKeyToBeInstalled = regKeyList.pop(0)
			
			open(regKeyFilename, 'w').close()
			
			
			REGKEYLISTFILEHANDLE = open(regKeyFilename, 'w')
			for regKeyTemp in regKeyList:
			
				REGKEYLISTFILEHANDLE.write(regKeyTemp)
			
			REGKEYLISTFILEHANDLE.close()	
			
			#regKeyData = json.dumps({'command':'install','registration-key':regKey}) 
			regKeyData = json.dumps({'command':'run', 'utilCmdArgs':'-c \"tmsh install /sys license registration-key ' + regKeyToBeInstalled + '\"'}) 


			uri = scheme + bigip + '/mgmt/tm/util/bash'

			r = requests.post(uri,regKeyData,headers=restHeaders,auth=(adminUser,adminPass),verify=False)
			print(r.text)


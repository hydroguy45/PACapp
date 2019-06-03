from __future__ import print_function
from pprint import pprint
from googleapiclient import discovery
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import time
import json
import os

# Setup the Sheets API
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
store = file.Storage('/root/PACapp/Backend/credentials.json')
creds = store.get()
if not creds or creds.invalid:
	flow = client.flow_from_clientsecrets('/root/PACapp/Backend/client_secret.json', SCOPES)
	creds = tools.run_flow(flow, store)
service = discovery.build('sheets', 'v4', credentials=creds)
spreadsheet_id = '1vGwybPul8-9r-u1Oj_5sHO6RxG-fqyNTTmcU7ajfBd0'
queries = 0

def getPACData():
	print("[Attempting to load & Parse PAC data]")
	PACSheet = "Group Credentials"
	pacData = {}
	#Get Subcommittee data
	print("Loading subcommittee data")
	subcomittees = {}
	rows = getList(PACSheet,"A", "A",2)
	for row in rows:
		print("Looking at "+row[0])
		subcomittees[row[0]] = getSubcommitteeData(row[0])
	pacData["Subcomittees"] = subcomittees
        pacData["Calendar"] = getList(PACSheet, "L","L")
	#Announcements
	print("Loading PAC wide announcements")
	announcements = []
	rows = getList(PACSheet,"C", "E", 5)
	for row in rows:
		announcement = {"Announcement":row[0], "Date":row[1], "Time":row[2]}
		announcements.append(announcement)
	pacData["Announcements"] = announcements
	#General Performance Deadlines
	print("Loading PAC wide deadlines")
	deadlines = []
	rows = getList(PACSheet,"G", "H", 3)
	for row in rows:
		deadline = {"What":row[0], "When":row[1]}
		deadlines.append(deadline)
	pacData["Deadlines"] = deadlines
	#Spaces
	print("Loading location data")
	spaces = {}
	rows = getList(PACSheet,"J","J", 2)
	for row in rows:
		print("Looking at "+row[0])
		spaces[row[0]] = getLocationData(row[0])
	pacData["Spaces"] = spaces
	#Done
	#pprint(pacData)
	return pacData

def getLocationData(name):
	location = {}
	#Announcements
	print(" -Loading announcements")
	announcements = []
	rows = getList(name, "A","C",5)
	for row in rows:
		announcement = {"Announcement":row[0],"Date":row[1],"Time":row[2]}
		announcements.append(announcement)
	location["Announcements"] = announcements
	#Deadlines
	print(" -Loading deadlines")
	deadlines = []
	rows = getList(name,"E", "F", 3)
	for row in rows:
		deadline = {"What":row[0], "When":row[1]}
		deadlines.append(deadline)
	location["Deadlines"] = deadlines
	return location

def getSubcommitteeData(name):
	subcomittee = {}
	#Deadlines
	print(" -Loading deadlines")
	deadlines = []
	rows = getList(name, "G", "H", 3)
	for row in rows:
		deadline = {"What":row[0],"When":row[1]}
		deadlines.append(deadline)
	subcomittee["Deadlines"] = deadlines
        #Calendar
        subcomittee["Calendar"] = getList(name,"J","J")
	#Subcommittee Announcements
	print(" -Loading announcements")
	announcements = []
	rows = getList(name, "C", "E", 5)
	for row in rows:
		announcement = {"Announcement":row[0], "Date":row[1], "Time":row[2]}
		announcements.append(announcement)
	subcomittee["Announcements"] = announcements
	#Group data
	print(" -Loading groups")
	groups = {}
	rows = getList(name, "A", "A")
	for row in rows:
		print("   >Looking at "+row[0])
		groups[row[0]] = (getGroupData(row[0]))
	subcomittee["Groups"] = groups
	return subcomittee

def getGroupData(name):
	group = {}
	#Add group members
	persons = []
	rows = getList(name, "A", "E")
	for row in rows:
            person = {"Name":row[0],"Position":row[1],"Email":row[2],"Expected Year of Graduation":row[3],"Receive Emails":row[4],"Index":row[5]}
	    persons.append(person)
	group["Persons"] = persons
	#Add group performance details
	performanceDetails = {}
	rows = getRange(name, "F", "G", 12, 20)
	for row in rows:
		performanceDetails[row[0]] = row[1]
	group["Performance Details"] = performanceDetails
	rows = getRange(name,"H","I",12,13)
	for row in rows:
		group["Performance Details"][row[0]] = row[1]
	#Add group announcements
	announcements = []
	rows = getList(name, "F", "H", 26)
	for row in rows:
		announcement = {"Announcement":row[0], "Date":row[1], "Time":row[2]};
		announcements.append(announcement)
	group["Announcements"] = announcements
	#Add group demerits
	demerits = []
	rows = getRange(name, "F","H",3,10)
	for row in rows:
		demerit = {"Title":row[0], "Date":row[1],"Reason":row[2]}
		demerits.append(demerit)
	group["Demerits"] = demerits
	return group

def getRange(name, lowerEnd, higherEnd, startingRow, endingRow):
	global queries
	queries = queries + 1
	if queries == 90:
		time.sleep(100)
		queries = 0
	rows = []
	range_ = name+'!'+lowerEnd+str(startingRow)+':'+higherEnd+str(endingRow)
	request = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_)
	response = request.execute()
	values = response.get('values', [])
	if not values:
		print('No data found.')
	else:
		#print('Groups:')
		#print(len(values))
                index=-1
		for row in values:
			index = index + 1
                        if(len(row) != 0):
				numberOfColumns = ord(higherEnd[0]) -  ord(lowerEnd[0]) + 1
				while(len(row) < numberOfColumns):
					row.append("")
				row.append(index)
                                rows.append(row)
	return rows

def getList(name, lowerEnd, higherEnd, startingRow=2):
	global queries
	rows = []
	rowLowerEnd = startingRow
	gotAllTheNames = False
	while(not gotAllTheNames):
		queries = queries + 1
		if queries == 90:
			time.sleep(100)
			queries = 0
		rowHigherEnd = 29 + rowLowerEnd
		range_ = name+'!'+lowerEnd+str(rowLowerEnd)+':'+higherEnd+str(rowHigherEnd)
		request = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_)
		response = request.execute()
		#pprint(response)
		values = response.get('values', [])
		if not values:
			print('     *No data found.')
			gotAllTheNames = True
		else:
			#print('Groups:')
			#print(len(values))
			if len(values) != 30:
				#print("Final buffer")
				gotAllTheNames = True
			else:
				#print("Potentially more members left")
				gotAllTheNames = False
			index = 0
                        for row in values:
				index = index + 1
                                if(len(row) != 0):
					numberOfColumns = ord(higherEnd[0]) -  ord(lowerEnd[0]) + 1
					while(len(row) < numberOfColumns):
						row.append("")
                                        row.append(index)
					rows.append(row)
		rowLowerEnd = rowHigherEnd+1
	return rows
def getModifications():
    modificationFile = "/root/PACapp/Backend/modificationQueue.json"
    f = open(modificationFile,"rw+")
    modificationQueue = json.loads(f.read())
    f.seek(0)
    f.truncate()
    f.write("[]")
    f.close()
    return modificationQueue

def commitModifications(modificationQueue):
    global queries
    for modification in modificationQueue:
        persons = []
	rows = getList(modification["groupName"], "A", "E")
	exists = False
        for row in rows:
            person = {"Name":row[0],"Position":row[1],"Email":row[2],"Expected Year of Graduation":row[3],"Receive Emails":row[4]}
	    persons.append(person)
            if modification["field"]!="synch":
                print("Looking at person \"{}\" and index {}".format(row[0],row[5]))
                if row[0] == modification["personName"] and row[5]==int(modification["index"]):
                    print("Trying to push")
                    field = modification["field"]
                    row="{}".format(int(modification["index"])+1)
                    column = "A" if (field=="Name") else "B" if (field=="Position") else "C" if (field=="Email") else "D" if (field=="Expected Year of Graduation") else "E"
                    range_=modification["groupName"]+'!'+column+row+":"+column+row
                    Body={'values':[[modification['value']]]}
                    queries = queries + 1
		    if queries == 90:
			time.sleep(100)
			queries = 0
                    change =  service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=range_, valueInputOption="RAW", body=Body)
                    print(change)
                    result = change.execute()
                    print(result)
                    break
        if modification["field"]=="synch":
            overrideCopy = modification["value"]
            currentCopyLength = len(persons)
            overrideCopyLength = len(overrideCopy)
            row = max(overrideCopyLength, currentCopyLength)
            range_=modification["groupName"]+"!A2:E"+"{}".format(int(row+1))
            values = [[x["Name"],x["Position"],x["Email"],x["Expected Year of Graduation"],x["Receive Emails"]] for x in overrideCopy]
            while len(values) < row:
                values.append(["","","","",""])
            Body = {'values':values}
            queries = queries + 1
            if queries == 90:
                time.sleep(100)
                queries = 0
            change =  service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=range_, valueInputOption="RAW", body=Body)
            print(change)
            result = change.execute()
            print(result)
        #TODO: else you need to find the first person with the same name
    return "Fixed"

def cacheData():
	queries = 0
        print("Loading Modifications")
        modificationQueue = getModifications()
        print(modificationQueue)
        commitModifications(modificationQueue)
	PACdata = getPACData()
	cacheFile = "/root/PACapp/Backend/cache.json"
	f = open(cacheFile, "w")
	json.dump(PACdata, f)
	f.close()

cacheData()
print("Launching the calendarCache application")
os.system('/usr/bin/python /root/PACapp/Backend/calendarCache.py')

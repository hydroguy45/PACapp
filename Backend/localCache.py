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
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
store = file.Storage('credentials.json')
creds = store.get()
if not creds or creds.invalid:
	flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
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
	pprint(pacData)
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
	rows = getList(name, "A", "D")
	for row in rows:
		person = {"Name":row[0],"Position":row[1],"Email":row[2],"Expected Year of Graduation":row[3]}
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
		for row in values:
			if(len(row) != 0):
				numberOfColumns = ord(higherEnd[0]) -  ord(lowerEnd[0]) + 1
				while(len(row) < numberOfColumns):
					row.append("")
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
			for row in values:
				if(len(row) != 0):
					numberOfColumns = ord(higherEnd[0]) -  ord(lowerEnd[0]) + 1
					while(len(row) < numberOfColumns):
						row.append("")
					rows.append(row)
		rowLowerEnd = rowHigherEnd+1
	return rows

def cacheData():
	queries = 0
	PACdata = getPACData()
	cacheFile = "cache.json"
	f = open(cacheFile, "w")
	json.dump(PACdata, f)
	f.close()

cacheData()
print("Launching the calendarCache application")
os.system('python calendarCache.py')

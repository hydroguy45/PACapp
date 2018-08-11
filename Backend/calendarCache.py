from __future__ import print_function
import datetime
from oauth2client import file, client, tools
from apiclient.discovery import build
from google.oauth2 import service_account
import pprint
import dateutil.parser
from dateutil.tz import gettz
import datetime
import json
import time
# Setup the Calendar API
cachedData = {}
SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'My Project-80c8a8763136.json'
credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('calendar', 'v3', credentials=credentials)
pp = pprint.PrettyPrinter(indent=4)

def loadGroupDataFromCache():
    global cachedData
    raw_json = open("cache.json").read()
    cachedData = json.loads(raw_json)

def getGroupInfo(subcomittee, groupName):
	subcomittees = cachedData["Subcomittees"]
	SubComitteeData = subcomittees[subcomittee]
	GroupData = SubComitteeData["Groups"][groupName]
	Deadlines = cachedData["Deadlines"] + SubComitteeData["Deadlines"]
	Announcements = cachedData["Announcements"] + SubComitteeData["Announcements"] + GroupData["Announcements"]
	Demerits = GroupData["Demerits"]
	Persons = GroupData["Persons"]
	Details = GroupData["Performance Details"]
	SpaceName = Details["Location (as seen in sheet tag)"]
	if(SpaceName != ""):
		Space = cachedData["Spaces"][SpaceName]
		Announcements = Announcements + Space["Announcements"]
		Deadlines = Deadlines + Space["Deadlines"]
	ResultData = {
		"Deadlines":Deadlines,
		"Announcements":Announcements,
		"Demerits":Demerits,
		"Persons":Persons,
		"Details":Details
	}
	return ResultData

def getGroupRequiredEventsForGroup(subcomittee,groupName):
    groupInfo = getGroupInfo(subcomittee, groupName)
    events = []
    if groupInfo["Details"]["Date (mm/dd/yyyy)"] != "":
        performance = dateutil.parser.parse(groupInfo["Details"]["Date (mm/dd/yyyy)"], tzinfos={None:gettz("America/New_York")})
        for dueDate in groupInfo["Deadlines"]:
            dateOffset = int(dueDate["When"])
            date = performance - datetime.timedelta(days=dateOffset)
            events.append((date,dueDate["What"]))
    else:
        print("{} is missing a performance date".format(groupName))
    return events

# Call the Calendar API
def getUpcomingEventsFromCalendar(calID):
    print(calID)
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    #Gets 250 upcoming events
    events_result = service.events().list(calendarId=calID, timeMin=now, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    pairsWithIDs = []
    pairs = []
    if not events:
        print('No upcoming events found.')
    for event in events:
        #pp.pprint(event)
        start = dateutil.parser.parse(event['start'].get('dateTime', event['start'].get('date')), tzinfos={None:gettz("America/New_York")})
        #print(start, event['summary'])
        pairs.append((start, event['summary']))
        pairsWithIDs.append((event['id'],start, event['summary']))
    return (pairsWithIDs, pairs)

def addEventToCalendar(event, calID):
    start=event[0].isoformat()
    end=(event[0]+datetime.timedelta(minutes=30)).isoformat()
    summaryOfEvent=event[1]
    eventFormated = {
      'summary': summaryOfEvent,
      'start': {
        'dateTime': start,
        'timeZone': 'America/New_York',
      },
      'end': {
        'dateTime': end,
        'timeZone': 'America/New_York',
      },
      'recurrence': [],
      'attendees': [],
      'reminders': {
        'useDefault':True,
        'overrides': [],
      },
    }
    service.events().insert(calendarId=calID, body=eventFormated).execute()
    print("Adding events to calendar")

def rectifyDescripanciesOnGroupCalendar(subcomittee, groupName):
    calID = cachedData["Subcomittees"][subcomittee]["Groups"][groupName]["Performance Details"]["Preproduction Calendar"].rstrip()
    eventsWithIDs, eventsInCalendar = getUpcomingEventsFromCalendar(calID)
    groupEvents = getGroupRequiredEventsForGroup(subcomittee, groupName)
    for event in groupEvents:
        if event not in eventsInCalendar:
            print("Adding new events")
            addEventToCalendar(event,calID)
    for i in range(0,len(eventsInCalendar)):
        event = eventsInCalendar[i]
        eventWithId = eventsWithIDs[i]
        if event not in groupEvents:
            print("Removing event that isn't appart of pre-prod cycle")
            removalID = eventWithId[0]
            print("ID to remove is {} and the event summary is \"{}\"".format(removalID, eventWithId[2]))
            service.events().delete(calendarId=calID, eventId=removalID).execute()

if __name__=="__main__":
    print("Starting the calendar cache application")
    loadGroupDataFromCache()
#    mainEvents = getUpcomingEventsFromCalendar('gj1lt5vrqqegdhncc1cmm3t10k@group.calendar.google.com')
#    pp.pprint(mainEvents)
#    rectifyDescripanciesOnGroupCalendar("SMAC", "Bloomers")
    index = 1
    for subcomittee in cachedData["Subcomittees"]:
        for group in cachedData["Subcomittees"][subcomittee]["Groups"]:
            print("\nInspecting calendar for {} which is a part of {}".format(group, subcomittee))
            rectifyDescripanciesOnGroupCalendar(subcomittee, group)
            if index == 10:
                time.sleep(100)
                index = 1
            index = index + 1

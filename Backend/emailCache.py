from __future__ import print_function
from pprint import pprint
from googleapiclient import discovery
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import time
import json
import os

store = file.Storage('/root/PACapp/Backend/credentials.json')
creds = store.get()
pp = pprint.PrettyPrinter(indent=4)

cachedData = {}

def loadGroupDataFromCache():
    global cachedData
    raw_json = open("/root/PACapp/Backend/cache.json").read()
    cachedData = json.loads(raw_json)
def getGroupRequiredEventsForGroup(group):
    events = []
    if group["Details"]["Date (mm/dd/yyyy)"] != "":
        performance = dateutil.parser.parse(group["Details"]["Date (mm/dd/yyyy)"],tzinfos={None:gettz("America/New_York")})
        performance = performance - datetime.timedelta((performance.weekday()+1)%7)
        for dueDate in group["Deadlines"]:
            dateOffset = int(dueDate["When"])
            date = performance - datetime.timedelta(days=dateOffset)
            events.append((date,dueDate["What"]))
    else:
        print("     Missing a performance date")
    return events

def formatEmail(group):
    result = str("<html><head></head><body><p><a href=\"https://calendar.google.com/calendar/htmlembed?mode=ADGENDA&src=")
    result += str(group["Performance Details"]["Preproduction Calendar"])+str("\">Performance  Calendar</a>")
    result += str("[Performance Deadlines]<br>")
    events = getGroupRequiredEventsForGroup(group)
    for index in events:
        date = events[index][0]
        what = events[index][1]
        results += str(" " )+str(date)+str("<br>")
        results += str("   ")+str(what)+str("<br>")
    calendarIframe = group["Performance Details"]["Embedded Calendar Link"]
    result += str(calendarIframe)
    result += str("</p></body></html>")
    return result

def getEmailRecipientListForGroup(group):
    result = []
    for index in group["Persons"]:
        person = group["Persons"][index]
        receive = person["Receive Emails"]
        if receive == "y" or recieve == "Y" or receive == "Yes" or receive == "yes":
            result.append(person["Email"])
    return result

def sendEmailToGroup(message, group):
    recipientList = getEmailRecipientListForGroup(group)
    print("TODO: make email send function")

if __name__=="__main__":
    for subcomittee in cachedData["Subcomittees"]:
        for groupName in cachedData["Subcomittees"][subcomittee]["Groups"]:
            group = cachedData["Subcomittees"][subcomittee]["Groups"][groupName]
            message = formatEmail(group)
            sendEmailToGroup(message, group)

from __future__ import print_function
import pprint
import base64
from email.mime.text import MIMEText
import mimetypes
from apiclient import errors
from google.oauth2 import service_account
from googleapiclient import discovery
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import time
import datetime
from dateutil.tz import gettz
import dateutil.parser
import pytz
import json
import os
import pickle
import os.path
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
DEBUG_MODE = False
SERVICE_ACCOUNT_FILE = '/root/PACapp/Backend/My Project-80c8a8763136.json'
SCOPES =['https://www.googleapis.com/auth/gmail.send']
credentials = None#service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
#delegated_creds = credentials.create_delegated('thepacapp@gmail.com')
#http_auth = delegated_creds.authorize(Http())
if os.path.exists('token.pickle'):
    with open('token.pickle','rb') as token:
        credentials = pickle.load(token)
if not credentials or not credentials.valid:
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    else:
        secret = 'client_secret.json'
        flow = InstalledAppFlow.from_client_secrets_file(secret, SCOPES)
        credentials = flow.run_local_server()
    with open('token.pickle', 'wb') as token:
        pickle.dump(credentials, token)
service = build('gmail', 'v1', credentials=credentials)
#creds = flow.run_local_server()
#service = build('gmail', 'v1', credentials=creds)
pp = pprint.PrettyPrinter(indent=4)

#Gmail API Functions
def create_message(sender, to, subject, message_text):
  """Create a message for an email.

  Args:
    sender: Email address of the sender.
    to: List of email addresses of receivers

  Returns:
    An object containing a base64url encoded email object.
  """
  toFormated = ", ".join(receiver for receiver in to)
  print(toFormated)
  message = MIMEText(message_text, 'html')
  message['to'] = toFormated
  message['from'] = sender
  message['subject'] = subject
  return {'raw': base64.urlsafe_b64encode(message.as_string()), 'payload':{'mimeType':'text/html'}}

def send_message(service, user_id, message):
  """Send an email message.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    message: Message to be sent.

  Returns:
    Sent Message.
  """
  if(DEBUG_MODE):
    return message
  try:
    message = (service.users().messages().send(userId=user_id, body=message)
               .execute())
    print('Message Id: %s' % message['id'])
    return message
  except errors.HttpError, error:
    print('An error occurred: %s' % error)


#Cache Parsing Functions
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
            if date >= datetime.datetime.now(tz=gettz("America/New_York")):
                events.append((date,dueDate["What"]))
    else:
        print("     Missing a performance date")
    return events

def formatEmail(group, groupName):
    result = str("<html><head></head><body><p><h2><a href=\"https://calendar.google.com/calendar/htmlembed?mode=AGENDA&src=")
    result += str(group["Details"]["Preproduction Calendar"])+str("\">Performance  Calendar Upcoming Deadlines</a></h2><br><ul><li>")
    events = getGroupRequiredEventsForGroup(group)
    previousDate = None
    events.sort(key=lambda index:index[0])
    for index in events:
        date = index[0].strftime('<strong>Due %m-%d-%y</strong>')
        #print(type(date))
        if previousDate == None:
            result += str(date)
        if previousDate != None and not(previousDate.year == index[0].year and previousDate.month == index[0].month and previousDate.day == index[0].day):
            result += str("</li><li>") + str(date)
        previousDate = index[0]
        what = index[1]
        result += str("<br>  >")+str(what)
    if(len(events)==0):
        result+= "No Upcoming Performance Deadlines"
    result += "</li></ul>Please remember to check the PAC calendar and your subcomittee's calendar." 
    result += "<br><br>You can unsubscribe from these emails by login into the PAC App <a href='https://play.google.com/store/apps/details?id=com.PACapp.demo&pcampaignid=MKT-Other-global-all-co-prtnr-py-PartBadge-Mar2515-1'>application</a> or "
    result += "<a href='upenn.pennpacapp.com'>website</a> with the username:\""+str(groupName)+"\" and password:\""
    result += group["Details"]["PAC App password"] + "\" and looking under \"Your Group Details\""
    calendarIframe = group["Details"]["Embedded Calendar Link"]
    result += str(calendarIframe)
    result += str("</p></body></html>")
    return result

def getEmailRecipientListForGroup(group):
    result = []
    for person in group["Persons"]:
        receive = person["Receive Emails"]
        if receive == "y" or receive == "Y" or receive == "Yes" or receive == "yes":
            result.append(person["Email"])
    return result
   
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
def generateTitle(groupName):
    return "[PAC APP] Monthly Event Reminder for "+groupName 
def sendEmailToGroup(message, group, groupName):
    recipientList = getEmailRecipientListForGroup(group)
    if(len(recipientList)==0):
        return
    print("For group ({}) recipients".format(groupName))
    pp.pprint(recipientList)
    SENDER = "thepacapp@gmail.com"
    title = generateTitle(groupName)
    email = create_message(SENDER, recipientList, title, message)
    send_message(service, "me", email)

if __name__=="__main__":
    #Load Cache
    loadGroupDataFromCache()
    #Use Gmail API to email people in every group
    for subcomittee in cachedData["Subcomittees"]:
        for groupName in cachedData["Subcomittees"][subcomittee]["Groups"]:
            group = getGroupInfo(subcomittee, groupName)
            #pp.pprint(group)
            message = formatEmail(group, groupName)
            sendEmailToGroup(message, group, groupName)

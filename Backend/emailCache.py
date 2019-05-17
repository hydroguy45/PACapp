from __future__ import print_function
import pprint
from google.oauth2 import service_account
from googleapiclient import discovery
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
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
SERVICE_ACCOUNT_FILE = '/root/PACapp/Backend/My Project-80c8a8763136.json'
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
#flow = InstalledAppFlow.from_client_secrets_file(
 #               'credentials_email.json', SCOPES)
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('gmail', 'v1', credentials=credentials)
#creds = flow.run_local_server()
#service = build('gmail', 'v1', credentials=creds)
pp = pprint.PrettyPrinter(indent=4)

#Gmail API Functions
def create_message(sender, to, subject, message_text):
  """Create a message for an email.

  Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.

  Returns:
    An object containing a base64url encoded email object.
  """
  message = MIMEText(message_text)
  message['to'] = to
  message['from'] = sender
  message['subject'] = subject
  return {'raw': base64.urlsafe_b64encode(message.as_string())}

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
    if group["Performance Details"]["Date (mm/dd/yyyy)"] != "":
        performance = dateutil.parser.parse(group["Performance Details"]["Date (mm/dd/yyyy)"],tzinfos={None:gettz("America/New_York")})
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
    SENDER = "thepacapp@gmail.com"
    email = create_message(SENDER, "foleych@seas.upenn.edu", "[PAC APP] Monthly Event Reminder", message)
    send_message(service, "me", email)
    print("TODO: make email send function")

if __name__=="__main__":
    #Load Cache
    loadGroupDataFromCache()
    # Call the Gmail API
    pp.pprint(cachedData)
    for subcomittee in cachedData["Subcomittees"]:
        for groupName in cachedData["Subcomittees"][subcomittee]["Groups"]:
            group = cachedData["Subcomittees"][subcomittee]["Groups"][groupName]
            message = formatEmail(group)
            sendEmailToGroup(message, group)

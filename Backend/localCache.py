from __future__ import print_function
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import json
PACAppSheetUrl = "https://docs.google.com/spreadsheets/d/1vGwy/bPul8-9r-u10j_5sH06RxG-fqyNTTmcU7ajfBd0/edit#gid=0"

#Setup the sheets API
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
store = file.Storage('credentials.json')
creds = store.get()
if not creds or creds.invalid:
	flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
	creds = tools.run_flow(flow, store)
service = build('sheets', 'v4', http=creds.authorize(Http()))

# Call the sheets API
SPREADSHEET_ID = '1vGwybPul8-9r-u10j_5sH06RxG-fqyNTTmcU7ajfBd0'
RANGE_NAME = 'Group Credentials!A2:A5'
result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
values=result.get('values',[])
if not values:
	print('No data found.')
else:
	print('Name, Major:')
	for row in values:
		print('%s, %s' % (row[0], row[4]))

#def saveDictionary(dictionary, filename):
#	f = open(filename, "w")
#	json.dump(dictionary, f)
#	f.close()

#	gc = pygsheets.authorize()
#	with gc.open(url) as sheet:
	
#if __name__ == "__main__":
#	sampleDic = {'a':1, 'b':2}
#	testFilename = "test.txt"
#	saveDictionary(sampleDic, testFilename)

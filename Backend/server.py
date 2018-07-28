from wsgiref.simple_server import make_server
from pyramid.events import NewRequest, subscriber
from pyramid.config import Configurator
from pyramid.response import Response
import json
import time
import threading
import os
HOST = "0.0.0.0"
PORT = 8080

cachedData = {}
def loadJSON():
	global cachedData
	raw_json = open("cache.json").read()
	cachedData = json.loads(raw_json)
	#print(json.dumps(cachedData["Subcomittees"]["ACK"]))

def getPerformances():
	performances = []
	subcomitteeDict = getGroups()
	for subcomitteeName in subcomitteeDict:
		for group in subcomitteeDict[subcomitteeName]:
			performanceDetails = cachedData["Subcomittees"][subcomitteeName]["Groups"][group]["Performance Details"]
			performance = {
				"Description":performanceDetails["Description"],
				"Title":performanceDetails["Performance title"],
				"Cost":performanceDetails["Cost of tickets"],
				"Family friendly?":performanceDetails["Family friendly?"],
				"Date":performanceDetails["Date (mm/dd/yyyy)"],
				"Location":performanceDetails["Location (as seen in sheet tag)"]
			}
			if(performance["Date"]!="" and performance["Location"]!=""):
				performances.append(performance)
	return performances

def getPerformancesAsString(request):
	return Response(json.dumps(getPerformances()))

def getGroups():
	allGroups = {}
	for subcomitteeName in cachedData["Subcomittees"]:
		subcomittee = cachedData["Subcomittees"][subcomitteeName]
		groups = []
		for groupName in subcomittee["Groups"]:
			groups.append(groupName)
		allGroups[subcomitteeName] = groups
	return allGroups

def getGroupsAsString(request):
	return Response(json.dumps(getGroups()))

def getGroupInfo(subcomittee, groupname, password):
	subcomittees = cachedData["Subcomittees"]
	SubComitteeData = subcomittees[subcomittee]
	GroupData = SubComitteeData["Groups"][groupname]
	if(password != GroupData["Performance Details"]["PAC App password"]):
		return "Incorrect Password"
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
#Example
#http://localhost:8080/getInfo?Subcomittee=ACK&Group=PennYo&Password=readthehandbook
def getGroupInfoAsString(request):
	subcomittee = ""
	group = ""
	password = ""
	if "Subcomittee" in request.GET and "Group" in request.GET and "Password" in request.GET:
		subcomittee = request.GET["Subcomittee"]
		group = request.GET["Group"]
		password = request.GET["Password"]
		info = getGroupInfo(subcomittee, group, password)
		return Response(json.dumps(info))
	else:
		return Response("Illegal Argument")

def main(request):
	html = "<h1>The server is up and running</h1></br><p>%s</p>" % json.dumps(getGroupInfo("ACK","Pennsylvania Six-5000", "readthehandbook"))
	return Response(html)

class cachingThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.setDaemon(True)
	def run(self):
		while True:
			print("Caching google docs data")
			os.system('python localCache.py')
			print("Syncing with cache")
			loadJSON()
			print("Waiting till next cache time")
			time.sleep(60*60*23)#Once every 23 hours

def add_cors_headers_response_callback(event):
    def cors_headers(request, response):
        response.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST,GET,DELETE,PUT,OPTIONS',
        'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept, Authorization',
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Max-Age': '1728000',
        })
    event.request.add_response_callback(cors_headers)
	
if __name__ == "__main__":
	print("Loading the google sheets data")
	loadJSON()
	print("Initializing the caching thread")
	cacher = cachingThread()
	cacher.start()
	print("Starting up server")
	with Configurator() as config:
		config.add_subscriber(add_cors_headers_response_callback, NewRequest)

		config.add_route("main", "/")
		config.add_view(main, route_name="main")

		config.add_route("getInfo", "/getInfo")
		config.add_view(getGroupInfoAsString, route_name="getInfo")

		config.add_route("getGroups", "/getGroups")
		config.add_view(getGroupsAsString, route_name="getGroups")

		config.add_route("getPerformances", "/getPerformances")
		config.add_view(getPerformancesAsString, route_name="getPerformances")
		
		config.add_static_view('static', path='../The PAC App/www/')
		
		app=config.make_wsgi_app()
	server = make_server(HOST, PORT, app)
	print("Started server on %s:%d" % (HOST,PORT))
	server.serve_forever()

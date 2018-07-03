from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response
import json
HOST = "0.0.0.0"
PORT = 8080

cachedData = {}
def loadJSON():
	global cachedData
	raw_json = open("cache.json").read()
	cachedData = json.loads(raw_json)
	#print(json.dumps(cachedData["Subcomittees"]["ACK"]))

def getPerformances():
	#TODO: complete
	return []

def getPerformancesAsString():
	return Response("TODO")

def getGroups():
	allGroups = {}
	for subcomitteeName in cacheData["Subcomittees"]:
		subcomittee = cacheData["Subcomittees"][subcomitteeName]
		groups = []
		for groupName in subcomittee["Groups"]:
			groups.append(groupName)
		allGroups[subcomitteeName] = groups
	return allGroups

def getGroupsAsString():
	return Response("TODO")

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
		Deadlines = Deadlines + Spaces["Deadlines"]
	ResultData = {
		"Deadlines":Deadlines,
		"Announcements":Announcements,
		"Demerits":Demerits,
		"Persons":Persons,
		"Details":Details
	}
	return ResultData

def getGroupInfoAsString(request):
	return Response("TODO")

def main(request):
	html = "<h1>The server is up and running</h1></br><p>%s</p>" % json.dumps(getGroupInfo("ACK","Pennsylvania Six-5000", "readthehandbook"))
	return Response(html)

if __name__ == "__main__":
	print("Loading the google sheets data")
	loadJSON()
	print("Starting up server")
	with Configurator() as config:
		config.add_route("main", "/")
		config.add_view(main, route_name="main")
		app=config.make_wsgi_app()
	server = make_server(HOST, PORT, app)
	print("Started server on %s:%d" % (HOST,PORT))
	server.serve_forever()

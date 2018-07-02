from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response
import json
HOST = "0.0.0.0"
PORT = 8080

cachedData = {}
def loadJSON():
	raw_json = open("cache.json").read()
	cachedData = json.loads(raw_json)

def getInfo(request):
	groupname = "test"
	password = "test"
	info = getGroupInfo(groupname, password)
	return Response(info)

def getGroupInfo(groupname, password):
	return "need to get group info"

def main(request):
	return Response("<h1>The server is up and running</h1>")

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

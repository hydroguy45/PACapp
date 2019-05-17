console.log("Starting Server");
var express = require("express");
var app = express();
var fs = require("fs");
var cronJob = require("cron").CronJob;

cachedData = {};
fs.readFile("../cache.json", "utf8", (err, data)=>{
	if(err) {
		console.log(err);
	}
	cachedData = JSON.parse(data);
	console.log(cachedData);
})

new cronJob("00 00 4 * * *", function(){
	console.log("Server.js is querying the cache.json file")
	fs.readFile("../cache.json", "utf8", (err, data)=>{
		if(err) {
			console.log(err);
		}
		cachedData = JSON.parse(data);
		console.log(cachedData);
	})
}, null, true);

app.use(express.static("../../The PAC App/www"));
var server = app.listen(80, function(){
	var port = server.address().port;
	console.log("Server started at http://localhost:%s", port);
});
function getGroups(){
	allGroups = {};
	for(subcomitteeName in cachedData.Subcomittees){
		subcomittee = cachedData.Subcomittees[subcomitteeName]
		groups= [];
		for(groupName in subcomittee.Groups){
			groups.push(groupName);
		}
		allGroups[subcomitteeName] = groups;
	}
	return allGroups;
}

function getPerformances(){
	performances = []
	subcomitteeDict = getGroups()
	for(subcomitteeName in subcomitteeDict){
		for(group in subcomitteeDict[subcomitteeName]){
			group = subcomitteeDict[subcomitteeName][group]
			//console.log("Subcomittee:"+subcomitteeName+" and Group:"+group)
			performanceDetails = cachedData.Subcomittees[subcomitteeName].Groups[group]["Performance Details"]
			performance = {}
			performance.Group = group
			performance.Description = performanceDetails.Description
			performance.Title = performanceDetails["Performance title"]
			performance.Cost = performanceDetails["Cost of tickets"]
			performance["Family friendly?"] = performanceDetails["Family friendly?"]
			performance.Data = performanceDetails["Date (mm/dd/yyyy)"]
			performance.Location = performanceDetails["Location (as seen in sheet tag)"]
			if(performance["Date"]!="" && performance["Location"]!=""){
				performances.push(performance)
			}
		}
	}
	return performances
}
function getGroupInfo(subcomittee, groupname, password){
	subcomittees = cachedData.Subcomittees;
	SubComitteeData = subcomittees[subcomittee]
	GroupData = SubComitteeData.Groups[groupname]
	if(password != GroupData["Performance Details"]["PAC App password"]){
		return "Incorrect Password"
	}
	Deadlines = cachedData.Deadlines.concat(SubComitteeData.Deadlines)
	Announcements = cachedData.Announcements.concat(SubComitteeData.Announcements.concat(GroupData.Announcements))
	Demerits = GroupData.Demerits
	Persons = GroupData.Persons
	//console.log(GroupData)
	Details = GroupData["Performance Details"]
	SpaceName = Details["Location (as seen in sheet tag)"]
	if(SpaceName != ""){
		//console.log(SpaceName)
		Space = cachedData.Spaces[SpaceName]
		//console.log(Space)
		Announcements = Announcements.concat(Space.Announcements)
		Deadlines = Deadlines.concat(Space.Deadlines)
	}
	ResultData = {}
	ResultData.Deadlines = Deadlines
	ResultData.Announcements = Announcements
	ResultData.Demerits = Demerits
	ResultData.Persons = Persons
	ResultData.Details = Details
	return ResultData
}
app.get("/getPerformances", (req,res)=>{
	performanceList = JSON.stringify(getPerformances())
	res.end(performanceList)
})
app.get("/getInfo", (req, res)=>{
	subcomittee = req.query.Subcomittee
	groupname = req.query.Group
	password = req.query.Password
	infoList = JSON.stringify(getGroupInfo(subcomittee, groupname, password))
	res.end(infoList)
})
app.get("/getGroups", (req,res)=>{
	allGroupsString = JSON.stringify(getGroups())
	res.end(allGroupsString)
})

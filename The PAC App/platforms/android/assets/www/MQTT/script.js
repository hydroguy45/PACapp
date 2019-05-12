// Create a client instance
client = new Paho.MQTT.Client("broker.mqttdashboard.com", 8000, String(Date.now()));

// set callback handlers
client.onConnectionLost = onConnectionLost;
client.onMessageArrived = onMessageArrived;

// connect the client
client.connect({onSuccess:onConnect});

// called when the client connects
function onConnect() {
  // Once a connection has been made, make a subscription and send a message.
  console.log("onConnect");
  client.subscribe("c541-urf-beat");
}

function sendMsg() {
  message = new Paho.MQTT.Message("Hello");
  message.destinationName = "urffer-channel-CIS441";
  client.send(message);
}

function sendRandNum() {
  message = new Paho.MQTT.Message(String(Math.random()));
  message.destinationName = "urffer-channel-CIS441";
  client.send(message);
}

// called when the client loses its connection
function onConnectionLost(responseObject) {
  if (responseObject.errorCode !== 0) {
    console.log("onConnectionLost:" + responseObject.errorMessage);
  }
}

// called when a message arrives
function onMessageArrived(message) {
	if (message.destinationName === "c541-urf-beat") {
		var splitted = message.payloadString.split("-");
		if (splitted[2].localeCompare("N") === 0) {
			window.numNatural++;
			addData(splitted[0], parseInt(splitted[1]), true);
		} else {
			window.numArtificial++;
			addData(splitted[0], parseInt(splitted[1]), false);
		}
		if (Date.now() - window.pastMillisec > 20000) {
			if (numNatural + numArtificial < 14) {
				console.log("Beating too slow");
				$("#tooSlow").show();
			} else {
				$("#tooSlow").hide();
			}
				
			if (numNatural + numArtificial > 16) {
				console.log("BEATING TOO FAST");
				$("#tooFast").show();
			} else {
				$("#tooFast").hide();
			}
				
			if (numNatural + numArtificial <= 16 &&
				numNatural + numArtificial >= 14) {
				console.log("Beating normally");
				$("#normalSpeed").show();
			} else {
				$("#normalSpeed").hide();
			}
			
			window.pastMillisec = Date.now();
			window.numArtificial = 0;
			window.numNatural = 0;
		}
	} else {
		console.log("Message source not recognised");
	}
	
	//console.log("onMessageArrived:" + message.payloadString);
}

// create the graph
function createGraph() {
	var config = {
		type: 'line',
		data: {
			labels: [],
			datasets: [
			{
				label: 'Delay since previous beat',
				backgroundColor: window.chartColors.red,
				borderColor: window.chartColors.red,
				data: [],
				fill: false,
				lineTension: 0.1,
			},{
				label: '60-second moving average delay',
				backgroundColor: window.chartColors.blue,
				borderColor: window.chartColors.blue,
				data: [],
				fill: false,
			},{
				label: 'Delay cap (hysterisis v. non-hysterisis)',
				backgroundColor: window.chartColors.yellow,
				borderColor: window.chartColors.yellow,
				data: [],
				fill: false,
				lineTension: 0.1,
			}]
		},
		options: {
			responsive: true,
			title: {
				display: true,
				text: 'Chart.js Line Chart'
			},
			tooltips: {
				mode: 'index',
				intersect: false,
			},
			hover: {
				mode: 'nearest',
				intersect: true
			},
			scales: {
				xAxes: [{
					display: true,
					scaleLabel: {
						display: true,
						labelString: 'Beat number'
					}
				}],
				yAxes: [{
					display: true,
					scaleLabel: {
						display: true,
						labelString: 'moving average delay'
					}
				}]
			}
		}
	};

	window.onload = function() {
		var ctx = document.getElementById('canvas').getContext('2d');
		window.myLine = new Chart(ctx, config);
		window.gConfig = config;
		window.numNatural = 0;
		window.numArtificial = 0;
		window.pastMillisec = 0;
	};
}

function addData(label, value, natural) {
	// add the most recent label
	window.gConfig.data.labels.push(label);
	
	// remove the oldest label, delay, and delay cap
	if (window.gConfig.data.labels.length > 60) {
		window.gConfig.data.labels.shift();
		window.gConfig.data.datasets[0].data.shift();
		window.gConfig.data.datasets[2].data.shift();
	}
	
	// add the most recent delay value
	window.gConfig.data.datasets[0].data.push(value);
	if (natural) {
		window.gConfig.data.datasets[2].data.push(1500);
	} else {
		window.gConfig.data.datasets[2].data.push(1090);
	}
	
	// remove the oldest average delay value
	if (window.gConfig.data.datasets[1].data.length > 60) {
		window.gConfig.data.datasets[1].data.shift();
	}
    var numMovingAvgVals = 60;
	if (window.gConfig.data.datasets[0].data.length > numMovingAvgVals){
        // add the most recent moving average value
        var lastElem = window.gConfig.data.datasets[0].data.length-1;
        var movingAvgVal = window.gConfig.data.datasets[1].data[lastElem-1];
        var removing = window.gConfig.data.datasets[0].data[lastElem-numMovingAvgVals];
        var delta =  (value - removing) / (numMovingAvgVals);
        movingAvgVal += delta;
        console.log("Removing (i="+lastElem+"): "+removing);
        console.log("Adding : "+value);
        console.log("Delta : "+delta);
        console.log("New Avg (len "+numMovingAvgVals+"): "+movingAvgVal);
        window.gConfig.data.datasets[1].data.push(movingAvgVal);
	} else {
        //For the first 60 seconds it is an actual average calculation, before it becomes a moving average calculation.
        var mySum = window.gConfig.data.datasets[0].data.reduce((prev, cur)=> cur += prev)
        var myAvg = mySum/window.gConfig.data.datasets[0].data.length;
        window.gConfig.data.datasets[1].data.push(myAvg);
    }
	
	// update the graph
	window.myLine.update();
}
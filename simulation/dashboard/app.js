const express = require('express')
const path = require('path');
const expressWs = require('express-ws')
const NATS = require('nats');

const app = express()

expressWs(app)

// Serve static files from the React app
app.use(express.static(path.join(__dirname, 'build')));

const connections = new Set()

var argv = require('minimist')(process.argv.slice(2));

var nats_user = ''
var nats_password = ''
var nats_host = 'host.docker.internal'
var nats_port = 4222
var api_port = 8080

if (argv.u) {
  nats_user = argv.u.replace(/\s+/g, '').replace(/\n+/g, '').replace(/\r+/g, '').replace(/\t+/g, '');
}
if (argv.p) {
  nats_password = argv.p.replace(/\s+/g, '').replace(/\n+/g, '').replace(/\r+/g, '').replace(/\t+/g, '');
}
if (argv.s) {
  nats_host = argv.s.replace(/\s+/g, '').replace(/\n+/g, '').replace(/\r+/g, '').replace(/\t+/g, '');
}
if (argv.t) {
  api_port = parseInt(argv.t.replace(/\s+/g, '').replace(/\n+/g, '').replace(/\r+/g, '').replace(/\t+/g, ''));
}

var connection_string = "nats://"

if (nats_user) {
  connection_string = connection_string + nats_user + ':' + nats_password + '@'
}

connection_string = connection_string + nats_host + ':' + nats_port

console.log('Connecting to NATS server: ' + connection_string)

const nc = NATS.connect(connection_string);


const wsHandler = (ws) => {
  connections.add(ws)
  console.log("Connected client")

  ws.on('close', () => {
    connections.delete(ws);
  })
}

function callback(msg, reply, subject, sid) {
  let parsed = {msg: JSON.parse(msg), subject: subject}
  connections.forEach(function each(client) {
    console.log(parsed);
    client.send(JSON.stringify(parsed));
  });
}

const channels = ["simulation.timestep", "state", "graphics.sat", "graphics.doc", "graphics.grstn", "graphics.iot", "graphics.sat2sat", "graphics.grstn2sat", "received.temperature", "received.soil_water_content", "received.fertilization", "received.battery_percentage", "groundstation.packets_received"]

channels.forEach( (topic) => nc.subscribe(topic, callback));


app.ws('/api/streaming', wsHandler)
app.listen(api_port)

/* eslint-disable no-console */
const commands = require('./commands');
const https = require('https');
const apiOptions = {
    host: "https://2j1tyo67g5.execute-api.ap-southeast-2.amazonaws.com",
    port: 80,
    path: '/default/aoes-request-handler?method=get',
    method: 'POST'
  };

// API can get commands waiting on the server, and clear the most recent one once it's executed. 
let scriptRunning = false;

function main() {
  listen();
}

main();

function listen(){
  
  if (scriptRunning){
    return;
  }
  console.log("Listening...");
  
  https.get('https://2j1tyo67g5.execute-api.ap-southeast-2.amazonaws.com/default/aoes-request-handler?method=get', (resp) => {
    let data = '';
  
    // A chunk of data has been recieved.
    resp.on('data', (chunk) => {
      data += chunk;
    });
        // The whole response has been received. Print out the result.
    resp.on('end', () => {
      try{
  
        data = JSON.parse(data);
        handleCommand(data.command.toLowerCase());
      } catch(e){
        console.log("Error: Could not parse API command" + data);
      }
    });
  
  }).on("error", (err) => {
    console.log("Error: " + err.message);
    listen();
  }); 
}

async function clear(){
  https.get('https://2j1tyo67g5.execute-api.ap-southeast-2.amazonaws.com/default/aoes-request-handler?method=clear', (resp) => {
    let data = '';
  
    // A chunk of data has been recieved.
    resp.on('data', (chunk) => {
      data += chunk;
    });
        // The whole response has been received. Print out the result.
    resp.on('end', () => {
      try{
  
        console.log("Cleared command " + data);
      } catch(e){
        console.log("Error: Could not parse API command" + data);
      }
      
      listen();
    });
  
  }).on("error", (err) => {
    console.log("Error: " + err.message);
  });
}

async function handleCommand(newCommand){
  
  if (newCommand.length > 0){
    scriptRunning = true;
    console.log("Executing: " + newCommand);
    await commands.runCommands([newCommand]);
    console.log("Request complete! Clearing queue.");
    clear();
    scriptRunning = false;
  } else {
    listen();
  }
  
}


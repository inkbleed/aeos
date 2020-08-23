/* eslint-disable no-console */
const commands = require('./commands');

const prompts = require('prompts');
 
 
function home(){
  
  var choices = createChoices();
  
  (async () => {
    const response = await prompts({
      type: 'autocomplete',
      name: 'mycommand',
      message: 'Select your command:',
      choices: choices,
      fallback: "Create new"
    });
    
    // Null is returned if an existing command is not selected. 
      
    if (response.mycommand != "Quit"){
      
      // Check if arguments required
      let mysweetasscommand = response.mycommand;
      
      if (response.mycommand.indexOf("${") > 0){
        let params = parseCommand(response.mycommand);
        let answers = await populateParams(params);
        
        //construct the command:
        
        mysweetasscommand = "";
        
        for (let i = 0; i < params.length; i++){
          if (params[i].substr(0,2) == "${"){
            mysweetasscommand += ((mysweetasscommand.substr(mysweetasscommand.length - 1) != " ") ? " " + answers[params[i]] : answers[params[i]]);
          } else {
            mysweetasscommand += (mysweetasscommand.length > 0) ? " " + params[i] : params[i];
          } 
        }
      }
      await commands.runCommands([mysweetasscommand]);
      
      home();
    } else {
      console.log("Smell you later!");
      process.exit(); 
    }
    
  })();
}

async function populateParams(choices){
  // If you're running a command w/ parameters, this asks the values from the user
  let qs = [];
  
  for (let i = 0; i < choices.length; i++){
    if (choices[i].substr(0,2) == "${"){
      qs.push({
        type:"text",
        name:choices[i],
        message:choices[i]
        });
    }
  }
  
  return await (async () => {
    return await prompts(qs);
  })();
}

function createChoices(){
  // Takes all the commands, and uses this to generate autocomplete choices for the user to select commands
  let myChoices = [];
  
  for (var cmd in commands.allCommands){
    
    myChoices.push({title:commands.allCommands[cmd].commandFormat});
  }
  
  myChoices.push({title:"Quit"})
  return myChoices;
}

function parseCommand(cmd){
  // This function finds the arguments within the command, and splits it up into "text" and argument sections. 
  
  let myArgs = [];
  let lastPos = 0;
  var breaker = 0;
  
  for (var i = 0; i < cmd.length; i++){
    
    let pos = cmd.indexOf("${",i);
    let end = cmd.indexOf("}",i) + 1;
    
    if (pos < 0){
      myArgs.push(cmd.substr(i));
      i = cmd.length;
    } else {
      
      if (cmd.substr(i,pos - i).length > 0) {myArgs.push(cmd.substr(i,pos - i))};
      myArgs.push(cmd.substr(pos,end - pos));
      
      i = end;
    }
    
    breaker++
    
    if (breaker>20){
      i = 5000;
    }
  }
  
  return myArgs;
  
}

function main() {
  let inputCommands = ["open browser"];
  commands.runCommands(inputCommands);
}

home();

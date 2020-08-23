var fs = require("fs");
const notifier = require('node-notifier');
const controls = require('./controls');

// these can be accessed by commands with the format ${foo}
// command arguments are added to this dictionary during execution
let vars = {
  'browser': 'chrome'
}

const controlCommands = [
  {
    "commandFormat": "click",
    "type": "function",
    "function": controls.click
  },
  {
    "commandFormat": "doubleclick",
    "type": "function",
    "function": controls.doubleclick
  },
  {
    "commandFormat": "rightclick",
    "type": "function",
    "function": controls.doubleclick
  },
  {
    "commandFormat": "echo ${text}",
    "type": "function",
    "function": controls.echo
  },
  {
    "commandFormat": "press ${key}",
    "type": "function",
    "function": controls.keyTap
  },
  {
    "commandFormat": "press ${modifier1} ${modifier2} ${key}",
    "type": "function",
    "function": controls.keyTapWithModifiers
  },
  {
    "commandFormat": "press ${modifier} ${key}",
    "type": "function",
    "function": controls.keyTapWithModifier
  },
  {
    "commandFormat": "move mouse ${x} ${y}",
    "type": "function",
    "function": controls.moveMouse
  },
  {
    "commandFormat": "do a sine wave",
    "type": "function",
    "function": controls.doASineWave
  },
  {
    "commandFormat": "move to ${item}",
    "type": "function",
    "function": controls.moveToItem
  },
  {
    "commandFormat": "scroll mousewheel ${y}",
    "type": "function",
    "function": controls.scrollMouseWheel
  },
  {
    "commandFormat": "wait ${seconds} until ${item} is visible",
    "type": "function",
    "function": controls.waitForVisible
  },
  {
    "commandFormat": "pause ${seconds} seconds",
    "type": "function",
    "function": controls.pause
  },
  {
    "commandFormat": "type ${text}",
    "type": "function",
    "function": controls.type
  },
  {
    "commandFormat": "if ${statement} then ${action}",
    "type": "function",
    "function": controls.ifthen
  }
  
]


function getUserCommands(args) {
  return JSON.parse(fs.readFileSync("./commands/default.json")).commands;
}

function addVarsIntoCommand(input) {
    var argsRegex = /\$\{(\w+)\}/g
    var args = input.match(argsRegex);
    if (!args) return input;
    return args.reduce((result, arg) => {
      result = result.replace(arg, vars[arg.slice(2,-1)]);
      return result;
    }, input);
}

function findCommand(input) {
  input = addVarsIntoCommand(input);
  
  let results = allCommands.reduce((results, command) => {
    if (input === command.commandFormat) {
      results.push({
        command: command,
        args: {},
      });
      return results;
    }

    // var valRegexString = command.commandFormat.replace(/\$\{\w+\}/g, '(.+)');
    var valRegexString = command.commandFormat.replace(/\$\{\w+\}/g, '(".+"|[\\S]+)');
    var valRegex = new RegExp('^'+valRegexString+'$');
    var vals = input.match(valRegex);
    if (!vals) return results;
    var argsRegex = /\$\{(\w+)\}/g
    var argsMatch = command.commandFormat.match(argsRegex);
    if (!argsMatch) return results;
    var args = argsMatch.map(arg => arg.slice(2,-1));

    let argMap = args.reduce((result, val, i) => {
      result[val] = vals[i+1];
      return result;
    }, {});

    results.push({
      command: command,
      args: argMap,
    });
    return results;
  }, []);

  switch(results.length) {
    case 1:
      return {
        success: true,
        command: results[0].command,
        args: results[0].args,
      }
    case 0:
      console.log(`Command not found: "${input}"`);
      return {
        success: false,
      }
    default:
      // TODO allow prompt specify command
      console.log(`Multiple matches for: "${input}"`);
      return {
        success: false,
      }
  }
}

async function runCommands(commands) {
  if (!commands || !commands.length) return;

  let input = commands[0];
  
  if (typeof input != "object"){
    // Only run text parsing on standard 
    let result = findCommand(input);
    if (!result.success) return;
    let runresult = "tmp";
    
    command = result.command;
    args = result.args;
    vars = {...vars, ...args};
    if (!command.type) command.type = "command"
  } else {
    command = input;
    command.type = "flow";
  }

  
  switch(command.type) {
    case "function":
      runresult = await command.function(args);
      break;
    case "command":
      // If you don't do this, then as it runs, it deletes elements from allCommands, so no command can run more than once! 
      // This is due to how js handles assigning functions to variables, it passes a reference rather than making a copy. 
      let tmpActions = [].concat(command.actions);
      
      runresult = await runCommands(tmpActions);
      break;
    case "flow":
      runresult = await runFlowCommands(command);
      break;
  }
  
  if (runresult){
    commands.shift();
    await runCommands(commands);
  } else {
    console.log("Failed: " + input);
  }
  
  return runresult; // Pass successes/failures back up
}

async function runFlowCommands(command){
  // This takes in an object, with its own set of conditions + actions, which are then run as a new set of commands. 
  let flowcommands = [];
  if (command.repeat){
    // Options: You can repeat based on rows within a file, or you can repeat a certain number of times. 
    
    if (command.file){
      try{        
        require('fs').readFileSync(command.file, 'utf-8').split(/\r?\n/).forEach(function(line){
          console.log(line);
          for (var i = 0; i < command.actions.length; i++){
            
            flowcommands.push(setVarInActions(command.actions[i], "${file-data}", line));
            
          }         
        });
        
      } catch(e){
        console.log("Unable to read file: " + e);
      }
    } else {
    
      for (var i = 0; i < command.repeat; i++){
        flowcommands.push(...command.actions);
      }
    }
  } else if (command.try){
    flowcommands.push(...command.try);
  }
  
  // Run your new array of actions!
  let runresult = await runCommands(flowcommands);
  
  if ((!runresult) && (command.catch)){
    // If you try some commands but it fails, try to 
    console.log("Caught error, trying other commands: ") + JSON.stringify(command.catch);
    flowcommands = [];
    flowcommands.push(...command.catch);
    runresult = await runCommands(flowcommands);
  }
  
  return runresult;  
}

function setVarInActions(actions, varname, newvalue){
  // If you are doing a repeat/loop based on filenames, you need to populate all actions with the correct filename for that loop. 
  // Problem is, actions can be strings, arrays of strings, or objects (containing arrays of strings!) depending on whether 
  // you're using flowcontrol or not. So this function takes a set of actions and just populates the new value (i.e. filename) 
  // regardless of object type. 
  
  if (typeof actions == "string"){
    return actions.replace(varname, newvalue);
  } else if (Array.isArray(actions)){
    
    let newactions = [];
    for (var i = 0; i < actions.length; i++){
      newactions.push(setVarInActions(actions[i], varname, newvalue));
    }
    
    return newactions;
  } else if (typeof actions === "object"){
    // This means we're dealing with a flow control object and need to return that!
    
    let newactions = {};
    
    if (actions.actions){
      
      newactions.actions = setVarInActions(actions.actions, varname, newvalue);
    }
    
    if (actions.try) {
      newactions.try = setVarInActions(actions.try, varname, newvalue);
    }
    
    if (actions.catch) {
      newactions.catch = setVarInActions(actions.catch, varname, newvalue);
    }
    
    return newactions;
    
  }
  
}

let allCommands = controlCommands.concat(getUserCommands());

module.exports = {
  runCommands: runCommands,
  allCommands: allCommands
}

var robot = require("robotjs");
const image = require('./image');
const notifier = require('node-notifier');

async function echo(args) {
  console.log(args.text.replace(/^"(.*)"$/, '$1'));
  return true;
}

async function click(args) {
  robot.mouseClick();
  return true;
}

async function doubleclick(args) {
  robot.mouseClick("left",true);
  return true;
}

async function rightclick(args) {
  robot.mouseClick("right");
  return true;
}

async function keyTap(args) {
  try {
    robot.keyTap(args.key);
  } catch {
    console.log(`Invalid key: ${args.key}`);
  }
  return true;
}

async function keyTapWithModifier(args) {
  try {
    robot.keyTap(args.key, args.modifier);
  } catch {
    console.log(`Invalid key or modifier. Key: ${args.key}, modifier: ${args.modifier}`);
  }
  return true;
}

async function keyTapWithModifiers(args) {
  //Same as above, but w/ 2 modifiers
  try {
    robot.keyTap(args.key, [args.modifier1, args.modifier2]);
  } catch {
    console.log(`Invalid key or modifier. Key: ${args.key}, modifiers: ${args.modifier1} , ${args.modifier2}`);
  }
  return true;
}

async function moveMouse(args) {
  robot.moveMouse(args.x, args.y);
  return true;
}

function doASineWave(args) {
  robot.setMouseDelay(2);

  var twoPI = Math.PI * 2.0;
  var screenSize = robot.getScreenSize();
  var height = (screenSize.height / 2) - 10;
  var width = screenSize.width;

  for (var x = 0; x < width; x++)
  {
    y = height * Math.sin((twoPI * x) / width) + height;
    robot.moveMouse(x, y);
  }
  return true;
}

async function moveToItem(args) {
  
  let match = await image.locateOnScreen(args.item);
  
  if ((match) && (!match.err)){ 
    // By default, click in the center of the image
    await robot.moveMouse((match.loc.x + (match.img.width / 2)), (match.loc.y +  (match.img.height / 2)));
    return true;
  } else {
    notify("Failed to move to item - can't find " + args.item + "!");
    console.log("Could not find " + args.item + "!");
    return false;
  }
  
}

async function waitForVisible (args) {
  
  let time = args.seconds;
  let counter = 0;
   
  return new Promise((resolve, reject) => {const timer = setInterval(async function(){
  
    let match = await image.locateOnScreen(args.item);
    console.log("Trying to find " + args.item + " - attempt " + counter);
    if ((match) && (!match.err)){
      console.log("Found " + args.item);
      clearInterval(timer);
      resolve(true);
      return true;
    } else if ((match) && (match.err)){
      console.log("Failed: " + JSON.stringify(match));
      clearInterval(timer);
      resolve(false);
    }
    
    if (counter++ > time * 2){
      clearInterval(timer);
      notify("Waited " + time + " seconds, and couldn't find " + args.item);
      console.log("Waited " + time + " seconds, and couldn't find " + args.item);
      resolve(false);
    }
    
  }, 500)});
    
}

function type(args) {
  robot.typeString(args.text);
  return true;
}

async function scrollMouseWheel(args) {
  robot.scrollMouse(0,parseInt(args.y));
  return true;
}


async function pause(args) {
  const sleep = (milliseconds) => {
    return new Promise(resolve => setTimeout(resolve, milliseconds))
  }
  
  const waitMe = async () => {
    await sleep((parseInt(args.seconds) * 1000));
  }

  await waitMe();
  return true;
  
}

function notify(message){
  notifier.notify({
    title: "Aeos",
    message: message,
    icon: 'gir.png', // Absolute Path to Triggering Icon
    timeout: 1, // Takes precedence over wait if both are defined.
  });
}

module.exports = {
  click: click,
  doubleclick: doubleclick,
  rightclick:rightclick,
  echo: echo,
  keyTap: keyTap,
  keyTapWithModifier: keyTapWithModifier,
  keyTapWithModifiers: keyTapWithModifiers,
  moveMouse: moveMouse,
  doASineWave: doASineWave,
  type: type,
  moveToItem: moveToItem,
  waitForVisible: waitForVisible,
  scrollMouseWheel: scrollMouseWheel,
  pause: pause
};

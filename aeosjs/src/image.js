/* eslint-disable no-console */


// Move the mouse across the screen as a sine wave.
const robot = require("robotjs");
const fs = require("fs");
const cv = require('opencv4nodejs');
const notifier = require('node-notifier');

var dir = __dirname.split("\\");
dir.pop();
const imgDir = dir.join("/") + "/img/";

if (!fs.existsSync(imgDir)){
    //Create the directory if it doesn't already exist
    fs.mkdirSync(imgDir);
}
if (!fs.existsSync(imgDir + "/tmp/")){
    //Create the directory if it doesn't already exist
    fs.mkdirSync(imgDir + "/tmp/");
}

var localImages = []; // List of all searchable images in the image director

// Get a list of all images before you start, so it knows which ones are present or not. 
fs.readdirSync(imgDir).forEach(file => {
    localImages.push(file);
});


function captureImage(){
  // Was hoping to turn this into an in-app 'screen cap' tool, however opencv4node doesn't support clicking/dragging on the image windows
  // so no luck D: 
  let tmpScreen = robot.screen.capture();
  let screen = img2mat(tmpScreen.image, tmpScreen.width, tmpScreen.height);
  
  cv.imshow('Capture', screen);
  cv.waitKey();
}

async function locateOnScreen(imgName){
    
  if (!localImages.includes(imgName)){
    
    notify("Can't find " + imgName + "! Please add it then try again.");
    console.log("Can't find " + imgName + "! Please add it then try again.");
    return {err: 666};
  }
  let found = null;
  // Each image name is a folder, containing a suite of potentially matching images
  images = await fs.readdirSync(imgDir + imgName);
  await asyncForEach(images, async (img) => {
    if (found) return false; //Can't find a clean way to cancel the async for loop!
    
    let result = await templateMatch(imgName, img);
    
    if (result.minMax.maxVal > .8) {
      found = {loc: result.minMax.maxLoc, img: result.img};
      return false;
    }
  }).catch(function(e){
    notify("Find " + imgName + " failed: " + e);
    console.log("Failed! Error: " + e);
    return {err: e};
  });
  
  return found;
  
}

async function templateMatch(imgName, file){
  
  // This should be fixed so you take 1 screencap for every file you check, not one for each!
  let tmpScreen = robot.screen.capture();
  let screen = img2mat(tmpScreen.image, tmpScreen.width, tmpScreen.height);
  /* OK this is dumb as fuck, but I can't get the format of robot.screen to match the file that's read, without saving/opening the screen capture. */
  cv.imwrite(imgDir + "tmp/screen-match.jpg", screen); 
  screen = await cv.imreadAsync(imgDir + "tmp/screen-match.jpg")
 
  let searchImg = await cv.imreadAsync(imgDir + imgName + "/" + file);
    
  const matched = searchImg.matchTemplate(screen, 5);
  
  const minMax = matched.minMaxLoc();
  const { maxLoc: { x, y } } = minMax;
  
  const imsize =  {height: searchImg.rows, width: searchImg.cols};
  
  return {minMax: minMax, img: imsize};
}

function img2mat(img, width, height){

    return new cv.Mat(img,height,width,cv.CV_8UC4);
}

async function asyncForEach(array, callback) {
  for (let index = 0; index < array.length; index++) {
    await callback(array[index], index, array);
  }
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
  locateOnScreen: locateOnScreen
}

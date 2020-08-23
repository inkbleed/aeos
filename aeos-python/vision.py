import cv2
import numpy as np
from PIL import ImageGrab

USING_TESSERACT = True
try:
    import pytesseract
    from PIL import Image
except (ImportError, RuntimeError):
    USING_TESSERACT = False

# only used to visualise what Aeos is seeing - can remove later
USING_MATPLOT = False
if USING_MATPLOT:
    try:
        import matplotlib.pyplot as plt
    except (ImportError, RuntimeError):
        print('Error: Unable to import matplotlib, disabling these features')
        USING_MATPLOT = False

class RelativeOffset:
    TOP = 0
    LEFT = 0
    CENTER = 0.5
    BOTTOM = 1
    RIGHT = 1

    DEFAULTS = (CENTER, CENTER)

    offset_map = {
        '$TOP_LEFT': (LEFT, TOP),
        '$TOP': (CENTER, TOP),
        '$TOP_RIGHT': (RIGHT, TOP),
        '$LEFT': (LEFT, CENTER),
        '$CENTER': (CENTER, CENTER),
        '$RIGHT': (RIGHT, CENTER),
        '$BOTTOM_LEFT': (LEFT, BOTTOM),
        '$BOTTOM': (CENTER, BOTTOM),
        '$BOTTOM_RIGHT': (RIGHT, BOTTOM)
    }


def locate(image_path, offsets=RelativeOffset.DEFAULTS, required_confidence=0.7, retina=False):
    location, confidence, width, height = locate_templatematch(image_path)
    if (confidence < required_confidence):
        #print("Detecting features!")
        #results = self.locate_featuredetect(image_path)
        #if len(results) is not None:
        #    location, confidence
        #    location_x,location_y = location
        #else:
        return None
    if retina:
        location = location[0] / 2, location[1] / 2
        width /= 2
        height /= 2
    location_x = location[0] + (width * offsets[0])
    location_y = location[1] + (height * offsets[1])
    return location_x, location_y

def locate_templatematch(image_path):
    screenimg = ImageGrab.grab()
    
    screenimg = screenimg.convert('RGB')
    screenimg = np.array(screenimg)
    
    img_gray = cv2.cvtColor(screenimg, cv2.COLOR_RGB2GRAY)
    template = cv2.imread(image_path)
    template_gray = cv2.cvtColor(template, cv2.COLOR_RGBA2GRAY)

    if template is None:
        return

    result = cv2.matchTemplate(img_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(result)

    if maxLoc is None:
        return False
    else:
        print(maxLoc, maxVal)
        height, width = template.shape[:2]
        return maxLoc, maxVal, width, height

def locate_featuredetect(image_path):
    # Other visino types to include:
    # https://www.learnopencv.com/blob-detection-using-opencv-python-c/
    # https://pythonprogramming.net/canny-edge-detection-gradients-python-opencv-tutorial/
    # http://coding-robin.de/2013/07/22/train-your-own-opencv-haar-classifier.html
    screenimg = ImageGrab.grab()
    screenimg = np.array(screenimg)
    img_gray = cv2.cvtColor(screenimg, cv2.COLOR_RGB2GRAY)
    template = cv2.imread(image_path)

    template_gray = cv2.cvtColor(template, cv2.COLOR_RGBA2GRAY)
    if template is None:
        return

    orb = cv2.ORB_create()

    kp1, des1 = orb.detectAndCompute(template_gray,None)
    kp2, des2 = orb.detectAndCompute(img_gray,None)

    print(kp2)
    print(des2)

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    matches = bf.match(des1,des2)
    matches = sorted(matches, key = lambda x:x.distance)

    if not matches:
        return

    img3 = cv2.drawMatches(template_gray,kp1,img_gray,kp2,matches[:10],None, flags=2)

    if USING_MATPLOT:
        plt.imshow(img3)
        plt.show()

    return (kp2[matches[0].queryIdx].pt, matches[0].distance)

def image_to_text(image_path):
    if USING_TESSERACT:
        return pytesseract.image_to_string(Image.open(image_path))
    else:
        return None

def get_screen():
    # This function grabs/returns the current screen. Used to determine if the any user input is happening.
    
    try:
        screen = ImageGrab.grab()
    except:
        screen = None
    
    return screen
    
def compare_images(img1, img2):
    # Used for detecting if the screen has been updated - compares two images and returns similarity
    if img1 is None:
        return
    if img2 is None:
        return
    
    img1 = img1.convert('RGB')
    img1 = np.array(img1)
    img1 = cv2.cvtColor(img1, cv2.COLOR_RGB2GRAY)
    img2 = img2.convert('RGB')
    img2 = np.array(img2)
    img2 = cv2.cvtColor(img2, cv2.COLOR_RGBA2GRAY)

    result = cv2.matchTemplate(img1, img2, cv2.TM_CCOEFF_NORMED)
    (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(result)

    if maxLoc is None:
        return False
    else:
        return maxVal

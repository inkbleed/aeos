import clipboard
import os
import pyautogui    #controls mouse/keyboard (not awesome with the keyboard though)
import re
import smtplib

import subprocess   #This executes commandline processes
import time         #gets system time

from pynput import keyboard     #used for capturing keypresses/controlling mouse/keyboard

import vision
import database

class Controller:
    user_variables = {
        'REQ_CONFIDENCE': 0.7
    }

    def __init__(self):
        pyautogui.FAILSAFE = False
        self._controls = [
            ('click', self.click),
            ('copy image', self.copy_image),
            ('right click', self.click_right),
            ('double click', self.double_click),
            ('drag (-?\d+) (-?\d.+)', self.drag),
            ('drag to (\d+) (\d+)', self.drag_to),
            ('drag from (.+) to (.+)', self.drag_from),
            ('echo (.+)', self.echo),
            ('hotkey (.+)', self.hotkey),
            ('find (.+)', self.move_to_image),
            ('move to (.+) of (.+)', self.move_relative_to_image),
            ('extract (.+) from (.+)', self.extract_from_string),
            ('press (.+)', self.press),
            ('prompt (.+)', self.prompt),
            ('read', self.read),
            ('say (.+)', self.say),
            ('scroll (-?\d+)', self.scroll),
            ('set (.+) = (.+)', self.set_variable),
            ('sql (.+)', self.sql_execute),
            ('stop', self.stop_plan),
            ('store (.+) in clipboard', self.store_in_clipboard),
            ('hscroll (-?\d+)', self.horizontal_scroll),
            ('move cursor (.+) (.+)', self.move_cursor),
            ('\$ (.+)', self.subprocess),
            ('teleport (.+) (.+)', self.teleport),
            ('type (.+)', self.typewrite),
			('wait (\d+) seconds for (.+)', self.wait_for_image),
            ('wait (\d+)', self.wait),
        ]

    def get_controls(self):
        return self._controls

    def stop_plan(self, args):
        print('Stopped plan')
        return False

    def click(self, args):
        pyautogui.click()
        return True

    def click_right(self, args):
        pyautogui.click(button='right')
        return True

    def copy_image(self, args):
        return self.capture_image('tmp')

    def capture_image(self, image_name):
        print('Not implemented for your OS')
        return False

    def echo(self, args):
        print(args[0])
        return True

    def extract_from_string(self, args):
        matches = re.findall(args[0], args[1])
        if len(matches) > 0:
            self.user_variables['RESULT'] = matches[0]
            return True
        else:
            return False

    def double_click(self, args):
        pyautogui.doubleClick()
        return True

    def drag(self, args):
        pyautogui.dragRel(int(args[0]), int(args[1]), button='left')
        return True

    def drag_to(self, args):
        pyautogui.dragTo(int(args[0]), int(args[1]), button='left')
        return True

    def drag_from(self, args):
        loc1 = self.locate_image(args[0])
        if loc1 is None:
            return False
        
        loc2 = self.locate_image(args[1])
        if loc2 is None:
            return False
            
        self.move_cursor([loc1[0], loc1[1]])
        
        pyautogui.dragTo(loc2[0], loc2[1], button='left')
        
        return True
        
    def move_to_image(self, args):
        location = self.locate_image(args[0])
        if location is None:
            self.say("Unabled to find " + args[0])
            return False
        return self.move_cursor([location[0], location[1]])

    def read(self, args):
        if not self.capture_image('tmp', False):
            return None
        image_path = self._get_img_filepath('tmp')
        text = vision.image_to_text(image_path)
        if text is None:
            self.user_variables['TEXT'] = ''
            return False
        else:
            self.user_variables['TEXT'] = text
            self.echo(['Predicted text: ' + text])
            return True

    def move_relative_to_image(self, args):
        location = self.locate_image(args[1], args[0])
        if location is None:
            return False
        return self.move_cursor([location[0], location[1]])

    def hotkey(self, args):
        keys = args[0].split()
        if len(keys) == 2:
            pyautogui.hotkey(keys[0], keys[1])
        elif len(keys) == 3:
            pyautogui.hotkey(keys[0], keys[1], keys[2])
        return True

    def press(self, args):
        pyautogui.press(args[0])
        return True

    def say(self, args):
        print( 'Not implemented for your OS')
        return False

    def set_variable(self, args):
        if len(args) == 2:
            self.user_variables[args[0].upper()] = args[1]
            return True
        else:
            return False
    
    def sql_execute(self, args):
        print("Saved results to : " + (database.display_sql_html(args[0])))
        return True
    
    def store_in_clipboard(self, args):
        clipboard.copy(args[0])
        return True

    def subprocess(self, args):
        subprocess.run(args[0], shell=True)
        return True

    def move_cursor(self, args):
        pyautogui.moveTo(int(args[0]), int(args[1]), 1, pyautogui.easeInOutQuad)
        return True

    def scroll(self, args):
        pyautogui.scroll(int(args[0]))
        return True

    def horizontal_scroll(self, args):
        pyautogui.hscroll(int(args[0]))
        return True

    def teleport(self, args):
        pyautogui.moveTo(int(args[0]), int(args[1]))
        return True

    def typewrite(self, args):
        pyautogui.typewrite(args[0])
        return True

    def prompt(self, args):
        pyautogui.prompt(text=str(args[0]), title='Aeos')
        return True

    def wait(self, args):
        time.sleep(int(args[0]))
        return True

    def wait_for_image(self, args):
        timeout = int(args[0])
        images = args[1].split(" OR ");

        while timeout > 0:
            for image in images:
                location = self.locate_image(image)
                if location is not None:
                    return True
            self.wait([1])
            timeout = timeout - 1
        
        self.say("Could not find " + args[1])

    def locate_image(self, image_name, offset_arg=None):
        image_path = self._get_img_filepath(image_name)
        if not os.path.exists(image_path):
            if not self.capture_image(image_name):
                return None
        if offset_arg is None:
            offsets = vision.RelativeOffset.DEFAULTS
        else:
            if offset_arg in vision.RelativeOffset.offset_map:
                offsets = vision.RelativeOffset.offset_map[offset_arg]
            else:
                print('Please select either: '+' ,'.join(list(vision.RelativeOffset.offset_map.keys())))
                return None
        isScreenRetina = 'RETINA' in self.user_variables and self.user_variables['RETINA'] == "true"
        location = vision.locate(image_path, offsets, float(self.user_variables['REQ_CONFIDENCE']), isScreenRetina)
        if location is not None:
            self.user_variables['LOCATION_X'] = int(location[0])
            self.user_variables['LOCATION_Y'] = int(location[1])
        return location

    def _get_img_filepath(self, img):
        return self.IMG_DIR.replace('$IMG', img)

class MacController(Controller):
    IMG_DIR = 'img/$IMG.jpg'

    def capture_image(self, image_name, prompt=True):
        if prompt:
            self.echo(['can you show me what ' + image_name + ' looks like?'])
        cmd = ['screencapture', '-s', '-x', self._get_img_filepath(image_name)]
        completed_process = subprocess.run(cmd)
        return False if completed_process.returncode else True

    def say(self, args):
        cmd = ['say', '-v', 'Kate']
        cmd.extend(args[0].split())
        subprocess.run(cmd)
        return True

class LinuxController(Controller):
    def say(self, args):
        cmd = ['say']
        cmd.extend(args[0].split())
        subprocess.run(cmd)
        return True

class WindowsController(Controller):
    IMG_DIR = 'img\\$IMG.png'

    def capture_image(self, image_name=None, prompt=True):
        
        if image_name is not None:
            if prompt:
                self.echo(['can you show me what ' + image_name + ' looks like?'])
                self.echo(['Press F12 to take a screenshot, or esc to cancel.'])
            
        if image_name is None:
            image_name = pyautogui.prompt(text="What is the name of this image?", title='Aeos')
        
        cmd = ['plugins\\Minicap\\Minicap.exe', '-save', self._get_img_filepath(image_name), '-captureregselect', '-exit']
        
        #Start polling for keypresses
        def on_press(key):
            
            global hotkeys
    
            try:
                if key == keyboard.Key.f12:
                    completed_process = subprocess.run(cmd, shell=True)
                    return False
                    
            except AttributeError:
                print('Oh shit an error!')
                print(cmd)
                print(AttributeError)
				
        def on_release(key):
        
            if key == keyboard.Key.esc:
                print("No longer polling for screenshots!")
                return False
                
        # Collect events until released
        with keyboard.Listener(
                on_press=on_press,
                on_release=on_release) as listener:
            hotkeys = 0
            listener.join()
        
        return True
        
    def subprocess(self, args):
        cmd = args[0]
        subprocess.run(cmd, shell=True)
        return True

    def say(self, args):
        print(args[0])
        return True

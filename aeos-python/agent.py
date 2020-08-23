import action
import config
import threading
import sys

import time
import vision

import re

class State:
    IDLE = 1
    NP_CREATE_YN = 2
    NP_FORMAT = 3
    NP_ADD_ACTION = 4
    #This status is used so the idler knows if Aeos is executing a script or not
    EXECUTING = 5
    #This state is for when Aeos is waiting for users to take a screenshot
    WAIT_IMAGE_CAPTURE = 6
    #This status is used so the idler knows if Aeos is trying to close itself
    CLOSING = 999

UNKNOWN_COMMAND = "UNKNOWN_COMMAND"

class Agent:
    actions = {}
    new_plans = []
    state = State.IDLE

    input_for_new_plan = ''

    def __init__(self, store):
        self._store = store
        self._global_commands = {
            'help': self._help,
            'cancel': self._cancel,
            'reload actions': self._reload_actions
        }
        self._state_commands = {
            State.IDLE: {
                "new command": self._create_new_command,
                UNKNOWN_COMMAND: self._search_for_command
            },
            State.EXECUTING: {
                "new command": self._create_new_command,
                UNKNOWN_COMMAND: self._search_for_command
            },
            State.NP_CREATE_YN: {
                "y": self._new_plan_yes_response,
                "yes": self._new_plan_yes_response,
                "n": self._new_plan_no_response,
                "no": self._new_plan_no_response,
                UNKNOWN_COMMAND: self._new_plan_unknown_response
            },
            State.NP_FORMAT: {
                UNKNOWN_COMMAND: self._new_plan_format
            },
            State.NP_ADD_ACTION: {
                "done": self._new_plan_done,
                UNKNOWN_COMMAND: self._new_plan_add_action
            }
        }

    def handle_input(self, command):
        # This function takes user input, then executes it if it's a global or state command
        # or otherwise attempts to run the command using search_for_command
        if command in self._global_commands:
            return self._global_commands[command](command)
        elif command in self._state_commands[self.state]:
            return self._state_commands[self.state][command](command)
        else:
            return self._state_commands[self.state][UNKNOWN_COMMAND](command)

    def _cancel(self, command):
        self.set_idle()
        self.new_plans = []

    def _help(self, command):
        print('List of valid commands:')
        commands = sorted([item.form for sublist in self._store.actions.values() for item in sublist])
        print('  '+'\n  '.join(commands))
        print('------------')

    def _reload_actions(self, command):
        self._store.load_all_actions()

    def _create_new_command(self, command):
        self.state = State.NP_FORMAT
        return 'What will the format of the new command be?'

    def _search_for_command(self, command):
        # This function finds then executes any command it's given
        
        valid_actions = self._store.find_valid_actions(command)
        
        # If you're unable to find a command:
        if len(valid_actions) == 0:
            self.state = State.NP_CREATE_YN
            return 'Unrecognised command. Would you like to create a new one?'
        elif len(valid_actions) == 1:
            # If we find a valid action to execute:
            
            self.state = State.EXECUTING            
            
            if valid_actions[0][0].run(valid_actions[0][1]):
                #This is called when you run out of tasks

                #return None
                self.set_idle()
                return "Task complete."
            else:
                self.set_idle()
                return 'Could not complete command: "$CMD" - stuck on "$STEP"'.replace('$CMD', command).replace("$STEP",str(valid_actions[0][0].form) + " " + str(valid_actions[0][1]))
        else:
            # TODO: handle multiple valid options
            return 'Multiple valid options for command: "$CMD"'.replace('$CMD', command)
            self.set_idle()
            
    def _new_plan_yes_response(self, command):
        self.state = State.NP_FORMAT
        return 'What will the format of this command be?'

    def _new_plan_no_response(self, command):
        if len(self.new_plans) == 0:
            self.set_idle()
            return None
        else:
            if self.state == State.NP_CREATE_YN:
                self.state = State.NP_ADD_ACTION
            else:
                self.state = State.FC_ADD_ACTION
            return 'What action should I perform next then?'

    def _new_plan_unknown_response(self, command):
        return 'Please select either yes or no'

    def _new_plan_format(self, command):
        command = command.replace('??', '(.+)')
        new_plan = action.Plan(command)
        self.new_plans.append(new_plan)
        self.state = State.NP_ADD_ACTION
        return 'What action should I perform first?'

    def _new_plan_add_action(self, command):
        cur_plan = self.new_plans[-1]
        valid_actions = self._store.find_valid_actions(command)
        if len(valid_actions) == 0:
            self.state = State.NP_CREATE_YN
            self.input_for_new_plan = command
            return 'Unrecognised command. Would you like to add this command at the same time?'
        elif len(valid_actions) == 1:
            cur_plan.add_to_plan(valid_actions[0][0], valid_actions[0][1], command)
            return 'What action should I perform next?'
        else:
            self.set_idle()
            return 'Error: multiple valid options for command: "$CMD"'.replace('$CMD', command)

    def _new_plan_done(self, command):
        cur_plan = self.new_plans[-1]
        cur_plan.save_to_file()
        self._store.add_action(cur_plan)
        self.new_plans.pop()
        if len(self.new_plans) == 0:
            self.set_idle()
            return 'New command learnt. What else can I help you with?'
        else:
            cur_plan = self.new_plans[-1]
            command = self.input_for_new_plan
            valid_actions = self._store.find_valid_actions(command)
            if len(valid_actions) == 0:
                return 'The format of this new command does not match your last input. To add this command use the format ' + cur_plan.form + '.'
            elif len(valid_actions) == 1:
                cur_plan.add_to_plan(valid_actions[0][0], valid_actions[0][1], command)
                return 'New command learnt. What action should i perform next?'
            else:
                self.set_idle()
                return 'Error: multiple valid options for command: "$CMD"'.replace('$CMD', command)

    def idler(self):
        # This function automatically starts running anything set as an "Idle" task
        print("Computer is currently idle. Commencing chores.")
        
        for i in range(0,5):
            # We want to check every second whether the system is still in idle state or not.
            if not self.state == State.IDLE:
                return

            time.sleep(1)
        
        print("Commencing Idle actions")
        print(str(threading.enumerate()))
        
        
        response = self.handle_input("idler")
        if response:
            print(response)
        
        # Set the system to idle, and return to try to close the thread.
        self.state = State.IDLE
        
        sys.stdout.write("> ")
        return
    
    def detect_idle(self):
        # Detecting whether the machine is idle, based on screencap differences.
        # When triggered, it takes a screenshot. 
       
        old_screencap = vision.get_screen()

        # First, make sure the app actually is in an idle state, by making sure the 
        # screen hasn't really changed for 5 minutes.
        
        i = 0
        SECS_TIL_IDLE = 86400
        
        while i < SECS_TIL_IDLE:
            # We want to check every second whether the system is still in idle state or not.
            if not self.state == State.IDLE:
                return
                
            #We also need to check if the main thread has ended or not! 
                        
            bNonIdleThread = False
            
            for t in threading.enumerate():
                if t.getName() != "Idler" and t.is_alive():
                    bNonIdleThread = True
            
            if bNonIdleThread == False or threading.activeCount() == 1:
                # The idle thread is the only thing currently running! Close the app
                return
                sys.exit
            else:
                # If the main thread is still open, and the current state is still State.IDLE, then we should 
                # make sure the screen hasn't been updated yet...
                                
                try:
                    new_screencap = vision.get_screen()
                    screencap_delta = vision.compare_images(old_screencap, new_screencap)
                
                    #From trial and error, minor changes fall within the boundary of .999 similarity.
                
                    if screencap_delta is None:
                        screencap_delta = 0

                    if screencap_delta > .999:
                            i += 1
                    else:
                        #The screen is moving, so take a new screenshot, and start the clock again.
                        old_screencap = vision.get_screen()
                        i = 0
                except:
                    print("Caught error when capturing screen for idler!")
                    
            time.sleep(1)
            
        try:
            new_screencap = vision.get_screen()
            screencap_delta = vision.compare_images(old_screencap, new_screencap)
            
        except:
            print("Caught error when capturing screen for idler!")
            screencap_delta = .999
            i -= 1
            
        #Make sure you're a) still idle, and b) screencap show no real difference, before executing idler
        if screencap_delta > .99 and self.state == State.IDLE:
            self.idler()
            return
            
        elif self.state == State.IDLE:
            
            # We're in an idle state, but the screen's still moving! Call itself again.
            self.detect_idle()
            
            # Once the detect_idles' bottom out, we close the thread.
            return
        else:
            # We're no longer in an idle state, so stop idling!
            # By returning, we essentially end the current thread we're on.
            return
    
    def set_idle(self):
        # This function is called whenever the app tries to move to an Idle
        # state, so it can try to detect no human interaction on screen, and 
        # trigger its "idle" tasks.
        
        self.state = State.IDLE
        
        #First, make sure we don't already have an idler thread running:
        bIdleThread = False
        
        main_thread = threading.currentThread()
        for t in threading.enumerate():
            if t is main_thread:
                continue
            if t.getName() == "Idler":
                bIdleThread = True
        
        # If we have 0 idle threads running, trigger a new one!
        if bIdleThread == False:
            t1 = threading.Thread(name="Idler",target=self.detect_idle, args=[])
            t1.start()
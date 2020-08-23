import clipboard
import datetime
import re

import config
import vision

class Action(object):
    def __init__(self, form):
        self.form = form

    def run(self):
        pass

class CoreAction(Action):
    def __init__(self, form, func_ptr, controller):
        self.func_ptr = func_ptr
        self._controller = controller
        Action.__init__(self, form)

    def run(self, args):
        return self.func_ptr(self._update_args(args))

    def _update_args(self, args):
        new_args = []
        for arg in args:
            now = datetime.datetime.now()
            arg = arg.replace("$DATETIME", now.strftime("%Y%m%d%H%M"))
            arg = arg.replace("$HOUR", now.strftime("%H"))
            arg = arg.replace("$YEAR", now.strftime("%Y"))
            arg = arg.replace("$MONTH", now.strftime("%m"))
            arg = arg.replace("$DAY", now.strftime("%d"))
            arg = arg.replace("$MINUTE", now.strftime("%M"))
            arg = arg.replace("$CLIPBOARD", clipboard.paste())

            for key, value in self._controller.user_variables.items():
                arg = arg.replace("$"+key, str(value))

            new_args.append(arg)
        
        return new_args

class Plan(Action):
    def __init__(self, form):
        self.action_list = []
        Action.__init__(self, form)

    def add_to_plan(self, new_action, args, command):
        self.action_list.append((new_action, args, command))

    def run(self, plan_args):
        for cur_action in self.action_list:
            action_args = self._update_action_args(cur_action[1], plan_args)
            if not cur_action[0].run(action_args):
                return False
        return True

    def _update_action_args(self, action_args, plan_args):
        new_args = []
        for arg in action_args:
            matches = re.findall(r'(\$(\d+))', arg)
            for match in matches:
                arg = arg.replace(match[0], plan_args[int(match[1])])
            new_args.append(arg)
        return new_args

    def save_to_file(self):
        with open('./scripts/custom.as', 'a') as f:
            f.write('\n' + self.form + ':')
            for action in self.action_list:
                f.write('\n    ' + action[2])
            f.write('\n')


class FlowControlFactory:
    class FlowControl(Plan):
        def __init__(self, controller):
            Plan.__init__(self, self._format)
            self._controller = controller

    class IfVisible(FlowControl):
        # Note: This function can't handle being nested, if you use $0, $1 etc as a parameter on the lower nests.
        # I.e. "If webpage is visible: if $0 is visible: say Hi" will check for webpage twice, not $0.
        # The workaround for the above function is:
        # "set thingy = $0; if webpage is visible: if $THINGY is visible: say Hi". 
        # Made a fix so that the above workaround works, however wasn't able to figure out fixing it "properly". 
        # IfNotVisible is obviously the same.
        
        
        _format = 'if (.+) is visible'
        def run(self, args):
            args = CoreAction._update_args(self,args)
            location = self._controller.locate_image(args[0])
            return FlowControlFactory.FlowControl.run(self, args) if location is not None else True

    class IfNotVisible(FlowControl):
        _format = 'if (.+) is not visible'
        def run(self, args):
            args = CoreAction._update_args(self,args)
            location = self._controller.locate_image(args[0])
            return FlowControlFactory.FlowControl.run(self, args) if location is None else True

    class RepeatTimes(FlowControl):
        _format = 'repeat (\d+) times'
        def run(self, args):
            times = 0
            while times < int(args[0]):
                if FlowControlFactory.FlowControl.run(self, args) == False:
                    return False
                times += 1
            return True
    
    class RepeatFromFile(FlowControl):
        
        #This loops through a file, running a set of commands on each line, and passing the variable "STRLINE" which contains each row of the file.
        #Basically so you can have, say, a list of files to be updated, and it loops through that file
        
        _format = 'repeat this on file (.+)'
        
        def run(self, args):
            
            args = CoreAction._update_args(self,args)
            
            with open(args[0],'r') as f:
                for x in f:
                    x = x.rstrip()
                    if not x:
                        continue
                    else:
                        self._controller.user_variables["STRLINE"] = x
                        if FlowControlFactory.FlowControl.run(self, args) == False:
                            return False
            
            return True
    
    class WhileVisible(FlowControl):
        _format = 'while (.+) is visible'
        def run(self, args):
            location = self._controller.locate_image(args[0])
            while location is not None:
                if FlowControlFactory.FlowControl.run(self, args) == False:
                    return False
                location = self._controller.locate_image(args[0])
            return True

    class WhileNotVisible(FlowControl):
        _format = 'while (.+) is not visible'
        def run(self, args):
            location = self._controller.locate_image(args[0])
            while location is None:
                if FlowControlFactory.FlowControl.run(self, args) == False:
                    return False
                location = self._controller.locate_image(args[0])
            return True

    flow_control_objects = {
        'RepeatTimes': RepeatTimes,
        'RepeatFromFile':RepeatFromFile,
        'IfVisible': IfVisible,
        'IfNotVisible': IfNotVisible,
        'WhileVisible': WhileVisible,
        'WhileNotVisible': WhileNotVisible
    }

    def __init__(self, controller):
        self._controller = controller

    def create(self, command):
        for fc in FlowControlFactory.FlowControl.__subclasses__():
            match = re.match('^'+fc._format+':$', command)
            if match:
                return FlowControlFactory.flow_control_objects[fc.__name__](self._controller), match.groups()


class ActionStore:
    def __init__(self, controller):
        self._controller = controller
        self.load_all_actions()

    def load_all_actions(self):
        self.actions = {}
        self._load_core_actions(self._controller.get_controls())
        self._flow_control_factory = FlowControlFactory(self._controller)
        config.load_actions_from_file(self)

    def _load_core_actions(self, controls):
        for control in controls:
            new_action = CoreAction(control[0], control[1], self._controller)
            self.add_action(new_action)

    def add_action(self, new_action):
        first_word = new_action.form.split(' ', 1)[0]
        if first_word in self.actions:
            self.actions[first_word].append(new_action)
        else:
            self.actions[first_word] = [new_action]

    def find_flow_control(self, command):
        return self._flow_control_factory.create(command)

    def find_valid_actions(self, command):
        first_word = re.escape(command.split(' ', 1)[0])
        if first_word not in self.actions:
            return []
        matches = []
        closest_matches = self.actions[first_word]
        for closest_match in closest_matches:
            match = re.match('^'+closest_match.form+'$', command)
            if match:
                matches.append((closest_match, match.groups()))
        return matches

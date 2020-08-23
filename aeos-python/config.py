import action
import re

def load_actions_from_file(store, script='custom'):
    scripts = []
    _load_script(script, store, scripts)

def _load_script(script, store, scripts):
    scripts.append(script)
    filename = './scripts/' + script + '.as'
    with open(filename) as f:
        content = f.readlines()
        indents = 0
        plan_stack = []
        for lineno, line in enumerate(content):
            if skip_line(line):
                continue
            line = line.rstrip()

            # handle imports
            import_regex = '^import (\w+)$'
            match = re.match(import_regex, line.strip())
            if match:
                if len(plan_stack) != 0:
                    invalid_config(filename, lineno+1, 'Imports must be declared at the top of the file')
                next_script = match.groups()[0]
                if next_script in scripts:
                    continue
                _load_script(next_script, store, scripts)
                continue

            # check indentation
            line_indent = compare_indents(line, indents)
            if line_indent is None:
                invalid_config(filename, lineno+1, 'Bad indentation')
            while line_indent < 0:
                indents -= 1
                last_action, args, command = plan_stack.pop()
                if len(plan_stack) == 0:
                    store.add_action(last_action)
                else:
                    plan_stack[-1][0].add_to_plan(last_action, args, command)
                line_indent += 1
            line = line.strip()

            # handle new plan
            if indents == 0:
                new_plan_regex = '^(\w.+):$'
                match = re.match(new_plan_regex, line)
                if match:
                    new_plan_format = match.groups()[0]
                    plan_stack.append((action.Plan(new_plan_format), [], new_plan_format))
                    indents = 1
                    continue
                else:
                    invalid_config(filename, lineno+1, 'Bad syntax - did you miss a semicolon?')

            # handle flow controls
            flow_control = store.find_flow_control(line)
            if flow_control is not None:
                plan_stack.append((flow_control[0], flow_control[1], line))
                indents += 1
                continue

            # handle actions
            valid_actions = store.find_valid_actions(line)
            if len(valid_actions) == 0:
                invalid_config(filename, lineno+1, 'Unrecognised action')
            elif len(valid_actions) > 1:
                invalid_config(filename, lineno+1, 'Multiple matching actions')
            else:
                plan_stack[-1][0].add_to_plan(valid_actions[0][0], valid_actions[0][1], line)
                continue

    while indents > 0:
        last_action, args, command = plan_stack.pop()
        if len(plan_stack) == 0:
            store.add_action(last_action)
        else:
            plan_stack[-1][0].add_to_plan(last_action, args, command)
        indents -= 1
    return True

def compare_indents(line, indents):
    leading_spaces = len(line) - len(line.lstrip())
    if leading_spaces % 4 != 0 or (leading_spaces / 4) > indents:
        return None
    return (leading_spaces / 4) - indents

def skip_line(line):
    return True if line.strip() == '' or line.strip()[0] == '#' else False

def invalid_config(filename, lineno, err_msg):
    msg = 'Invalid config: $MSG ($FILE:$LINE)'.replace(
        '$MSG', err_msg).replace(
        '$FILE', filename).replace(
        '$LINE', str(lineno))
    print(msg)
    exit()

import action
import agent
import controller

import json
import platform
import sys
import atexit

from flask import Flask, request, Response
APP = Flask(__name__)

def get_data(data):
    json_data = json.loads(data)
    print("Received: {}".format(data))
    return json_data

@APP.route("/")
def hello():
    ret = {}
    ret['code'] = 0
    ret['message'] = 'success'
    return json.dumps(ret)

@APP.route("/api/run", methods=["POST"])
def run_command():
    global AGENT

    json_data = get_data(request.data)
    print("Running command: {}".format(json_data['command']))

    response = AGENT.handle_input(json_data['command'])
    if response:
        print(response)

    result = {'code': 0, 'command': json_data['command'], 'response': response}
    return Response(result, mimetype="application/json")

def main():
    global AGENT
    atexit.register(shutdown)

    if platform.system() == 'Darwin':
        c = controller.MacController()
    elif platform.system() == 'Linux':
        c = controller.LinuxController()
    elif platform.system() == 'Windows':
        c = controller.WindowsController()
    else:
        print('Operating system not supported')
        exit()
    store = action.ActionStore(c)
    AGENT = agent.Agent(store)

    response = AGENT.handle_input('startup')
    if response:
        print(response)

    APP.run(debug=False)

def shutdown():
    global AGENT

    #If the ui is actually "quit", we need to update the state of the Aeos to Closing, so threads stop themselves.:
    AGENT.state = 6
    print("Shutting down...")

main()

import platform
import sys

import action
import agent
import controller

def main():
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
    a = agent.Agent(store)
    ui = 'startup'
    print('aeos v1.0')
    print('Type \'help\' to list all available commands.')

    while ui != 'quit' and ui != 'q':
        response = a.handle_input(ui)
        if response:
            print(response)
        sys.stdout.write("> ")
        ui = input()

    #If the ui is actually "quit", we need to update the state of the Aeos to Closing, so threads stop themselves.:
    a.state = 6

if __name__ == "__main__":
    main()

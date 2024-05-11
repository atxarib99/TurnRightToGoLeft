import sys
import os
import ac
import acsys
import directkeys
import time

appName = "popUpAirBrake"

#car states
brake = 0
gas = 0
lights = False

#options
active = False 

#UI components
active_switch = None

lights_key=0x4C # l on keyboard


def log_to_file(msg):
    ac.log(appName + ": " + str(msg))

def log_to_console(msg):
    ac.console(appName + ": " + str(msg))

def log(msg):
    ac.log(appName + ": " + str(msg))
    ac.console(appName + ": " + str(msg))


def acMain(ac_version):
    global active_switch, active
    appWindow = ac.newApp(appName)
    ac.setSize(appWindow, 100, 100)
    log("SEM SEM SEM SEM")

    active_switch = ac.addCheckBox(appWindow, "Active")
    ac.setPosition(active_switch, 5, 50)
    ac.setSize(active_switch, 25, 25)
    ac.addOnCheckBoxChanged(active_switch, onActiveClicked)

    #get last state
    try:
        filename = os.path.join(os.path.dirname(__file__), 'options.dat')
        fh = open(filename, 'r')
        active = int(fh.readline().rstrip())
        fh.close()
        if active:
            ac.setValue(active_switch, 1)
    except:
        log("No file found.")

    #run after every acUpdate, after every data point comes in
    ac.addRenderCallback(appWindow, onFormRender)

    return appName

def acUpdate(deltaT):
    global brake, gas, lights
    brake = ac.getCarState(0, acsys.CS.Brake)
    gas = ac.getCarState(0, acsys.CS.Gas)
    
    if lights:
        if gas > .95 and brake < 0.01:
            setLights(False)
    else:
        if brake > .25 and gas < 0.01:
            setLights(True)

def onFormRender(deltaT):
    pass


def onActiveClicked(checkBoxName, selected):
    global active

    #apply to active var
    active = (selected == 1)
    log(active)

    #write state to file
    filename = os.path.join(os.path.dirname(__file__), 'options.dat')
    fh = open(filename, 'w+')
    fh.write(str(selected))
    fh.close()

def setLights(val):
    global lights
    if active:
        lights = val
        directkeys.PressKey(lights_key)
        time.sleep(0.001)
        directkeys.ReleaseKey(lights_key)

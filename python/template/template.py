import sys
import ac
import acsys

appName = "template"


def log_to_file(msg):
    ac.log(appName + ": " + str(msg))

def log_to_console(msg):
    ac.console(appName + ": " + str(msg))

def log(msg):
    ac.log(appName + ": " + str(msg))
    ac.console(appName + ": " + str(msg))

def acMain(ac_version):
    appWindow = ac.newApp(appName)
    ac.setSize(appWindow, 100, 100)
    log("SEM SEM SEM SEM")
   
    #run after every acUpdate, after every data point comes in
    ac.addRenderCallback(appWindow, onFormRender)

    return appName

def acUpdate(deltaT):
    pass
    
def onFormRender(deltaT):
    pass


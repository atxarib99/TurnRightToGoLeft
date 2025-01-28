import sys
import ac
import acsys

appName = "button_box"
buttons = []
phys_buttons = []

def log_to_file(msg):
    ac.log(appName + ": " + str(msg))

def log_to_console(msg):
    ac.console(appName + ": " + str(msg))

def log(msg):
    ac.log(appName + ": " + str(msg))
    ac.console(appName + ": " + str(msg))

def load_config():
    global buttons
    # with open("C:\\Program Files (x86)\\Steam\\steamapps\\common\\assettocorsa\\apps\\python\\button_box\\buttons.config", "r") as config:
    with open("apps/python/button_box/buttons.config", "r") as config:
        for line in config.readlines():
            if line[0] == "#":
                continue
            if line.strip() == "":
                continue
            split = line.split("|")
            buttons.append((split[0], split[1]))


def dynamic_callback(cnt):
    if cnt == 0:
        return simple_callback_1
    if cnt == 1:
        return simple_callback_2
    if cnt == 2:
        return simple_callback_3
    if cnt == 3:
        return simple_callback_4
    if cnt == 4:
        return simple_callback_5



def acMain(ac_version):
    global phys_buttons
    appWindow = ac.newApp(appName)

    load_config()
    
    ac.setSize(appWindow, 20 + 50*len(buttons), 100)
    log("SEM SEM SEM SEM")

    cnt = 0
    log(str(len(buttons)))
    for button in buttons:
        log("1")
        button_iden = ac.addButton(appWindow, button[0])
        log(str(button_iden))
        log("2")
        succ = ac.addOnClickedListener(button_iden, dynamic_callback(cnt))
        log(str(succ))
        log("3")
        ac.setSize(button_iden, 50, 50)
        log("4")
        ac.setPosition(button_iden, 50*cnt+10, 40)
        cnt += 1
   
    #run after every acUpdate, after every data point comes in
    ac.addRenderCallback(appWindow, onFormRender)

    return appName


def on_press(key):
    log(key)

def acUpdate(deltaT):
    pass
    
def onFormRender(deltaT):
    pass


#please ignore this cringe, idk why its like this, but let me out

def simple_callback_1(v1,v2):
    log("button1 pressed")
    ac.sendChatMessage(buttons[0][1])

def simple_callback_2(v1,v2):
    log("button2 pressed")
    ac.sendChatMessage(buttons[1][1])
    
def simple_callback_3(v1,v2):
    log("button3 pressed")
    ac.sendChatMessage(buttons[2][1])
def simple_callback_4(v1,v2):
    log("button4 pressed")
    ac.sendChatMessage(buttons[3][1])

def simple_callback_5(v1,v2):
    log("button5 pressed")
    ac.sendChatMessage(buttons[4][1])
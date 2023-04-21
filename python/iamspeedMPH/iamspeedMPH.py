import sys
import ac
import acsys

appName = "iamspeedMPH"

#labels
min_speed_label = 0
cur_speed_label = 0
max_speed_label = 0
min_speed_label_head = 0
cur_speed_label_head = 0
max_speed_label_head = 0


#data
brake = 0
gas = 0
speed = 5
min_speed = 0
cur_speed = 0
max_speed = 0
gas_flat_start = 0

def log_to_file(msg):
    ac.log(appName + ": " + str(msg))

def log_to_console(msg):
    ac.console(appName + ": " + str(msg))

def log(msg):
    ac.log(appName + ": " + str(msg))
    ac.console(appName + ": " + str(msg))

def acMain(ac_version):
    global min_speed_label, cur_speed_label, max_speed_label
    appWindow = ac.newApp(appName)
    ac.setSize(appWindow, 410, 125)
    log("SEM SEM SEM SEM")
   

    #displays
    min_speed_label = ac.addLabel(appWindow, "min")
    cur_speed_label = ac.addLabel(appWindow, "cur")
    max_speed_label = ac.addLabel(appWindow, "max")
    min_speed_label_head = ac.addLabel(appWindow, "min")
    cur_speed_label_head = ac.addLabel(appWindow, "cur")
    max_speed_label_head = ac.addLabel(appWindow, "max")
    

    ac.addRenderCallback(appWindow, onFormRender)


    #set positions and size
    ac.setPosition(min_speed_label, 0, 50)
    ac.setPosition(cur_speed_label, 150, 50)
    ac.setPosition(max_speed_label, 300, 50)
    ac.setPosition(min_speed_label_head, 0, 40)
    ac.setPosition(cur_speed_label_head, 150, 40)
    ac.setPosition(max_speed_label_head, 300, 40)
    ac.setFontAlignment(min_speed_label, "center")
    ac.setFontAlignment(cur_speed_label, "center")
    ac.setFontAlignment(max_speed_label, "center")
    ac.setFontAlignment(min_speed_label_head, "center")
    ac.setFontAlignment(cur_speed_label_head, "center")
    ac.setFontAlignment(max_speed_label_head, "center")
    ac.setFontSize(min_speed_label, 40)
    ac.setFontSize(cur_speed_label, 40)
    ac.setFontSize(max_speed_label, 40)
    ac.setSize(min_speed_label, 100, 100)
    ac.setSize(cur_speed_label, 100, 100)
    ac.setSize(max_speed_label, 100, 100)
    ac.setSize(min_speed_label_head, 100, 25)
    ac.setSize(cur_speed_label_head, 100, 25)
    ac.setSize(max_speed_label_head, 100, 25)
    

    return appName

def acUpdate(deltaT):
    global brake, gas, speed, min_speed, cur_speed, max_speed
    #get brake
    brake = ac.getCarState(0, acsys.CS.Brake)
    #get throttle
    gas = ac.getCarState(0, acsys.CS.Gas)
    #get speed(s)
    speed = ac.getCarState(0, acsys.CS.SpeedMPH)

    #first set current speed
    cur_speed = speed

    #if brakes are being pressed, always sync min speed to current speed
    #or if the speed has lowered due to coast
    if brake > 0 or cur_speed < min_speed:
        min_speed = cur_speed
    
    #if throttle is flat for longer than 2 seconds, sync maxspeed to cur speed
    # or if speed has somehow increased
    if gas == 1 or cur_speed > max_speed:
        max_speed = cur_speed
    


def onFormRender(deltaT):
    global min_speed_label, cur_speed_label, max_speed_label
    ac.setText(min_speed_label, str(int(min_speed)))
    ac.setText(cur_speed_label, str(int(cur_speed)))
    ac.setText(max_speed_label, str(int(max_speed)))
    
    #need to draw boxes around stuff to max it look nice
    x, y = 5, 35
    w, h = 100, 80
    t = 1
    ac.glColor3f(1,0,0)
    ac.glQuad(x,y,w,t)
    ac.glQuad(x,y,t,h)
    ac.glQuad(x+w,y,t,h)
    ac.glQuad(x,y+h,w,t)
    
    #shift by 150?
    x+=145
    ac.glQuad(x,y,w,t)
    ac.glQuad(x,y,t,h)
    ac.glQuad(x+w,y,t,h)
    ac.glQuad(x,y+h,w,t)

    x+=150
    ac.glQuad(x,y,w,t)
    ac.glQuad(x,y,t,h)
    ac.glQuad(x+w,y,t,h)
    ac.glQuad(x,y+h,w,t)

    
    

    
    

    

import sys
import ac
import acsys
import os
import platform

if platform.architecture()[0] == "64bit":
    libdir = 'third_party/lib64'
else:
    libdir = 'third_party/lib'
sys.path.insert(0, os.path.join(os.path.dirname(__file__), libdir))
os.environ['PATH'] = os.environ['PATH'] + ";."

from third_party.sim_info import SimInfo

appName = "slipometer"

#text labels
label_slip_ratio_FL = None
label_slip_ratio_FR = None
label_slip_ratio_RL = None
label_slip_ratio_RR = None

#window size settings
size_mult = 1.0
window_height = 200*size_mult
window_width = 100 * size_mult

#height 0-(.5*height) front boxes
#height (.5*height)-(1.0*heihgt) rear boxes

#width 0-(.5*width) left boxes
#width (.5*width)-(1.0*width) right boxes

#car data
slip_ratio_FL = 0.0
slip_ratio_FR = 0.0
slip_ratio_RL = 0.0
slip_ratio_RR = 0.0
tc_setting = 1
abs_setting = 1


def log_to_file(msg):
    ac.log(appName + ": " + str(msg))

def log_to_console(msg):
    ac.console(appName + ": " + str(msg))

def log(msg):
    ac.log(appName + ": " + str(msg))
    ac.console(appName + ": " + str(msg))

def acMain(ac_version):
    global label_slip_ratio_FL, label_slip_ratio_FR, label_slip_ratio_RL, label_slip_ratio_RR
    appWindow = ac.newApp(appName)
    ac.setSize(appWindow, window_width, window_height)
    log("SEM SEM SEM SEM")

    #create lables
    label_slip_ratio_FL = ac.addLabel(appWindow, "fl")
    label_slip_ratio_FR = ac.addLabel(appWindow, "fr")
    label_slip_ratio_RL = ac.addLabel(appWindow, "rl")
    label_slip_ratio_RR = ac.addLabel(appWindow, "rr")

    #align text center
    ac.setFontAlignment(label_slip_ratio_FL, "right")
    ac.setFontAlignment(label_slip_ratio_FR, "left")
    ac.setFontAlignment(label_slip_ratio_RL, "right")
    ac.setFontAlignment(label_slip_ratio_RR, "left")

    #positions
    ac.setPosition(label_slip_ratio_FL, .33*window_width, .25*window_height)
    ac.setPosition(label_slip_ratio_FR, .66*window_width, .25*window_height)
    ac.setPosition(label_slip_ratio_RL, .33*window_width, .75*window_height)
    ac.setPosition(label_slip_ratio_RR, .66*window_width, .75*window_height)

   
    #run after every acUpdate, after every data point comes in
    ac.addRenderCallback(appWindow, onFormRender)

    return appName


def draw_box(x, y, width, height):
    """
    Draws a box using the draw() function with the given x, y coordinates,
    width, and height.
    """
    ac.glColor3f(0,1,0)
    ac.glQuad(x, y, width, 1)  # Top edge
    ac.glQuad(x, y + height - 1, width, 1)  # Bottom edge
    ac.glQuad(x, y, 1, height)  # Left edge
    ac.glQuad(x + width - 1, y, 1, height)  # Right edge
    ac.glColor3f(0,0,1)

def acUpdate(deltaT):
    global slip_ratio_FL, slip_ratio_FR, slip_ratio_RL, slip_ratio_RR, tc_setting, abs_setting
    siminfo = SimInfo()

    slip_ratio_FL, slip_ratio_FR, slip_ratio_RL, slip_ratio_RR = ac.getCarState(0, acsys.CS.SlipRatio)
    if abs(slip_ratio_FL) < 0.01:
        slip_ratio_FL = 0
    if abs(slip_ratio_FR) < 0.01:
        slip_ratio_FR = 0
    if abs(slip_ratio_RL) < 0.01:
        slip_ratio_RL = 0
    if abs(slip_ratio_RR) < 0.01:
        slip_ratio_RR = 0

    tc_setting = float(siminfo.physics.tc)
    abs_setting = float(siminfo.physics.abs)


    siminfo.close()


def render_tyre_box(x, y, slip, margin=2):
    """
    Draws a box, and fills it if needed
    """
    draw_box(int(x+margin), int(y+margin), int((.5*window_width)-margin), int((.5*window_height)-margin))
    #need to check if this wheel is slippin
    if tc_setting < slip:
        ac.glColor3f(1,1,1)
        ac.glQuad(int(x+margin), int(y+margin), int((.5*window_width)-margin), int((.5*window_height)-margin))
    elif -1*abs_setting > slip:
        ac.glColor3f(1,1,1)
        ac.glQuad(int(x+margin), int(y+margin), int((.5*window_width)-margin), int((.5*window_height)-margin))
    else:
        if slip > 0:
            #percentage to tc activation
            slip_perc = slip/tc_setting
            if slip_perc > 1:
                slip_perc = 1
            ac.glColor3f(1,0,0)
            ac.glQuad(x+margin, y+(.5*window_height)-(slip_perc*(.5*window_height))+margin, ((.5*window_width)-margin), (slip_perc*(.5*window_height))-margin)
        elif slip < 0:
            slip_perc = (-1*slip)/tc_setting
            if slip_perc > 1:
                slip_perc = 1
            ac.glColor3f(0,0,1)
            ac.glQuad(x+margin, y+margin, (.5*window_width)-margin, slip_perc*(.5*window_height)-margin)


    #if not breakin no limits
    #else:

    #else if negative ELIF IMPORTANT!!
    #height = perc to limit slip/abs_settign
    #glquad(x, top, width, perc of box height)
    #glquad(x, y, width, perc*(.5*height)


    
def onFormRender(deltaT):
    margin = 2

    #draw FL box
    render_tyre_box(0, 0, slip_ratio_FL)
    render_tyre_box((.5*window_width), 0, slip_ratio_FR)
    render_tyre_box(0, (.5*window_height), slip_ratio_RL)
    render_tyre_box((.5*window_width), (.5*window_height), slip_ratio_RR)

    #set labels
    ac.setText(label_slip_ratio_FL, str(round(slip_ratio_FL,2)))
    ac.setText(label_slip_ratio_FR, str(round(slip_ratio_FR,2)))
    ac.setText(label_slip_ratio_RL, str(round(slip_ratio_RL,2)))
    ac.setText(label_slip_ratio_RR, str(round(slip_ratio_RR,2)))


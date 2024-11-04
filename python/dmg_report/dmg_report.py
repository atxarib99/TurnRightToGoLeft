import sys
import ac
import acsys
import platform
import os

appName = "dmg_report"

# Set up library path based on architecture
if platform.architecture()[0] == "64bit":
    libdir = 'third_party/lib64'
else:
    libdir = 'third_party/lib'
sys.path.insert(0, os.path.join(os.path.dirname(__file__), libdir))
os.environ['PATH'] = os.environ['PATH'] + ";."

from third_party.sim_info import SimInfo

# Global variables for labels
label_damage_front = None
label_damage_rear = None
label_damage_left = None
label_damage_right = None
label_damage_center = None
label_repair_time = None  # Label for estimated repair time

# Window size
window_width = 200
window_height = 180

def log_to_file(msg):
    ac.log(appName + ": " + str(msg))

def log_to_console(msg):
    ac.console(appName + ": " + str(msg))

def log(msg):
    ac.log(appName + ": " + str(msg))
    ac.console(appName + ": " + str(msg))

def acMain(ac_version):
    global label_damage_front, label_damage_rear, label_damage_left, label_damage_right, label_damage_center, label_repair_time

    # Create app window
    appWindow = ac.newApp(appName)
    ac.setSize(appWindow, window_width, window_height)
    log("Damage Report Initialized")

    # Create labels for each damage area
    label_damage_front = ac.addLabel(appWindow, "Front Damage: ")
    label_damage_rear = ac.addLabel(appWindow, "Rear Damage: ")
    label_damage_left = ac.addLabel(appWindow, "Left Damage: ")
    label_damage_right = ac.addLabel(appWindow, "Right Damage: ")
    label_damage_center = ac.addLabel(appWindow, "Center Damage: ")
    #label_repair_time = ac.addLabel(appWindow, "Estimated Repair Time: ")  # Label for repair time

    # Position the labels
    ac.setPosition(label_damage_front, 10, 20)
    ac.setPosition(label_damage_rear, 10, 50)
    ac.setPosition(label_damage_left, 10, 80)
    ac.setPosition(label_damage_right, 10, 110)
    ac.setPosition(label_damage_center, 10, 140)
    #ac.setPosition(label_repair_time, 10, 160)  # Position for repair time label

    #run after every acUpdate, after every data point comes in
    ac.addRenderCallback(appWindow, onFormRender)

    return appName

def acUpdate(deltaT):
    global damage_values, repair_time

    # Access SimInfo and get damage data
    siminfo = SimInfo()
    damage_values = [
        siminfo.physics.carDamage[0],  # Front damage
        siminfo.physics.carDamage[1],  # Rear damage
        siminfo.physics.carDamage[2],  # Left damage
        siminfo.physics.carDamage[3],  # Right damage
        siminfo.physics.carDamage[4]   # Center damage
    ]
    siminfo.close()

    # Calculate estimated repair time based on center damage
    # INCORRECT !!! 
    #repair_time = round((damage_values[4] / 10) * 20, 2)  # Every 10% = 20 seconds

def onFormRender(deltaT):
    global damage_values, repair_time

    # Update each damage label with the rounded values
    ac.setText(label_damage_front, "Front Damage: " + str(round(damage_values[0], 2)) + "%")
    ac.setText(label_damage_rear, "Rear Damage: " + str(round(damage_values[1], 2)) + "%")
    ac.setText(label_damage_left, "Left Damage: " + str(round(damage_values[2], 2)) + "%")
    ac.setText(label_damage_right, "Right Damage: " + str(round(damage_values[3], 2)) + "%")
    ac.setText(label_damage_center, "Center Damage: " + str(round(damage_values[4], 2)) + "%")
    #ac.setText(label_repair_time, "Estimated Repair Time: " + str(repair_time) + " seconds")


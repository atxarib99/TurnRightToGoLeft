from re import A
import sys
import ac
import acsys

appName = "State of Kachow"

#labels
last_lap_recharge = 0
bar_kj = 0
this_lap_energy_recharge = 0
this_lap_energy_spent = 0


#raw data 
#current kers charge as a percent
kers_charge_perc = 0 
#current kers input as a percent
kers_input_perc = 0
#ers recovery setting (from setup)
ers_recovery = 0 
#ers delivery setting (from setup
ers_delivery = 0
#MGU-H charge setting
ers_heat_charging = 0
#spent kj this lap
ers_current_kj = -1
#battery max kj
ers_max_kj = 0
#current lap count (used for reset)
lap_count = 0

#calculated data
#last known SoC in KJ
last_charge_kj = -1
#energy spent this lap
energy_spend_kj = 0
#energy recharge this lap
energy_recharge_kj = 0
#last lap energy spent
last_lap_energy_spent = 0
#last lap energy recharge
last_lap_energy_recharge = 0
#calculated charge
kers_charge_kj = 1

cnt = 0


def log_to_file(msg):
    ac.log(appName + ": " + str(msg))

def log_to_console(msg):
    ac.console(appName + ": " + str(msg))

def log(msg):
    ac.log(appName + ": " + str(msg))
    ac.console(appName + ": " + str(msg))

def acMain(ac_version):
    global bar_kj, last_lap_recharge, this_lap_energy_recharge, this_lap_energy_spent
    appWindow = ac.newApp(appName)
    ac.setSize(appWindow, 600, 150)

    #text displays
    last_lap_recharge = ac.addLabel(appWindow, "recharge")
    ac.setPosition(last_lap_recharge, 80, 75)
    bar_kj = ac.addLabel(appWindow, "bar_kj")
    ac.setPosition(bar_kj, 450, 75)
    this_lap_energy_recharge = ac.addLabel(appWindow, )
    
    ac.addRenderCallback(appWindow, onFormRender)

    return appName


def acUpdate(deltaT):
    """
    acUpdate is called when Assetto Corsa has new data available to communicate.
    """
    global kers_charge_perc, kers_input, ers_recovery, ers_delivery, ers_heat_charging, ers_current_kj, ers_max_kj, lap_count, last_lap_energy_spent, last_lap_energy_recharge, energy_recharge_kj, energy_spend_kj, last_charge_kj, cnt, kers_charge_kj

    #get kers_charge
    kers_charge_perc = ac.getCarState(0, acsys.CS.KersCharge)
    #get kers_input
    kers_input = ac.getCarState(0, acsys.CS.KersInput)
    #get ers_recovery
    ers_recovery = ac.getCarState(0, acsys.CS.ERSRecovery)
    #get ers_delivery 
    ers_delivery = ac.getCarState(0, acsys.CS.ERSDelivery)
    #get ers_heat_charging
    ers_heat_charging = ac.getCarState(0, acsys.CS.ERSHeatCharging)
    #get ers_current_kj, set last_kj first
    ers_current_kj = ac.getCarState(0, acsys.CS.ERSCurrentKJ)
    #get ers_max_kj
    #this is in MJ, need to convert
    ers_max_kj = ac.getCarState(0, acsys.CS.ERSMaxJ) / 1000
    #current lap
    #if lap count has changed, update, and reset current lap metrics
    if lap_count != ac.getCarState(0, acsys.CS.LapCount):
        lap_count = ac.getCarState(0, acsys.CS.LapCount)
        last_lap_energy_spent = energy_spend_kj
        last_lap_energy_recharge = energy_recharge_kj
        energy_spend_kj = -1
        energy_recharge_kj = -1

    #calculate charge in kj
    if last_charge_kj != -1:
        last_charge_kj = kers_charge_kj
        kers_charge_kj = kers_charge_perc * ers_max_kj
    else:
        kers_charge_kj = kers_charge_perc * ers_max_kj
        last_charge_kj = kers_charge_kj

    #calculate deltas 
    #if current charge has gone down, we've spent
    if last_charge_kj - kers_charge_kj > 0:
        energy_spend_kj += abs(last_charge_kj - kers_charge_kj)
    else:
        energy_recharge_kj += abs(last_charge_kj - kers_charge_kj)


    #every 100 iterations dump to console
    if cnt >= 100:
        dump()
        cnt = 0
    else:
        cnt+=1

def dump():
    #current kers charge as a percent
    log_to_console("kers_charge_perc: " + str(kers_charge_perc)) 
    #current kers input as a percent
    log_to_console("kers_input_perc: " + str(kers_input_perc))
    #current SoC in kj
    log_to_console("ers_current_kj: " + str(ers_current_kj)) 
    #battery max kj
    log_to_console("ers_max_kj: " + str(ers_max_kj))
    #current lap count (used for reset)
    log_to_console("lap_count: " + str(lap_count))

    #calculated data
    #last known SoC in KJ
    log_to_console("last_charge_kj: " + str(last_charge_kj)) 
    #energy spent this lap
    log_to_console("energy_spend_kj: " + str(energy_spend_kj))
    #energy recharge this lap
    log_to_console("energy_recharge_kj: " + str(energy_recharge_kj))
    #last lap energy spent
    log_to_console("last_lap_energy_spent: " + str(last_lap_energy_spent))
    #last lap energy recharge
    log_to_console("last_lap_energy_recharge: " + str(last_lap_energy_recharge))
    log_to_console("kers_charge_kj: " + str(kers_charge_kj))

#calculated charge
kers_charge_kj = 1

def draw_box(x, y, width, height):
    # Draw the top line
    ac.glQuad(x, y, width, 1)
    # Draw the right line
    ac.glQuad(x + width - 1, y, 1, height)
    # Draw the bottom line
    ac.glQuad(x, y + height - 1, width, 1)
    # Draw the left line
    ac.glQuad(x, y, 1, height)


def onFormRender(deltaT):
    """
    We setup this callback, Assetto Corsa will tell us when we can draw.
    """
    global kers_charge_perc, kers_input, ers_recovery, ers_delivery, ers_heat_charging, ers_current_kj, ers_max_kj, lap_count, last_lap_energy_spent, last_lap_energy_recharge, energy_recharge_kj, energy_spend_kj, last_charge_kj
    
    #main bar outline
    draw_box(25, 25, 550, 50)

    #bar amount
    ac.setText(bar_kj, str(int(ers_max_kj)))
    ac.setText(last_lap_recharge, str(int(last_lap_energy_spent)))
    
    #need to draw boxes around stuff to max it look nice
    #main bar value = bar_kj - spent (as a percentage)
    main_bar_value = (ers_max_kj - energy_spend_kj) / ers_max_kj
    #set color yellow
    ac.glColor3f(1,1,0)
    #draw bar
    ac.glQuad(25, 25, main_bar_value*550, 50)

    #draw corner lines
    #TODO


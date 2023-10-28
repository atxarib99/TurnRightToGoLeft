import sys
import ac
import acsys

appName = "State of Kachow"

#markers 
corner_data = [0.2, 0.4, 0.6, 0.7]

# calibratable numbers
lapEnergyTarget = 40

#configurables
#TODO: implement
app_scale_factor = 1
bar_width = 500*app_scale_factor
bar_height = 25*app_scale_factor
marker_thickness = 2

#labels
last_lap_recharge = 0
bar_mj = 0
this_lap_energy_recharge = 0
this_lap_energy_spent = 0

target_spinner = 0

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
ers_current_mj = -1
#battery max kj
ers_max_mj = ac.getCarState(0, acsys.CS.ERSMaxJ) / 1000000
#current lap count (used for reset)
lap_count = 0

#calculated data
#energy spent this lap
energy_spend_mj = 0
#energy recharge this lap
energy_recharge_mj = 0
#last lap energy spent
last_lap_energy_spent = 0
#last lap energy recharge
last_lap_energy_recharge = 0
#calculated charge, assume car starts at 100 pct
kers_charge_mj = ers_max_mj
#last known SoC in KJ
last_charge_mj = kers_charge_mj

#app meta
cnt = 0
first_loop = True
debug = False

def log_to_file(msg):
    ac.log(appName + ": " + str(msg))

def log_to_console(msg):
    ac.console(appName + ": " + str(msg))

def log(msg):
    ac.log(appName + ": " + str(msg))
    ac.console(appName + ": " + str(msg))

def acMain(ac_version):
    global bar_mj, last_lap_recharge, this_lap_energy_recharge, this_lap_energy_spent, target_spinner
    appWindow = ac.newApp(appName)
    ac.setSize(appWindow, 600*app_scale_factor, 150*app_scale_factor)

    #text displays
    last_lap_recharge = ac.addLabel(appWindow, "recharge")
    ac.setPosition(last_lap_recharge, 80*app_scale_factor, 75*app_scale_factor)
    ac.setFontSize(last_lap_recharge, 16*app_scale_factor)
    bar_mj = ac.addLabel(appWindow, "bar_mj")
    ac.setPosition(bar_mj, 450*app_scale_factor, 75*app_scale_factor)
    ac.setFontSize(bar_mj, 16*app_scale_factor)

    #spinner
    target_spinner = ac.addSpinner(appWindow, "Target")
    ac.setValue(target_spinner, lapEnergyTarget)
    
    ac.addRenderCallback(appWindow, onFormRender)

    return appName


def acUpdate(deltaT):
    """
    acUpdate is called when Assetto Corsa has new data available to communicate.
    """
    global kers_charge_perc, kers_input, ers_recovery, ers_delivery, ers_heat_charging, ers_current_mj, ers_max_mj, lap_count, last_lap_energy_spent, last_lap_energy_recharge, energy_recharge_mj, energy_spend_mj, last_charge_mj, cnt, kers_charge_mj, lapEnergyTarget

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
    #get ers_current_mj, set last_kj first
    ers_current_mj = ac.getCarState(0, acsys.CS.ERSCurrentKJ)
    #get ers_max_mj
    #current lap
    #if lap count has changed, update, and reset current lap metrics
    if lap_count != ac.getCarState(0, acsys.CS.LapCount):
        lap_count = ac.getCarState(0, acsys.CS.LapCount)
        last_lap_energy_spent = energy_spend_mj
        last_lap_energy_recharge = energy_recharge_mj
        energy_spend_mj = 0
        energy_recharge_mj = 0
        
    #calculate charge in mj
    last_charge_mj = kers_charge_mj
    kers_charge_mj = kers_charge_perc * ers_max_mj

    #calculate deltas 
    #if current charge has gone down, we've spent
    if last_charge_mj - kers_charge_mj > 0:
        energy_spend_mj += abs(last_charge_mj - kers_charge_mj)
    else:
        energy_recharge_mj += abs(last_charge_mj - kers_charge_mj)

    if not first_loop:
        lapEnergyTarget = ac.getValue(target_spinner) / 10

    #every 100 iterations dump to console
    if debug:
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
    log_to_console("ers_current_mj: " + str(ers_current_mj)) 
    #battery max kj
    log_to_console("ers_max_mj: " + str(ers_max_mj))
    #current lap count (used for reset)
    log_to_console("lap_count: " + str(lap_count))

    #calculated data
    #last known SoC in KJ
    log_to_console("last_charge_mj: " + str(last_charge_mj)) 
    #energy spent this lap
    log_to_console("energy_spend_mj: " + str(energy_spend_mj))
    #energy recharge this lap
    log_to_console("energy_recharge_mj: " + str(energy_recharge_mj))
    #last lap energy spent
    log_to_console("last_lap_energy_spent: " + str(last_lap_energy_spent))
    #last lap energy recharge
    log_to_console("last_lap_energy_recharge: " + str(last_lap_energy_recharge))
    log_to_console("kers_charge_mj: " + str(kers_charge_mj))


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
    global kers_charge_perc, kers_input, ers_recovery, ers_delivery, ers_heat_charging, ers_current_mj, ers_max_mj, lap_count, last_lap_energy_spent, last_lap_energy_recharge, energy_recharge_mj, energy_spend_mj, last_charge_mj, lapEnergyTarget, target_spinner, first_loop
    
    #main bar outline
    draw_box(25*app_scale_factor, 25*app_scale_factor, bar_width, bar_height)

    #bar amount
    ac.setText(bar_mj, str(round(lapEnergyTarget,2)))
    ac.setText(last_lap_recharge, str(round(last_lap_energy_recharge,2)))
    
    #need to draw boxes around stuff to max it look nice
    #main bar value = bar_mj - spent (as a percentage)
    main_bar_value = (lapEnergyTarget - energy_spend_mj) / lapEnergyTarget
    #set color yellow
    ac.glColor3f(1,1,0)
    #draw bar
    result = ac.glQuad(25*app_scale_factor, 25*app_scale_factor, max(main_bar_value*bar_width, 0), bar_height)

    #draw corner lines
    ac.glColor3f(0,0,0)
    for corner in corner_data:
        x_shift = bar_width * (1-corner)
        ac.glQuad((25 + x_shift), 25*app_scale_factor, marker_thickness, bar_height)
    
    
    #spinner
    ac.setPosition(target_spinner, 200*app_scale_factor, 75*app_scale_factor)
    if first_loop:
        ac.setValue(target_spinner, lapEnergyTarget)
        first_loop = False
    else:
        ac.setRange(target_spinner, 1, 80.0)
    result = ac.setStep(target_spinner, 1)
    log_to_console(result)
    
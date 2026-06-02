import sys
import ac
import acsys
import math
from third_party.sim_info import SimInfo

appName = "fuel_tracker"

# Global variables
current_fuel = 0.0
last_fuel = 0.0
lap_fuel_usage = []  # Holds fuel used in last 3 laps
last_lap_count = 0
estimated_laps = 0
session_laps_remaining = 0
fuel_to_take = 0
session = None

# Window size
window_width = 220
window_height = 230

label_current_fuel = None
label_fuel_lap1 = None
label_fuel_lap2 = None
label_fuel_lap3 = None
label_estimated_laps = None
label_session_laps_remaining = None
label_fuel_to_take = None


def log_to_file(msg):
    ac.log(appName + ": " + str(msg))


def log_to_console(msg):
    ac.console(appName + ": " + str(msg))


def log(msg):
    ac.log(appName + ": " + str(msg))
    ac.console(appName + ": " + str(msg))


def acMain(ac_version):
    global \
        label_current_fuel, \
        label_fuel_lap1, \
        label_fuel_lap2, \
        label_fuel_lap3, \
        label_estimated_laps, \
        label_session_laps_remaining, \
        label_fuel_to_take

    # Create app window
    appWindow = ac.newApp(appName)
    ac.setSize(appWindow, window_width, window_height)
    log("Fuel Tracker Initialized")

    # Create labels for current fuel level and lap fuel usage
    label_current_fuel = ac.addLabel(appWindow, "Current Fuel: ")
    label_fuel_lap1 = ac.addLabel(appWindow, "Fuel Lap 1: ")
    label_fuel_lap2 = ac.addLabel(appWindow, "Fuel Lap 2: ")
    label_fuel_lap3 = ac.addLabel(appWindow, "Fuel Lap 3: ")
    label_estimated_laps = ac.addLabel(appWindow, "Fuel Estimated Laps: ")
    label_session_laps_remaining = ac.addLabel(appWindow, "Session Laps Remaining: ")
    label_fuel_to_take = ac.addLabel(appWindow, "Fuel To Take: ")

    # Position the labels
    ac.setPosition(label_current_fuel, 10, 20)
    ac.setPosition(label_fuel_lap1, 10, 50)
    ac.setPosition(label_fuel_lap2, 10, 80)
    ac.setPosition(label_fuel_lap3, 10, 110)
    ac.setPosition(label_estimated_laps, 10, 140)
    ac.setPosition(label_session_laps_remaining, 10, 170)
    ac.setPosition(label_fuel_to_take, 10, 200)

    # Set up render callback
    ac.addRenderCallback(appWindow, onFormRender)

    return appName


def check_session_change(siminfo):
    global session
    newsession = siminfo.graphics.session
    if session is None:
        session = newsession
        return False
    if session != newsession:
        log(session)
        log(newsession)
        session = newsession
        log("Resetting for new session.")
        return True

    return False


def reset_all():
    global \
        current_fuel, \
        last_fuel, \
        lap_fuel_usage, \
        last_lap_count, \
        estimated_laps, \
        session_laps_remaining, \
        fuel_to_take, \
        session

    current_fuel = 0.0
    last_fuel = 0.0
    lap_fuel_usage = []  # Holds fuel used in last 3 laps
    last_lap_count = 0
    estimated_laps = 0
    session_laps_remaining = 0
    fuel_to_take = 0
    session = None


def acUpdate(deltaT):
    global \
        current_fuel, \
        last_fuel, \
        lap_fuel_usage, \
        last_lap_count, \
        estimated_laps, \
        session_laps_remaining, \
        fuel_to_take

    siminfo = SimInfo()

    # check if session has changed
    if check_session_change(siminfo):
        reset_all()

    lap_invalid = False
    # session info
    session = siminfo.graphics.session
    # Get the current lap count
    current_lap_count = ac.getCarState(0, acsys.CS.LapCount)
    # Get the current fuel level
    current_fuel = float(siminfo.physics.fuel)
    # speed
    speed = ac.getCarState(0, acsys.CS.SpeedKMH)

    # if we are in our pit box, reset everything
    # need to reset fuel usage, for back to pits usage
    # ignore during race sessions
    if ac.isCarInPit(0):
        lap_invalid = True
        last_fuel = 0
        last_lap_count = current_lap_count

    # start edge case, use 10kph as we have started moving
    # this speed check should fix issue with last_fuel starting at 30L
    if last_fuel == 0.0 and current_fuel != 0.0 and speed > 10:
        last_fuel = current_fuel

    should_recalculate_fuel_to_take = False

    # Check if the lap count has updated (new lap)
    if current_lap_count != last_lap_count:
        # Calculate fuel used on the last lap
        fuel_used_last_lap = last_fuel - current_fuel

        # Update the lap fuel usage
        if not lap_invalid:
            lap_fuel_usage.append(fuel_used_last_lap)

        # Update last lap count
        last_lap_count = current_lap_count

        # Update last fuel level for the next lap
        last_fuel = current_fuel

        # Estimate laps remaining if time based
        # TODO: Implement non-timed race
        # is_timed_race = int(siminfo.static.isTimedRace)
        # has_extra_lap = int(siminfo.static.hasExtraLap)
        # Get remaining session time
        try:
            session_time_remaining_ms = float(siminfo.graphics.sessionTimeLeft)
            # Utilize best time for estimate
            best_lap_time = str(siminfo.graphics.bestTime)
            best_lap_time_ms = lap_time_to_ms(best_lap_time)
            if best_lap_time_ms != 0:
                session_laps_remaining = math.ceil(
                    session_time_remaining_ms / best_lap_time_ms
                )
                # recalculate fuel neeeded
                should_recalculate_fuel_to_take = True

        except:
            session_laps_remaining = 0

    # do a simple ignore erraneous records to best estimate fuel_usage
    try:
        mean = sum(lap_fuel_usage) / len(lap_fuel_usage)
        squared_diffs = [(x - mean) ** 2 for x in lap_fuel_usage]
        variance = sum(squared_diffs) / len(lap_fuel_usage)
        std_dev = math.sqrt(variance)

        true_avg = 0
        true_avg_count = 0
        for fuel in lap_fuel_usage:
            # if within 1 std_dev
            if fuel < (mean + std_dev) and fuel > (mean - std_dev):
                true_avg += fuel
                true_avg_count += 1

        if true_avg_count > 0:
            true_avg /= true_avg_count

        if true_avg > 0:
            estimated_laps = current_fuel / true_avg
            # recalculate fuel needed
            if should_recalculate_fuel_to_take:
                fuel_to_take = session_laps_remaining * true_avg - current_fuel
    except:
        estimated_laps = 0

    siminfo.close()


def onFormRender(deltaT):
    global \
        current_fuel, \
        lap_fuel_usage, \
        label_current_fuel, \
        label_fuel_lap1, \
        label_fuel_lap2, \
        label_fuel_lap3, \
        label_session_laps_remaining, \
        label_fuel_to_take

    # Update the labels with the current fuel level and fuel usage for the last 3 laps
    # ac.setText(label_current_fuel, "Current Fuellll: " + str(current_fuel))
    ac.setText(label_current_fuel, "Current Fuel: {:.2f} L".format(current_fuel))
    if len(lap_fuel_usage) > 0:
        ac.setText(label_fuel_lap1, "Fuel Lap 1: {:.2f} L".format(lap_fuel_usage[-1]))
    if len(lap_fuel_usage) > 1:
        ac.setText(label_fuel_lap2, "Fuel Lap 2: {:.2f} L".format(lap_fuel_usage[-2]))
    if len(lap_fuel_usage) > 2:
        ac.setText(label_fuel_lap3, "Fuel Lap 3: {:.2f} L".format(lap_fuel_usage[-3]))
    ac.setText(
        label_estimated_laps, "Fuel Laps Rem: {:.2f} laps".format(estimated_laps)
    )
    ac.setText(
        label_session_laps_remaining,
        "Sesh Laps Rem: {:.2f} laps".format(session_laps_remaining),
    )
    ac.setText(label_fuel_to_take, "Fuel To Take: {:.2f} L".format(fuel_to_take))


def lap_time_to_ms(time_str: str) -> float:
    # Handle missing or invalid format
    if not time_str or "-" in time_str:
        return 0.0

    try:
        minutes, seconds, millis = time_str.split(":")
        total_ms = (int(minutes) * 60 * 1000) + (int(seconds) * 1000) + int(millis)
        return float(total_ms)
    except ValueError:
        return 0.0

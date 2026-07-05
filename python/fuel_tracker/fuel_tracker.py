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
true_avg = 0
target_fuel = 0
session = None

# Window size
window_scale = 1.0
window_width = 300 * window_scale
window_height = 200 * window_scale
# dont add padding to height, otherwise it'll get used in box_size calculation
top_padding = 25

# calculate box sizes needed with static padding 5
box_width = (window_width - 20) / 3
box_height = (window_height - 20) / 3


# title labels
label_current_fuel_title = None
label_fuel_lap1_title = None
label_fuel_lap2_title = None
label_fuel_lap3_title = None
label_estimated_laps_title = None
label_session_laps_remaining_title = None
label_fuel_to_take_title = None
label_target_fuel_title = None
label_true_avg_title = None

label_current_fuel = None
label_fuel_lap1 = None
label_fuel_lap2 = None
label_fuel_lap3 = None
label_estimated_laps = None
label_session_laps_remaining = None
label_fuel_to_take = None
label_target_fuel = None
label_true_avg = None


def log_to_file(msg):
    ac.log(appName + ": " + str(msg))


def log_to_console(msg):
    ac.console(appName + ": " + str(msg))


def log(msg):
    ac.log(appName + ": " + str(msg))
    ac.console(appName + ": " + str(msg))


def create_title_label(appWindow, label, grid_x, grid_y, text):
    label = ac.addLabel(appWindow, text)
    ac.setSize(label, box_width, 50)
    ac.setFontAlignment(label, "center")
    calc_x = 5 * (grid_x + 1) + (grid_x * box_width)
    calc_y = 2 + 5 * (grid_y + 1) + (grid_y * box_height) + top_padding
    ac.setPosition(label, calc_x, calc_y)
    return label


def create_value_label(appWindow, label, grid_x, grid_y):
    label = ac.addLabel(appWindow, "idk")
    ac.setSize(label, box_width, 50)
    ac.setFontAlignment(label, "center")
    calc_x = 5 * (grid_x + 1) + (grid_x * box_width)
    calc_y = (box_height / 2) + 5 * (grid_y + 1) + (grid_y * box_height) + top_padding
    ac.setPosition(label, calc_x, calc_y)
    return label


def acMain(ac_version):
    global \
        label_current_fuel, \
        label_fuel_lap1, \
        label_fuel_lap2, \
        label_fuel_lap3, \
        label_estimated_laps, \
        label_session_laps_remaining, \
        label_fuel_to_take, \
        label_target_fuel, \
        label_true_avg, \
        label_current_fuel_title, \
        label_fuel_lap1_title, \
        label_fuel_lap2_title, \
        label_fuel_lap3_title, \
        label_estimated_laps_title, \
        label_session_laps_remaining_title, \
        label_fuel_to_take_title, \
        label_target_fuel_title, \
        label_true_avg_title

    # Create app window
    appWindow = ac.newApp(appName)
    ac.setSize(appWindow, window_width, window_height + top_padding)
    log("Fuel Tracker Initialized")

    # Create title labels

    label_current_fuel_title = create_title_label(
        appWindow, label_current_fuel_title, 1, 0, "Current Fuel"
    )
    label_fuel_lap1_title = create_title_label(
        appWindow, label_fuel_lap1_title, 0, 0, "Lap 1"
    )
    label_fuel_lap2_title = create_title_label(
        appWindow, label_fuel_lap2_title, 0, 1, "Lap 2"
    )
    label_fuel_lap3_title = create_title_label(
        appWindow, label_fuel_lap3_title, 0, 2, "Lap 3"
    )
    label_estimated_laps_title = create_title_label(
        appWindow, label_estimated_laps_title, 2, 0, "Fuel Rem"
    )
    label_session_laps_remaining_title = create_title_label(
        appWindow,
        label_session_laps_remaining_title,
        2,
        1,
        "Sesh Rem",
    )
    label_fuel_to_take_title = create_title_label(
        appWindow,
        label_fuel_to_take_title,
        2,
        2,
        "Refuel",
    )
    label_target_fuel_title = create_title_label(
        appWindow, label_target_fuel_title, 1, 1, "Target"
    )
    label_true_avg_title = create_title_label(
        appWindow,
        label_true_avg_title,
        1,
        2,
        "True Avg",
    )

    # Create labels for current fuel level and lap fuel usage
    label_current_fuel = create_value_label(appWindow, label_current_fuel, 1, 0)
    label_fuel_lap1 = create_value_label(appWindow, label_fuel_lap1, 0, 0)
    label_fuel_lap2 = create_value_label(appWindow, label_fuel_lap2, 0, 1)
    label_fuel_lap3 = create_value_label(appWindow, label_fuel_lap3, 0, 2)
    label_estimated_laps = create_value_label(appWindow, label_estimated_laps, 2, 0)
    label_session_laps_remaining = create_value_label(
        appWindow, label_session_laps_remaining, 2, 1
    )
    label_fuel_to_take = create_value_label(appWindow, label_fuel_to_take, 2, 2)
    label_true_avg = create_value_label(appWindow, label_true_avg, 1, 2)
    label_target_fuel = create_value_label(appWindow, label_target_fuel, 1, 1)

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
        fuel_to_take, \
        true_avg, \
        target_fuel

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
                target_fuel = current_fuel / session_laps_remaining
    except:
        estimated_laps = 0

    siminfo.close()


def draw_box(x, y, width, height):
    """
    Draws a box using the draw() function with the given x, y coordinates,
    width, and height.
    """
    ac.glColor3f(0, 1, 0)
    ac.glQuad(x, y + top_padding, width, 1)  # Top edge
    ac.glQuad(x, y + top_padding + height - 1, width, 1)  # Bottom edge
    ac.glQuad(x, y + top_padding, 1, height)  # Left edge
    ac.glQuad(x + width - 1, y + top_padding, 1, height)  # Right edge
    ac.glColor3f(0, 0, 1)


def onFormRender(deltaT):
    global \
        current_fuel, \
        lap_fuel_usage, \
        label_current_fuel, \
        label_fuel_lap1, \
        label_fuel_lap2, \
        label_fuel_lap3, \
        label_session_laps_remaining, \
        label_fuel_to_take, \
        label_true_avg, \
        label_target_fuel

    # draw boxes within window
    # row 1
    draw_box(5, 5, box_width, box_height)
    draw_box(5, 10 + box_height, box_width, box_height)
    draw_box(5, 15 + (box_height * 2), box_width, box_height)

    # row 2
    draw_box(10 + box_width, 5, box_width, box_height)
    draw_box(10 + box_width, 10 + box_height, box_width, box_height)
    draw_box(10 + box_width, 15 + (box_height * 2), box_width, box_height)

    # row 2
    draw_box(15 + (box_width * 2), 5, box_width, box_height)
    draw_box(15 + (box_width * 2), 10 + box_height, box_width, box_height)
    draw_box(15 + (box_width * 2), 15 + (box_height * 2), box_width, box_height)

    # Update the labels with the current fuel level and fuel usage for the last 3 laps
    # ac.setText(label_current_fuel, "Current Fuellll: " + str(current_fuel))
    ac.setText(label_current_fuel, "{:.2f} L".format(current_fuel))
    if len(lap_fuel_usage) > 0:
        ac.setText(label_fuel_lap1, "{:.2f} L".format(lap_fuel_usage[-1]))
    if len(lap_fuel_usage) > 1:
        ac.setText(label_fuel_lap2, "{:.2f} L".format(lap_fuel_usage[-2]))
    if len(lap_fuel_usage) > 2:
        ac.setText(label_fuel_lap3, "{:.2f} L".format(lap_fuel_usage[-3]))
    ac.setText(label_estimated_laps, "{:.2f} laps".format(estimated_laps))
    ac.setText(
        label_session_laps_remaining,
        "{:.2f} laps".format(session_laps_remaining),
    )
    ac.setText(label_fuel_to_take, "{:.2f} L".format(fuel_to_take))
    ac.setText(label_target_fuel, "{:.2f} L".format(target_fuel))
    ac.setText(label_true_avg, "{:.2f} L".format(true_avg))


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

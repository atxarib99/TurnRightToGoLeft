import ac
import acsys
import functools

appName = "car_select"

SORT_SLOT  = 0
SORT_ALPHA = 1

appWindow      = 0
buttons        = []
button_actions = []
sort_btn_slot  = 0
sort_btn_alpha = 0
sort_mode      = SORT_SLOT
car_count      = 0
active_car     = -1

ROW_HEIGHT   = 26
ROW_H_INNER  = 22
LIST_START_Y = 62
WIN_WIDTH    = 300
SORT_BTN_W   = 135
SORT_BTN_H   = 22

def log(msg):
    ac.log(appName + ": " + str(msg))
    ac.console(appName + ": " + str(msg))


def acMain(ac_version):
    global appWindow, buttons, button_actions, sort_btn_slot, sort_btn_alpha, car_count

    appWindow = ac.newApp(appName)

    car_count = int(ac.getCarsCount())
    win_height = LIST_START_Y + car_count * ROW_HEIGHT + 10
    ac.setSize(appWindow, WIN_WIDTH, win_height)
    log("acMain: car_count={} win_height={}".format(car_count, win_height))

    sort_btn_slot = ac.addButton(appWindow, "By Slot")
    ac.setSize(sort_btn_slot, SORT_BTN_W, SORT_BTN_H)
    ac.setPosition(sort_btn_slot, 10, 32)
    ac.setFontSize(sort_btn_slot, 14)
    ac.addOnClickedListener(sort_btn_slot, onSortSlotClick)

    sort_btn_alpha = ac.addButton(appWindow, "A-Z")
    ac.setSize(sort_btn_alpha, SORT_BTN_W, SORT_BTN_H)
    ac.setPosition(sort_btn_alpha, 155, 32)
    ac.setFontSize(sort_btn_alpha, 14)
    ac.addOnClickedListener(sort_btn_alpha, onSortAlphaClick)

    for i in range(car_count):
        act = functools.partial(onDriverClick, car_id=i)
        act.__name__ = "onDriverClick"
        button_actions.append(act)

        btn = ac.addButton(appWindow, "")
        ac.setSize(btn, WIN_WIDTH - 20, ROW_H_INNER)
        ac.setPosition(btn, 10, LIST_START_Y + i * ROW_HEIGHT)
        ac.setFontSize(btn, 14)
        ac.setBackgroundColor(btn, 0.25, 0.25, 0.25)
        ac.setVisible(btn, 0)
        ac.addOnClickedListener(btn, act)
        buttons.append(btn)

    ac.addRenderCallback(appWindow, onFormRender)
    log("acMain: done")
    return appName


def acUpdate(deltaT):
    pass


def onFormRender(deltaT):
    global active_car

    car_info = []
    for i in range(car_count):
        connected = ac.isConnected(i)
        name_raw  = ac.getDriverName(i)
        model_raw = ac.getCarName(i)

        name_valid = isinstance(name_raw, str) and name_raw and name_raw != "-1"
        if not connected and not name_valid:
            continue

        last_name   = name_raw.split(" ")[-1] if name_valid else "Car{}".format(i)
        short_model = (model_raw[:12] if len(model_raw) > 12 else model_raw) \
                      if isinstance(model_raw, str) and model_raw else ""

        car_info.append({
            'index':  i,
            'driver': last_name,
            'model':  short_model,
        })

    active_car = ac.getFocusedCar()

    for btn in buttons:
        ac.setVisible(btn, 0)

    if sort_mode == SORT_ALPHA:
        sorted_cars = sorted(car_info, key=lambda x: x['driver'].lower())
    else:
        sorted_cars = sorted(car_info, key=lambda x: x['index'])

    for row, car in enumerate(sorted_cars):
        idx = car['index']
        btn = buttons[idx]
        ac.setPosition(btn, 10, LIST_START_Y + row * ROW_HEIGHT)
        ac.setText(btn, "{}  {}".format(car['driver'], car['model']))
        ac.setVisible(btn, 1)

        if idx == active_car:
            ac.setBackgroundColor(btn, 0.8, 0.4, 0.0)
        else:
            ac.setBackgroundColor(btn, 0.25, 0.25, 0.25)

    if sort_mode == SORT_SLOT:
        ac.setBackgroundColor(sort_btn_slot,  0.5, 0.5, 0.65)
        ac.setBackgroundColor(sort_btn_alpha, 0.25, 0.25, 0.25)
    else:
        ac.setBackgroundColor(sort_btn_slot,  0.25, 0.25, 0.25)
        ac.setBackgroundColor(sort_btn_alpha, 0.5, 0.5, 0.65)


def onSortSlotClick(*args):
    global sort_mode
    sort_mode = SORT_SLOT
    log("sort: By Slot")


def onSortAlphaClick(*args):
    global sort_mode
    sort_mode = SORT_ALPHA
    log("sort: A-Z")


def onDriverClick(*args, car_id=0):
    log("focus car_id={}".format(car_id))
    ac.focusCar(car_id)


def acShutdown():
    log("acShutdown")

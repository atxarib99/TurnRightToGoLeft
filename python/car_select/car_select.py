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

# Layout
ROW_HEIGHT   = 28
ROW_H_INNER  = 24
LIST_START_Y = 64
WIN_WIDTH    = 320
SORT_BTN_W   = 143
SORT_BTN_H   = 24
STRIPE_X     = 8
STRIPE_W     = 5
BTN_X        = STRIPE_X + STRIPE_W + 5   # 18
BTN_W        = WIN_WIDTH - BTN_X - 8     # 294

# One color per car model, assigned by hash so the same model always gets the same color
MODEL_COLORS = [
    (0.90, 0.25, 0.25),  # red
    (0.28, 0.58, 0.95),  # blue
    (0.22, 0.82, 0.40),  # green
    (0.95, 0.72, 0.12),  # amber
    (0.78, 0.30, 0.92),  # purple
    (0.95, 0.50, 0.12),  # orange
    (0.12, 0.82, 0.78),  # teal
    (0.92, 0.28, 0.65),  # pink
    (0.58, 0.88, 0.18),  # lime
    (0.18, 0.68, 0.90),  # sky
    (0.95, 0.95, 0.28),  # yellow
    (0.90, 0.55, 0.75),  # mauve
]

# Cache stripe colors per slot so we don't recompute every frame
_stripe_colors = {}


def log(msg):
    ac.log(appName + ": " + str(msg))
    ac.console(appName + ": " + str(msg))


def model_color(model_str):
    if not model_str:
        return (0.5, 0.5, 0.5)
    return MODEL_COLORS[abs(hash(model_str)) % len(MODEL_COLORS)]


def acMain(ac_version):
    global appWindow, buttons, button_actions, sort_btn_slot, sort_btn_alpha, car_count

    appWindow = ac.newApp(appName)

    car_count = int(ac.getCarsCount())
    win_height = LIST_START_Y + car_count * ROW_HEIGHT + 10
    ac.setSize(appWindow, WIN_WIDTH, win_height)
    log("acMain: car_count={} win_height={}".format(car_count, win_height))

    # Sort buttons
    sort_btn_slot = ac.addButton(appWindow, "By Slot")
    ac.setSize(sort_btn_slot, SORT_BTN_W, SORT_BTN_H)
    ac.setPosition(sort_btn_slot, 8, 32)
    ac.setFontSize(sort_btn_slot, 14)
    ac.addOnClickedListener(sort_btn_slot, onSortSlotClick)

    sort_btn_alpha = ac.addButton(appWindow, "A-Z")
    ac.setSize(sort_btn_alpha, SORT_BTN_W, SORT_BTN_H)
    ac.setPosition(sort_btn_alpha, WIN_WIDTH - SORT_BTN_W - 8, 32)
    ac.setFontSize(sort_btn_alpha, 14)
    ac.addOnClickedListener(sort_btn_alpha, onSortAlphaClick)

    # One driver button per car slot
    for i in range(car_count):
        act = functools.partial(onDriverClick, car_id=i)
        act.__name__ = "onDriverClick"
        button_actions.append(act)

        btn = ac.addButton(appWindow, "")
        ac.setSize(btn, BTN_W, ROW_H_INNER)
        ac.setPosition(btn, BTN_X, LIST_START_Y + i * ROW_HEIGHT)
        ac.setFontSize(btn, 15)
        ac.setFontAlignment(btn, "left")
        ac.setBackgroundColor(btn, 0.15, 0.15, 0.15)
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
        short_model = (model_raw[:14] if len(model_raw) > 14 else model_raw) \
                      if isinstance(model_raw, str) and model_raw else ""

        if i not in _stripe_colors:
            _stripe_colors[i] = model_color(model_raw if isinstance(model_raw, str) else "")

        car_info.append({
            'index':  i,
            'driver': last_name,
            'model':  short_model,
        })

    active_car = ac.getFocusedCar()

    # Hide all driver buttons
    for btn in buttons:
        ac.setVisible(btn, 0)

    if sort_mode == SORT_ALPHA:
        sorted_cars = sorted(car_info, key=lambda x: x['driver'].lower())
    else:
        sorted_cars = sorted(car_info, key=lambda x: x['index'])

    # Draw separator line between sort buttons and list
    ac.glColor3f(0.35, 0.35, 0.35)
    ac.glQuad(8, LIST_START_Y - 4, WIN_WIDTH - 16, 1)

    for row, car in enumerate(sorted_cars):
        idx = car['index']
        btn = buttons[idx]
        y   = LIST_START_Y + row * ROW_HEIGHT

        ac.setPosition(btn, BTN_X, y)
        ac.setText(btn, "  {}    {}".format(car['driver'], car['model']))
        ac.setVisible(btn, 1)

        if idx == active_car:
            ac.setBackgroundColor(btn, 0.50, 0.25, 0.02)
        else:
            ac.setBackgroundColor(btn, 0.15, 0.15, 0.15)

        # Colored model stripe
        r, g, b = _stripe_colors.get(idx, (0.5, 0.5, 0.5))
        if idx == active_car:
            ac.glColor3f(min(r + 0.1, 1.0), min(g + 0.1, 1.0), min(b + 0.1, 1.0))
        else:
            ac.glColor3f(r * 0.75, g * 0.75, b * 0.75)
        ac.glQuad(STRIPE_X, y + 3, STRIPE_W, ROW_H_INNER - 6)

    # Sort button highlight
    if sort_mode == SORT_SLOT:
        ac.setBackgroundColor(sort_btn_slot,  0.25, 0.45, 0.72)
        ac.setBackgroundColor(sort_btn_alpha, 0.18, 0.18, 0.18)
    else:
        ac.setBackgroundColor(sort_btn_slot,  0.18, 0.18, 0.18)
        ac.setBackgroundColor(sort_btn_alpha, 0.25, 0.45, 0.72)


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

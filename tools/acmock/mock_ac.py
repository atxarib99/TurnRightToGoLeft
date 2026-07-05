"""Mock of AC's built-in ``ac`` module.

Implements the UI + telemetry surface the apps use. Instead of drawing to the
game, it records a per-frame "scene" (window size, persistent controls/labels,
and the immediate-mode rectangles issued during onFormRender) which the server
serializes to JSON for the browser canvas.

Design notes:
  * A single ``Runtime`` holds all mutable state; ``bind(runtime)`` wires it in
    BEFORE the target app is imported (some apps call ac.* at import time).
  * Every control "add" returns an int id; later set*/get* calls look it up.
  * Immediate-mode drawing: glColor3f sets the current color; glQuad appends a
    filled rect (negative width/height normalized so it never vanishes).
  * A module-level ``__getattr__`` returns a logging no-op for any ac.* function
    not implemented here, so apps using rare APIs never AttributeError.
"""

from collections import deque

from . import arity

CONSOLE_MAX = 400


class Runtime(object):
    def __init__(self, data, strict=False):
        self.data = data                # DataProvider
        self.strict = strict
        self.window = {"name": "", "w": 200, "h": 200}
        self.window_id = None
        self.controls = {}              # id -> dict
        self._next_id = 1
        self.frame_rects = []           # reset each frame
        self.cur_color = (1.0, 1.0, 1.0, 1.0)
        self.console = deque(maxlen=CONSOLE_MAX)
        self.render_callback = None
        self.app_module = None
        self._warned = set()

    # -- ids / controls ------------------------------------------------------

    def new_id(self):
        cid = self._next_id
        self._next_id += 1
        return cid

    def add_control(self, ctype, text):
        cid = self.new_id()
        self.controls[cid] = {
            "id": cid, "type": ctype, "text": str(text),
            "x": 0.0, "y": 0.0, "w": 0.0, "h": 0.0,
            "size": 12.0, "align": "left",
            "color": (1.0, 1.0, 1.0, 1.0),
            "value": 0.0, "vmin": 0.0, "vmax": 100.0, "step": 1.0,
            "visible": True, "callback": None,
        }
        return cid

    # -- frame / scene -------------------------------------------------------

    def reset_frame(self):
        self.frame_rects = []
        self.cur_color = (1.0, 1.0, 1.0, 1.0)

    def log_line(self, line):
        self.console.append(line)

    def scene(self):
        labels, widgets = [], []
        for c in self.controls.values():
            if not c["visible"]:
                continue
            if c["type"] == "label":
                labels.append({
                    "x": c["x"], "y": c["y"], "w": c["w"], "h": c["h"],
                    "text": c["text"], "size": c["size"], "align": c["align"],
                    "color": _hex(c["color"]),
                })
            else:
                widgets.append({
                    "id": c["id"], "type": c["type"], "x": c["x"], "y": c["y"],
                    "w": c["w"], "h": c["h"], "text": c["text"],
                    "value": c["value"], "vmin": c["vmin"], "vmax": c["vmax"],
                    "step": c["step"],
                })
        return {
            "window": self.window,
            "rects": list(self.frame_rects),
            "labels": labels,
            "widgets": widgets,
            "console": list(self.console),
        }

    # -- event dispatch (called from the driver, on the app thread) ----------

    def dispatch_event(self, ev):
        cid = ev.get("id")
        c = self.controls.get(cid)
        if not c:
            return
        kind = ev.get("kind")
        cb = c.get("callback")
        if kind == "click":
            if cb:
                cb(0, 0)
        elif kind == "check":
            val = 1 if ev.get("value") else 0
            c["value"] = val
            if cb:
                cb(c["text"], val)
        elif kind == "spin":
            c["value"] = ev.get("value", c["value"])
            if cb:
                cb()


# --------------------------------------------------------------------------
# module-level binding
# --------------------------------------------------------------------------

_RT = None


def bind(runtime):
    global _RT
    _RT = runtime


def _rt():
    if _RT is None:
        raise RuntimeError("acmock: ac module used before bind(runtime)")
    return _RT


def _hex(color):
    r, g, b = color[0], color[1], color[2]
    clamp = lambda v: max(0, min(255, int(round(v * 255))))
    return "#%02x%02x%02x" % (clamp(r), clamp(g), clamp(b))


# --------------------------------------------------------------------------
# App / window management
# --------------------------------------------------------------------------

def newApp(name):
    rt = _rt()
    rt.window["name"] = str(name)
    cid = rt.new_id()
    rt.window_id = cid
    return cid


def setSize(cid, w, h):
    rt = _rt()
    if cid == rt.window_id:
        rt.window["w"] = float(w)
        rt.window["h"] = float(h)
    elif cid in rt.controls:
        rt.controls[cid]["w"] = float(w)
        rt.controls[cid]["h"] = float(h)
    return 1


def setTitle(cid, title):
    rt = _rt()
    if cid == rt.window_id:
        rt.window["name"] = str(title)
    return 1


def addRenderCallback(cid, fn):
    _rt().render_callback = fn
    return 1


def setBackgroundOpacity(cid, value):
    return 1


def drawBackground(cid, value):
    return 1


def drawBorder(cid, value):
    return 1


def setBackgroundColor(cid, r, g, b):
    return 1


def setVisible(cid, value):
    rt = _rt()
    if cid in rt.controls:
        rt.controls[cid]["visible"] = bool(value)
    return 1


# --------------------------------------------------------------------------
# Controls
# --------------------------------------------------------------------------

def addLabel(win, text):
    return _rt().add_control("label", text)


def addButton(win, text):
    return _rt().add_control("button", text)


def addSpinner(win, text):
    return _rt().add_control("spinner", text)


def addCheckBox(win, text):
    return _rt().add_control("checkbox", text)


def addProgressBar(win, text):
    return _rt().add_control("progressbar", text)


def addInputText(win, text):
    return _rt().add_control("inputtext", text)


def _set(cid, key, value):
    rt = _rt()
    if cid in rt.controls:
        rt.controls[cid][key] = value
    return 1


def setText(cid, text):
    return _set(cid, "text", str(text))


def getText(cid):
    rt = _rt()
    return rt.controls.get(cid, {}).get("text", "")


def setPosition(cid, x, y):
    rt = _rt()
    if cid in rt.controls:
        rt.controls[cid]["x"] = float(x)
        rt.controls[cid]["y"] = float(y)
    return 1


def getPosition(cid):
    rt = _rt()
    c = rt.controls.get(cid, {})
    return (c.get("x", 0.0), c.get("y", 0.0))


def setFontSize(cid, size):
    return _set(cid, "size", float(size))


def setFontAlignment(cid, alignment):
    return _set(cid, "align", str(alignment))


def setFontColor(cid, r, g, b, a=1.0):
    return _set(cid, "color", (r, g, b, a))


def setCustomFont(cid, *args):
    return 1


def initFont(*args):
    return 1


def setValue(cid, value):
    return _set(cid, "value", value)


def getValue(cid):
    rt = _rt()
    return rt.controls.get(cid, {}).get("value", 0.0)


def setRange(cid, vmin, vmax, *rest):
    rt = _rt()
    if cid in rt.controls:
        rt.controls[cid]["vmin"] = float(vmin)
        rt.controls[cid]["vmax"] = float(vmax)
    return 1


def setStep(cid, step):
    return _set(cid, "step", float(step))


def addOnClickedListener(cid, fn):
    return _set(cid, "callback", fn)


def addOnCheckBoxChanged(cid, fn):
    return _set(cid, "callback", fn)


def addOnValueChangeListener(cid, fn):
    return _set(cid, "callback", fn)


def addOnValidateListener(cid, fn):
    return _set(cid, "callback", fn)


# --------------------------------------------------------------------------
# Immediate-mode drawing
# --------------------------------------------------------------------------

def glColor3f(r, g, b):
    _rt().cur_color = (r, g, b, 1.0)
    return 1


def glColor4f(r, g, b, a):
    _rt().cur_color = (r, g, b, a)
    return 1


def glQuad(x, y, w, h):
    rt = _rt()
    x, w = float(x), float(w)
    y, h = float(y), float(h)
    # Normalize negative extents (scrubometer draws downward bars with -height).
    x0, x1 = sorted((x, x + w))
    y0, y1 = sorted((y, y + h))
    rt.frame_rects.append({
        "x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0,
        "color": _hex(rt.cur_color),
    })
    return 1


def glQuadTextured(x, y, w, h, texture_id):
    return glQuad(x, y, w, h)


def glBegin(primitive):
    return 1


def glEnd():
    return 1


def glVertex2f(x, y):
    return 1


def newTexture(path):
    return 0


# --------------------------------------------------------------------------
# Telemetry / general info
# --------------------------------------------------------------------------

def getCarState(car_id, ident, opt=None):
    rt = _rt()
    if rt.strict and arity.shape_of(ident) == "scalar":
        if ident not in rt.data.values and ident not in arity.SCALAR_DEFAULTS:
            if ident not in rt._warned:
                rt._warned.add(ident)
                rt.log_line("[strict] no data for getCarState id '%s' -> 0" % ident)
    return rt.data.car_state(ident)


def getCarName(car_id):
    return _rt().data.get("carName", "mock_car")


def getCarTyreCompound(car_id):
    rt = _rt()
    return rt.data.get("tyreCompound", rt.data.get("graphics.tyreCompound", "Soft"))


def getDriverName(car_id):
    return _rt().data.get("static.playerNick", "Tester")


def getTrackName(car_id):
    return _rt().data.get("static.track", "mock_track")


def getTrackConfiguration(car_id):
    return _rt().data.get("static.trackConfiguration", "")


def isCarInPit(car_id):
    return int(_rt().data.get("inPit", _rt().data.get("graphics.isInPit", 0)))


def isCarInPitline(car_id):
    return isCarInPit(car_id)


def isConnected(car_id):
    return 1


def getCarsCount():
    return 1


def sendChatMessage(message):
    _rt().log_line("CHAT: " + str(message))
    return 1


# --------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------

def log(message):
    _rt().log_line(str(message))
    return 1


def console(message):
    _rt().log_line(str(message))
    return 1


# --------------------------------------------------------------------------
# Fallback: any unimplemented ac.* becomes a logging no-op returning 0.
# --------------------------------------------------------------------------

def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)

    def _noop(*args, **kwargs):
        rt = _RT
        if rt is not None:
            rt.log_line("[unimpl] ac.%s(...) ignored" % name)
        return 0

    _noop.__name__ = name
    return _noop

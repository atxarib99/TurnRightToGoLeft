import sys
import ac
import acsys

appName = "liftLag"

installPath = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\assettocorsa\\"
carPath = "content\\cars\\"
possibleCars = ["ks_lamborghini_huracan_gt3", "bmw_z4_gt3", "ks_nissan_gtr_gt3", "ks_mercedes_amg_gt3"]

#will auto find car on game launch
car = ""

#car CL mappings
mapping_found = False
heightToCLMult_front = {}
heightToClMult_diff = {}

#figure out how to do this better
avgAOA = 3.3

#values
frontRideHeight = 0.0
rearRideHeight = 0.0
front_stall = False
diff_stall = False

#app size 
size_mult = 1.0
height = 400 * size_mult
width = 100 * size_mult

#labels
front_label = None
diff_label = None

def log_to_file(msg):
    ac.log(appName + ": " + str(msg))

def log_to_console(msg):
    ac.console(appName + ": " + str(msg))

def log(msg):
    ac.log(appName + ": " + str(msg))
    ac.console(appName + ": " + str(msg))

def acMain(ac_version):
    """
    App setup
    """
    global front_label, diff_label, car

    appWindow = ac.newApp(appName)
    ac.setSize(appWindow, width, height)
    log("SEM SEM SEM SEM")
    log(appName)
    
    car = ac.getCarName(0)

    loadCarInfo()
   
    #run after every cUpdate, after every data point comes in
    ac.addRenderCallback(appWindow, onFormRender)

    #add labels for front/diff
    front_label = ac.addLabel(appWindow, "Front")
    diff_label = ac.addLabel(appWindow, "Diffuser")

    #set positions, update to app size
    ac.setPosition(front_label, 50 * size_mult, 75 * size_mult)
    ac.setPosition(diff_label, 50 * size_mult, 325 * size_mult)
    ac.setFontAlignment(front_label, "center")
    ac.setFontAlignment(diff_label, "center")
    #maybe set size


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
    """
    Set values
    """
    global frontRideHeight, rearRideHeight, front_stall, diff_stall
    frontRideHeight = ac.getCarState(0, acsys.CS.RideHeight)[0]
    rearRideHeight = ac.getCarState(0, acsys.CS.RideHeight)[1]

    #calc stalls
    front_y3 = linearInterpolate(frontRideHeight, heightToCLMult_front)
    diff_y3 = linearInterpolate(rearRideHeight, heightToClMult_diff)

    if front_y3 < 0.8:
        front_stall = True
    else:
        front_stall = False

    if diff_y3 < 0.8:
        diff_stall = True
    else:
        diff_stall = False


    
def onFormRender(deltaT):
    """
    Render app
    """
    #draw boxes
    #front box
    margin = 5
    draw_box(0+margin, 0+margin, 100-margin, 150-margin)
    #check if front stall
    #if stall fill box
    if front_stall:
        ac.glQuad(0,0,100,150)

    #body box
    draw_box(0+margin, 150+margin, 100-margin, 100-margin)

    #diff box
    draw_box(0+margin, 250+margin, 100-margin, 150-margin)
    #check if rear stall 
    #if stall fill box
    if diff_stall:
        ac.glQuad(0,250,100,150)




def loadCarInfo():
    global heightToCLMult_front, heightToClMult_diff, mapping_found

    #point these to local?

    count = 0
    #get front height mult file
    heightToCLMultFront_file = open(installPath + carPath + car + "\\data\\height_front_CL.lut")
    for line in heightToCLMultFront_file.readlines():
        count += 1
        if line.strip() == "":
            continue
        split = line.split('|')
        heightToCLMult_front[float(split[0])] = float(split[1])
    heightToCLMultFront_file.close()


    #get diffuser height mult file
    heightToCLMultDiff_file = open(installPath + carPath + car + "\\data\\height_diffuser_CL.lut")
    for line in heightToCLMultDiff_file.readlines():
        if line.strip() == "":
            continue
        split = line.split('|')
        heightToClMult_diff[float(split[0])] = float(split[1])
    heightToCLMultDiff_file.close()

    mapping_found = True



def linearInterpolate(x3: float, search_dict: dict):
    #find x1,x2,y1,y3
    found = False
    index = 0
    keys = sorted(list(search_dict.keys()))
    x1,x2,y1,y2 = (keys[0],keys[-1],search_dict[keys[0]],search_dict[keys[-1]])

    #ensure x1<x3<x2, otherwise clip
    if x3 < x1:
        return search_dict[keys[0]]
    if x3 > x2:
        return search_dict[keys[-1]]

    while not found:
        if x3 > keys[index] and x3 > keys[index+1]:
            index += 1
            continue
        #index out of bounds protection?
        x1 = keys[index]
        y1 = search_dict[keys[index]]
        x2 = keys[index+1]
        y2 = search_dict[keys[index+1]]
        found = True

    #calc slope
    slope = (y2-y1)/(x2-x1)
    #-0.02 / .009 = -2.22222222222
    
    #calc perc between x1/x2
    perc = x3/(x1+x2)
    #0.068 / (.1418) = .479

    #apply perc to slope
    y3 = ((y2-y1) * perc) + y1

    return y3


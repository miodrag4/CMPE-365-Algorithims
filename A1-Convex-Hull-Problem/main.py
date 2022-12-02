# Convex hull
#
# Usage: python main.py [-d] file_of_points
#
# You can press ESC in the window to exit.
#
# You'll need Python 3 and must install these packages:
#
#   PyOpenGL, GLFW


import sys, os, math

try:  # PyOpenGL
    from OpenGL.GL import *
except:
    print('Error: PyOpenGL has not been installed.')
    sys.exit(1)

try:  # GLFW
    import glfw
except:
    print('Error: GLFW has not been installed.')
    sys.exit(1)

# Globals

window = None

windowWidth = 800  # window dimensions
windowHeight = 800

minX = None  # range of points
maxX = None
minY = None
maxY = None

r = 0.01  # point radius as fraction of window size

numAngles = 32
thetas = [i / float(numAngles) * 2 * 3.14159 for i in range(numAngles)]  # used for circle drawing

allPoints = []  # list of points

lastKey = None  # last key pressed

discardPoints = False


# Point
#
# A Point stores its coordinates and pointers to the two points beside
# it (CW and CCW) on its hull.  The CW and CCW pointers are None if
# the point is not on any hull.
#
# For debugging, you can set the 'highlight' flag of a point.  This
# will cause the point to be highlighted when it's drawn.

class Point(object):

    def __init__(self, coords):

        self.x = float(coords[0])  # coordinates
        self.y = float(coords[1])

        self.ccwPoint = None  # point CCW of this on hull
        self.cwPoint = None  # point CW of this on hull

        self.highlight = False  # to cause drawing to highlight this point

    def __repr__(self):
        return 'pt(%g,%g)' % (self.x, self.y)

    def drawPoint(self):

        # Highlight with yellow fill

        if self.highlight:
            glColor3f(0.9, 0.9, 0.4)
            glBegin(GL_POLYGON)
            for theta in thetas:
                glVertex2f(self.x + r * math.cos(theta), self.y + r * math.sin(theta))
            glEnd()

        # Outline the point

        glColor3f(0, 0, 0)
        glBegin(GL_LINE_LOOP)
        for theta in thetas:
            glVertex2f(self.x + r * math.cos(theta), self.y + r * math.sin(theta))
        glEnd()

        # Draw edges to next CCW and CW points.

        if self.ccwPoint:
            glColor3f(0, 0, 1)
            drawArrow(self.x, self.y, self.ccwPoint.x, self.ccwPoint.y)

        if self.cwPoint:
            glColor3f(1, 0, 0)
            drawArrow(self.x, self.y, self.cwPoint.x, self.cwPoint.y)


# Draw an arrow between two points, offset a bit to the right

def drawArrow(x0, y0, x1, y1):
    d = math.sqrt((x1 - x0) * (x1 - x0) + (y1 - y0) * (y1 - y0))

    vx = (x1 - x0) / d  # unit direction (x0,y0) -> (x1,y1)
    vy = (y1 - y0) / d

    vpx = -vy  # unit direction perpendicular to (vx,vy)
    vpy = vx

    xa = x0 + 1.5 * r * vx - 0.4 * r * vpx  # arrow tail
    ya = y0 + 1.5 * r * vy - 0.4 * r * vpy

    xb = x1 - 1.5 * r * vx - 0.4 * r * vpx  # arrow head
    yb = y1 - 1.5 * r * vy - 0.4 * r * vpy

    xc = xb - 2 * r * vx + 0.5 * r * vpx  # arrow outside left
    yc = yb - 2 * r * vy + 0.5 * r * vpy

    xd = xb - 2 * r * vx - 0.5 * r * vpx  # arrow outside right
    yd = yb - 2 * r * vy - 0.5 * r * vpy

    glBegin(GL_LINES)
    glVertex2f(xa, ya)
    glVertex2f(xb, yb)
    glEnd()

    glBegin(GL_POLYGON)
    glVertex2f(xb, yb)
    glVertex2f(xc, yc)
    glVertex2f(xd, yd)
    glEnd()


# Determine whether three points make a left or right turn

LEFT_TURN = 1
RIGHT_TURN = 2
COLLINEAR = 3


def turn(a, b, c):
    det = (a.x - c.x) * (b.y - c.y) - (b.x - c.x) * (a.y - c.y)

    if det > 0:
        return LEFT_TURN
    elif det < 0:
        return RIGHT_TURN
    else:
        return COLLINEAR


# Build a convex hull from a set of point
#
# Use the method described in class
#
# Using the Divide & Conquer method


def buildHull(points: list[Point]):
    # Handle base cases of two or three points

    if len(points) == 2:
        points[0].ccwPoint = points[1]
        points[0].cwPoint = points[1]
        points[1].ccwPoint = points[0]
        points[1].cwPoint = points[0]
        return
    if len(points) == 3:
        if turn(points[0], points[1], points[2]) == LEFT_TURN:
            points[0].ccwPoint = points[1]
            points[0].cwPoint = points[1]
            points[1].ccwPoint = points[0]
            points[1].cwPoint = points[0]
        else:
            points[0].ccwPoint = points[1]
            points[0].cwPoint = points[2]
            points[1].ccwPoint = points[2]
            points[1].cwPoint = points[0]
            points[2].ccwPoint = points[0]
            points[2].cwPoint = points[1]
        return

    split = len(points) // 2
    left = points[:split]
    right = points[split:]

    # Handle recursive case.
    #
    # After you get the hull-merge working, do the following: For each
    # point that was removed from the convex hull in a merge, set that
    # point's CCW and CW pointers to None.  You'll see that the arrows
    # from interior points disappear after you do this.

    buildHull(left)
    buildHull(right)

    # Merge the individual hulls.
    # Keep track of points stepped over during walk up/down.
    previous_points: set[Point] = set()

    # Walk up
    left_node: Point = left[-1]
    right_node: Point = right[0]



    # If the left or right point can step up
    while (
            turn(left_node.ccwPoint, left_node, right_node) == LEFT_TURN
            or turn(left_node, right_node, right_node.cwPoint) == LEFT_TURN
    ):
        # Step up
        if turn(left_node.ccwPoint, left_node, right_node) == LEFT_TURN:
            previous_points.add(left_node)
            assert left_node.ccwPoint is not None
            left_node = left_node.ccwPoint
        else:
            previous_points.add(right_node)
            assert right_node.cwPoint is not None
            right_node = right_node.cwPoint

    # Save references to points for top segment, to prevent modifying original
    # `l` and `r` points before walk down algorithm occurs.
    topleft = left_node
    topright = right_node

    # Walk down
    left_node = left[-1]
    right_node = right[0]

    # If the left or right point can step down
    while (
            turn(left_node.cwPoint, left_node, right_node) == RIGHT_TURN
            or turn(left_node, right_node, right_node.ccwPoint) == RIGHT_TURN
    ):
        # Step up
        if turn(left_node.cwPoint, left_node, right_node) == RIGHT_TURN:
            previous_points.add(left_node)
            assert left_node.cwPoint is not None
            left_node = left_node.cwPoint
        else:
            previous_points.add(right_node)
            assert right_node.ccwPoint is not None
            right_node = right_node.ccwPoint

    bottom_right = right_node
    bottom_left = left_node

    topleft.cwPoint = topright
    topright.ccwPoint = topleft
    bottom_left.ccwPoint = bottom_right
    bottom_right.cwPoint = bottom_left

    previous_points -= {topright, topleft, bottom_right, bottom_left}

    for point in previous_points:
        point.cwPoint = None
        point.ccwPoint = None

    # You can do the following to help in debugging.  This highlights
    # all the points, then shows them, then pauses until you press
    # 'p'.  While paused, you can click on a point and its coordinates
    # will be printed in the console window.  If you are using an IDE
    # in which you can inspect your variables, this will help you to
    # identify which point on the screen is which point in your data
    # structure.
    #
    # This is good to do, for example, after you have recursively
    # built two hulls, to see that the two hulls look right.
    #
    # This can also be done immediately after you have merged to hulls
    # ... again, to see that the merged hull looks right.
    #
    # Always after you have inspected things, you should remove the
    # highlighting from the points that you previously highlighted.

    for p in points:
        p.highlight = True
    display(wait=True)

    # At the very end of buildHull(), you should display the result
    # after every merge, as shown below.  This call to display() does
    # not pause.

    display()


windowLeft = None
windowRight = None
windowTop = None
windowBottom = None


# Set up the display and draw the current image

def display(wait=False):
    global lastKey, windowLeft, windowRight, windowBottom, windowTop

    # Handle any events that have occurred

    glfw.poll_events()

    # Set up window

    glClearColor(1, 1, 1, 0)
    glClear(GL_COLOR_BUFFER_BIT)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    windowLeft = -0.1 * (maxX - minX) + minX
    windowRight = 1.1 * (maxX - minX) + minX
    windowTop = 1.1 * (maxY - minY) + minY
    windowBottom = -0.1 * (maxY - minY) + minY

    glOrtho(windowLeft, windowRight, windowBottom, windowTop, 0, 1)

    # Draw points and hull

    for p in allPoints:
        p.drawPoint()

    # Show window

    glfw.swap_buffers(window)

    # Maybe wait until the user presses 'p' to proceed

    if wait:

        sys.stderr.write('Press "p" to proceed ')
        sys.stderr.flush()

        lastKey = None
        while lastKey != 80:  # wait for 'p'
            glfw.wait_events()
            if glfw.window_should_close(window):
                sys.exit(0)
            display()

        sys.stderr.write('\r                     \r')
        sys.stderr.flush()


# Handle keyboard input

def keyCallback(window, key, scancode, action, mods):
    global lastKey

    if action == glfw.PRESS:

        if key == glfw.KEY_ESCAPE:  # quit upon ESC
            glfw.set_window_should_close(window, GL_TRUE)
        else:
            lastKey = key


# Handle window reshape


def windowReshapeCallback(window, newWidth, newHeight):
    global windowWidth, windowHeight

    windowWidth = newWidth
    windowHeight = newHeight


# Handle mouse click/release

def mouseButtonCallback(window, btn, action, keyModifiers):
    if action == glfw.PRESS:

        # Find point under mouse

        x, y = glfw.get_cursor_pos(window)  # mouse position

        wx = (x - 0) / float(windowWidth) * (windowRight - windowLeft) + windowLeft
        wy = (windowHeight - y) / float(windowHeight) * (windowTop - windowBottom) + windowBottom

        minDist = windowRight - windowLeft
        minPoint = None
        for p in allPoints:
            dist = math.sqrt((p.x - wx) * (p.x - wx) + (p.y - wy) * (p.y - wy))
            if dist < r and dist < minDist:
                minDist = dist
                minPoint = p

        # print point and toggle its highlight

        if minPoint:
            minPoint.highlight = not minPoint.highlight
            print(minPoint)


# Initialize GLFW and run the main event loop

def main():
    global window, allPoints, minX, maxX, minY, maxY, r, discardPoints

    # Check command-line args

    if len(sys.argv) < 2:
        print('Usage: %s filename' % sys.argv[0])
        sys.exit(1)

    args = sys.argv[1:]
    while len(args) > 1:
        print(args)
        if args[0] == '-d':
            discardPoints = not discardPoints
        args = args[1:]

    # Set up window

    if not glfw.init():
        print('Error: GLFW failed to initialize')
        sys.exit(1)

    window = glfw.create_window(windowWidth, windowHeight, "Assignment 1", None, None)

    if not window:
        glfw.terminate()
        print('Error: GLFW failed to create a window')
        sys.exit(1)

    glfw.make_context_current(window)
    glfw.swap_interval(1)
    glfw.set_key_callback(window, keyCallback)
    glfw.set_window_size_callback(window, windowReshapeCallback)
    glfw.set_mouse_button_callback(window, mouseButtonCallback)

    # Read the points

    with open(args[0], 'rb') as f:
        allPoints = [Point(line.split(b' ')) for line in f.readlines()]

    # Get bounding box of points

    minX = min(p.x for p in allPoints)
    maxX = max(p.x for p in allPoints)
    minY = min(p.y for p in allPoints)
    maxY = max(p.y for p in allPoints)

    # Adjust point radius in proportion to bounding box

    if maxX - minX > maxY - minY:
        r *= maxX - minX
    else:
        r *= maxY - minY

    # Sort by increasing x.  For equal x, sort by increasing y.

    allPoints.sort(key=lambda p: (p.x, p.y))

    # Run the code

    buildHull(allPoints)

    # Wait to exit

    while not glfw.window_should_close(window):
        glfw.wait_events()

    glfw.destroy_window(window)
    glfw.terminate()


if __name__ == '__main__':
    main()

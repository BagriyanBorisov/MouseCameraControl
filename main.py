import cv2 as cv2
import ctypes
import time
import os
import numpy as np
from datetime import datetime
import utils
import HandTracking as ht
import gestureControl as gc
import visualFeedback as vf


#Variable to use on the cam
controlMovement = gc.GestureControl()
user32 = ctypes.windll.user32
WIDTH_SCREEN, HEIGHT_SCREEN = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
wCam, hCam = 640, 360
BORDER_PADDING = 25

#Hand variables
TWO_FINGERSs = [0,1,1,0,0]
TWO_FINGERS = [1,1,1,0,0]
THREE_FINGERS = [1,1,1,1,0]
FOUR_FINGERS = [1,1,1,1,1]
CLOSED_HAND = [0,0,0,0,0]
INDEX_FINGER = 8

PATH = utils.create_path()

def smooth_mouse_move(x_start, y_start, x_end, y_end, duration=0.05, steps=5):
    """
    Move mouse smoothly from (x_start, y_start) to (x_end, y_end) in small steps.
    - duration: total time to move
    - steps: number of steps to divide movement
    """
    dx = (x_end - x_start) / steps
    dy = (y_end - y_start) / steps
    for i in range(steps):
        new_x = x_start + dx * (i + 1)
        new_y = y_start + dy * (i + 1)
        ctypes.windll.user32.SetCursorPos(int(new_x), int(new_y))
        time.sleep(duration / steps)

def mouse_click(x, y):
    """
    Move to (x, y) and perform a left click using Windows API.
    """
    ctypes.windll.user32.SetCursorPos(int(x), int(y))
    ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)  # Mouse left button down
    ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)  # Mouse left button up


def mouse_scroll(vertical_amount=0, horizontal_amount=0):
    """
    Scroll mouse using Windows API.
    vertical_amount > 0 -> scroll up
    vertical_amount < 0 -> scroll down
    horizontal_amount -> sideways scroll (optional)
    """
    MOUSEEVENTF_WHEEL = 0x0800
    MOUSEEVENTF_HWHEEL = 0x01000

    if vertical_amount != 0:
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, int(vertical_amount), 0)

    if horizontal_amount != 0:
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_HWHEEL, 0, 0, int(horizontal_amount), 0)


def mouse_down(x, y):
    """
    Press left mouse button down at (x, y)
    """
    ctypes.windll.user32.SetCursorPos(int(x), int(y))
    ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)  # Left button down

def mouse_up(x, y):
    """
    Release left mouse button at (x, y)
    """
    ctypes.windll.user32.SetCursorPos(int(x), int(y))
    ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)  # Left button up

print("Hello")
def virtual_mouse():
    pTime = 0
    smooth_factor = 3  # Bigger = smoother, Slower mouse reaction
    prev_x3, prev_y3 = 0, 0  # Start previous smoothed position
    prev_x, prev_y = 0, 0
    dragging = False
    mode = "MOVE"
    x3, y3, cx, cy = 0, 0, 0, 0
    clicked = 0
    

    # Setting camera
    capCam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    capCam.set(3, wCam)
    capCam.set(4, hCam)
    # capCam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    """Setting hand recognition based on Mediapipe from Google"""
    handTracking = ht.HandDetector(modelComplexity=0, detectionCon=0.5, trackCon=0.5)
    lastPositionY = 0

    while True:
        (success, img) = capCam.read()
        if not success:
            print("Ignoring empty camera frame.")
            continue
        
        img = cv2.flip(img, 1)
        cv2.rectangle(img, (BORDER_PADDING, BORDER_PADDING), (wCam - BORDER_PADDING , hCam - BORDER_PADDING ), (255, 0, 255), 2)
        
        img = handTracking.findHands(img, draw=True)
        imgList, handBox = handTracking.findPositionFingers(img, draw=True)

        up = False
        down = False

        vf.draw_mode(img, mode)

        if len(imgList) != 0:
            handArea = utils.get_area_box(handBox)

            cv2.putText(img, f'Hand Area: {handArea}', (100, 440), cv2.FONT_HERSHEY_COMPLEX, 0.9, (255, 0, 0), 1)
            xCenter, yCenter = utils.get_center_rectangle(handBox)
            fingerUp = handTracking.fingersUp()
            
            if(lastPositionY > yCenter):
                up = True
                lastPositionY = yCenter
            if(lastPositionY < yCenter):
                down = True
                lastPositionY = yCenter

            if fingerUp == THREE_FINGERS:
                if up:
                    mouse_scroll(150)
                    mode = "SCROLL"
                    up = False    
                elif down:
                    mouse_scroll(-150)
                    mode = "SCROLL"
                    down = False
            else:
                if not dragging:
                    mode = "MOVE"

            # Always move
            x, y = imgList[INDEX_FINGER][1], imgList[INDEX_FINGER][2]
            x3 = np.interp(x, (BORDER_PADDING, wCam - BORDER_PADDING), (0, WIDTH_SCREEN))
            y3 = np.interp(y, (BORDER_PADDING, hCam - BORDER_PADDING), (0, HEIGHT_SCREEN))

            smoothed_x = prev_x3 + (x3 - prev_x3) / smooth_factor
            smoothed_y = prev_y3 + (y3 - prev_y3) / smooth_factor

            prev_x3, prev_y3 = smoothed_x, smoothed_y

            x1, y1 = imgList[4][1], imgList[4][2]  # Thumb tip
            x2, y2 = imgList[8][1], imgList[8][2]  # Index tip
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            move_threshold = 10  # Pixels before we decide to actually move

            dx = abs(smoothed_x - prev_x)
            dy = abs(smoothed_y - prev_y)

            if dx > move_threshold or dy > move_threshold:  
                smooth_mouse_move(prev_x, prev_y, smoothed_x, smoothed_y, duration=0.05, steps=5)
                prev_x, prev_y = smoothed_x, smoothed_y

                
            # Drag detection based on thumb-index distance
            distance = np.hypot(x2 - x1, y2 - y1)

            drag_threshold = 20

            if distance < drag_threshold and not dragging:
                mouse_down(x3, y3)
                dragging = True
                mode = "DRAG"
            elif distance >= drag_threshold and dragging:
                mouse_up(x3, y3)
                dragging = False
                mode = "MOVE"

            # Click detection based on fingersUp
            fingerUp = handTracking.fingersUp()
            if fingerUp == TWO_FINGERS or fingerUp == TWO_FINGERSs:
                if fingerUp[0] == 1 and clicked < 3:  # Index finger raised
                    mouse_click(x3, y3)
                    mode = "CLICK"
                    clicked += 1
                    fingerUp[0] = 0
                else:
                    mode = "MOVE"
                    clicked = 0
                    
            vf.draw_visual_feedback(img, mode, x2, y2, cx, cy, wCam, hCam)
            #distanceIndexAndMiddleFinger = utils.get_distance(imgList[FINGER], imgList[8])
            #print(f'distance between indexTip and middleTip: {distanceIndexAndMiddleFinger}')
        # Set desired FPS
        desired_fps = 30
        time_per_frame = 1.0 / desired_fps

        # Start timing
        start_time = time.time()

        # Sleep to maintain desired fps
        elapsed_time = time.time() - start_time
        if elapsed_time < time_per_frame:
            time.sleep(time_per_frame - elapsed_time)

        # Measure after everything
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime

        # Draw FPS
        cv2.putText(img, f'FPS: {int(fps)}', (35, 45), cv2.FONT_HERSHEY_SIMPLEX,
            0.6, (255, 0, 0), 2)
        cv2.imshow("Gesture Recognition", img)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

if __name__ == "__main__":
    virtual_mouse()
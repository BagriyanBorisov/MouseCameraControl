import cv2

def draw_mode(img, mode):
    """
    Draws the current mode as HUD text on the screen.
    """
    cv2.putText(img, f'MODE: {mode}', (470, 45),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

def draw_visual_feedback(img, mode, x2, y2, cx=None, cy=None, wCam=None, hCam=None):
    """
    Draws visual feedback depending on the current mode.
    """
    if mode == "MOVE":
        cv2.circle(img, (int(x2), int(y2)), 4, (0, 255, 0), cv2.FILLED)
    elif mode == "DRAG" and cx is not None and cy is not None:
        cv2.circle(img, (cx, cy), 8, (0, 255, 255), cv2.FILLED)
    elif mode == "SCROLL" and wCam is not None and hCam is not None:
        cv2.rectangle(img, (25, 25), (wCam - 25, hCam - 25), (0 , 170, 255), 4)
    elif mode == "CLICK" and wCam is not None and hCam is not None:
        cv2.circle(img, (int(x2), int(y2)), 6, (255, 255, 255), cv2.FILLED)

import cv2
import mediapipe as mp
import numpy as np

class HandDetector:
    def __init__(self, mode=False, maxHands=1, modelComplexity=1, detectionCon=0.5, trackCon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.modelComplexity = modelComplexity
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(self.mode, self.maxHands, self.modelComplexity, 
                                        self.detectionCon, self.trackCon)
        self.mpDraw = mp.solutions.drawing_utils
        self.tipIds = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky tips

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
        return img

    def findPositionFingers(self, img, draw=True):
        self.lmList = []
        bbox = []
        xPositionList = []
        yPositionList = []

        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[0]

            for id, fingerPosition in enumerate(myHand.landmark):
                heightImage, widthImage, _ = img.shape
                xScreen = int(fingerPosition.x * widthImage)
                yScreen = int(fingerPosition.y * heightImage)

                xPositionList.append(xScreen)
                yPositionList.append(yScreen)
                self.lmList.append([id, xScreen, yScreen])

            if xPositionList and yPositionList:
                xmin, xmax = min(xPositionList), max(xPositionList)
                ymin, ymax = min(yPositionList), max(yPositionList)
                bbox = (xmin, ymin, xmax, ymax)

                if draw:
                    cv2.rectangle(img, (bbox[0] - 15, bbox[1] - 15), 
                                       (bbox[2] + 15, bbox[3] + 15), 
                                       (0, 255, 0), 2)
        return self.lmList, bbox

    def fingersUp(self):
        fingers = []

        if len(self.lmList) != 0:
            # Thumb (x axis comparison)
            if self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)

            # Fingers (y axis comparison)
            for id in range(1, 5):
                if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:
                    fingers.append(1)
                else:
                    fingers.append(0)

        return fingers

    def findDistance(self, p1, p2, img=None, draw=True, r=10, t=3):
        """
        Find distance between two points (by id).
        Optionally draw it on the image.
        """
        x1, y1 = self.lmList[p1][1], self.lmList[p1][2]
        x2, y2 = self.lmList[p2][1], self.lmList[p2][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        distance = np.hypot(x2 - x1, y2 - y1)

        if img is not None and draw:
            cv2.circle(img, (x1, y1), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), r, (255, 0, 255), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), t)
            cv2.circle(img, (cx, cy), r, (0, 255, 0), cv2.FILLED)

        return distance, (x1, y1, x2, y2, cx, cy)

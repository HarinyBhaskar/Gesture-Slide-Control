import os
import numpy as np
import cv2
from cvzone.HandTrackingModule import HandDetector
from collections import deque
from screeninfo import get_monitors

# Constants for gestures
gestureThreshold = 150
swipeMinDistance = 80
swipeCooldown = 15
hs, ws = int(120 * 1), int(213 * 1)

# Smoothing parameters
smoothingFactor = 1
plocX, plocY = 0, 0

# Buffer for smoothing
pointerBuffer = deque(maxlen=5)
annotationBuffer = deque(maxlen=5)

# Get the screen resolution of the primary monitor
monitor = get_monitors()[0]  # Assuming we are working with the first monitor
screen_width = monitor.width
screen_height = monitor.height

# Adjust the slide dimensions to the screen resolution
slide_width, slide_height = screen_width, screen_height  # Set slide resolution to match screen

folderPath = "./OutputFolder"
pathImages = sorted(os.listdir(folderPath), key=len)

# Camera settings
cap = cv2.VideoCapture(0)
cap.set(3, 1280)  # Set webcam resolution
cap.set(4, 720)

detectorHand = HandDetector(detectionCon=0.8, maxHands=2)

# Variables
delay = 10
buttonPressed = False
counter = 0
imgNumber = 0
annotations = [[]]
annotationNumber = 0
annotationStart = False
colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (0, 255, 255)]
currentColorIndex = 0
previousX = 0
cooldownCounter = 0

# Zoom Parameters
zoomFactor = 1.0
zoomTargetFactor = 1.0
zoomStep = 0.15
maxZoom = 2.0
minZoom = 1.0
zoomCenter = (slide_width // 2, slide_height // 2)

def smoothenCoordinates(currentX, currentY, prevX, prevY, smoothing):
    return int(prevX + (currentX - prevX) * smoothing), int(prevY + (currentY - prevY) * smoothing)

# Setup the fullscreen window for the slides
cv2.namedWindow("Slides", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("Slides", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

while True:
    success, img = cap.read()
    img = cv2.flip(img, 1)
    pathFullImage = os.path.join(folderPath, pathImages[imgNumber])
    imgCurrent = cv2.imread(pathFullImage)
    
    # Resize the slide image to fit the screen resolution
    imgCurrent = cv2.resize(imgCurrent, (slide_width, slide_height))

    hands, img = detectorHand.findHands(img)
    cv2.line(img, (0, gestureThreshold), (1280, gestureThreshold), (0, 255, 0), 10)

    if hands and not buttonPressed:
        hand = hands[0]
        cx, cy = hand["center"]
        lmList = hand["lmList"]
        fingers = detectorHand.fingersUp(hand)

        if fingers == [1, 1, 1, 1, 1] and cooldownCounter == 0:
            currentX = cx
            if previousX != 0:
                deltaX = currentX - previousX
                if abs(deltaX) >= swipeMinDistance:
                    if deltaX < 0 and imgNumber > 0:
                        imgNumber -= 1
                        annotations = [[]]
                        annotationNumber = 0
                        annotationStart = False
                        cooldownCounter = swipeCooldown
                    elif deltaX > 0 and imgNumber < len(pathImages) - 1:
                        imgNumber += 1
                        annotations = [[]]
                        annotationNumber = 0
                        annotationStart = False
                        cooldownCounter = swipeCooldown
            previousX = currentX
        else:
            previousX = 0

        if fingers == [0, 1, 1, 0, 0]:
            xVal = int(np.interp(lmList[8][0], [0, 1280], [0, 1280]))
            yVal = int(np.interp(lmList[8][1], [0, 720], [0, 720]))
            clocX, clocY = smoothenCoordinates(xVal, yVal, plocX, plocY, smoothingFactor)
            cv2.circle(imgCurrent, (clocX, clocY), 12, colors[currentColorIndex], cv2.FILLED)
            
            plocX, plocY = clocX, clocY

        if fingers == [0, 1, 0, 0, 0]:
            xVal = int(np.interp(lmList[8][0], [0, 1280], [0, 1280]))
            yVal = int(np.interp(lmList[8][1], [0, 720], [0, 720]))
            
            clocX, clocY = smoothenCoordinates(xVal, yVal, plocX, plocY, smoothingFactor)
            
            if not annotationStart:
                annotationStart = True
                annotations.append([])  # Start new annotation
                annotationNumber = len(annotations) - 1
                plocX, plocY = clocX, clocY
            
            if annotationStart:
                annotations[annotationNumber].append((clocX, clocY))
            
            plocX, plocY = clocX, clocY
        else:
            annotationStart = False

        if fingers == [0, 1, 1, 1, 0]:
            if annotations:
                annotations.pop()
                buttonPressed = True
                if not annotations:
                    annotations = [[]]
                    annotationNumber = 0
                else:
                    annotationNumber = len(annotations) - 1

        if fingers == [0, 0, 0, 0, 1]:
            currentColorIndex = (currentColorIndex + 1) % len(colors)
            buttonPressed = True

        if len(hands) == 2:
            hand2 = hands[1]
            fingers2 = detectorHand.fingersUp(hand2)
            
            if fingers == [1, 1, 0, 0, 0] and fingers2 == [1, 1, 0, 0, 0]:
                if zoomTargetFactor < maxZoom:
                    zoomTargetFactor += zoomStep
                    zoomCenter = lmList[8][0], lmList[8][1]
            elif fingers == [1, 0, 0, 0, 1] and fingers2 == [1, 0, 0, 0, 1]:
                if zoomTargetFactor > minZoom:
                    zoomTargetFactor -= zoomStep

    if cooldownCounter > 0:
        cooldownCounter -= 1

    if buttonPressed:
        counter += 1
        if counter > delay:
            counter = 0
            buttonPressed = False

    zoomFactor += (zoomTargetFactor - zoomFactor) * 0.1
    zoomedImage = cv2.resize(imgCurrent, (0, 0), fx=zoomFactor, fy=zoomFactor)
    h_zoomed, w_zoomed, _ = zoomedImage.shape
    x_offset = int(zoomCenter[0] * zoomFactor - slide_width // 2)
    y_offset = int(zoomCenter[1] * zoomFactor - slide_height // 2)
    x_offset = max(0, min(x_offset, w_zoomed - slide_width))
    y_offset = max(0, min(y_offset, h_zoomed - slide_height))
    imgCurrent = zoomedImage[y_offset:y_offset + slide_height, x_offset:x_offset + slide_width]

    for annotation in annotations:
        for j in range(1, len(annotation)):
            cv2.line(imgCurrent, annotation[j - 1], annotation[j], colors[currentColorIndex], 5)

    webcamSmall = cv2.resize(img, (ws, hs))
    h, w, _ = imgCurrent.shape
    imgCurrent[h - hs - 20:h - 20, w - ws - 20:w - 20] = webcamSmall

    cv2.imshow("Slides", imgCurrent) 
    cv2.imshow("Webcam Feed", img)  
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

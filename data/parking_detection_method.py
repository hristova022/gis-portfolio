
# Sample code for parking detection (would run separately)

import cv2
import numpy as np
from ultralytics import YOLO

def detect_parking_spaces(image_path):
    # Load pre-trained YOLO model
    model = YOLO('yolov8n.pt')
    
    # Run detection
    results = model(image_path)
    
    # Filter for cars in parking spaces
    parking_spaces = []
    for result in results:
        boxes = result.boxes
        for box in boxes:
            if box.cls == 2:  # Class 2 is 'car' in COCO dataset
                parking_spaces.append(box.xyxy)
    
    return len(parking_spaces)

# Process multiple timestamps to compare occupancy
morning_occupancy = detect_parking_spaces('downtown_morning.jpg')
evening_occupancy = detect_parking_spaces('downtown_evening.jpg')

occupancy_rate = evening_occupancy / morning_occupancy * 100
print(f"Evening occupancy increase: {occupancy_rate}%")

# utils/image_processor.py
import os
import cv2
import numpy as np
import pytesseract
from datetime import datetime

class ImageProcessor:
    def __init__(self, tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    def capture_screenshot(self, device, screenshot_dir, prefix=""):
        """Capture screenshot to a specific directory with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{prefix}_{timestamp}_{device.id}.png"
        filepath = os.path.join(screenshot_dir, filename)
        device.screencap(filepath)
        return filepath
    
    def preprocess_image(self, filepath, roi, invert=True):
        """Process image for OCR with error handling."""
        img = cv2.imread(filepath)
        if img is None:
            print(f"ERROR: Could not load image {filepath}")
            return np.zeros((roi[3], roi[2]), dtype=np.uint8)
        
        try:
            x, y, w, h = roi
            cropped = img[y:y+h, x:x+w]
            gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
            
            thresh_type = cv2.THRESH_BINARY_INV if invert else cv2.THRESH_BINARY
            _, binary = cv2.threshold(gray, 0, 255, thresh_type + cv2.THRESH_OTSU)
            return binary
        except Exception as e:
            print(f"Error processing image {filepath}: {e}")
            return np.zeros((roi[3], roi[2]), dtype=np.uint8)
    
    def read_text(self, image, config=""):
        """Extract text from image using OCR."""
        return pytesseract.image_to_string(image, config=config).strip()
import os
import sys
import time
import traceback
from typing import List
import requests
import webbrowser
from datetime import date
from ppadb.client import Client
import cv2
import numpy as np
from PIL import Image
import pytesseract
import tkinter as tk
from tkinter import messagebox
import xlwt
import keyboard
from Ldplayer.device import Device
import random
import argparse
from utils import *

version = "RokTracker-v10.1"  # Updated version number to match roktracker
Debug = True
pytesseract.pytesseract.tesseract_cmd = r'D:\Code\rok\scanData\roktrackerRemake\Tesseract-OCR\tesseract.exe'
today = date.today()
Y = [285, 390, 490, 590, 605]  # Positions for governors

def tointcheck(element):
    try:
        return int(element)
    except ValueError:
        return element

def tointprint(element):
    try:
        return f'{int(element):,}'
    except ValueError:
        return str(element)

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def check_for_updates():
    """Check for updates on GitHub repository."""
    try:
        response = requests.get("https://api.github.com/repos/nikolakis1919/RokTracker/releases/latest")
        if (response.json()["name"]) != version:
            bo = tk.Tk()
            bo.withdraw()
            messagebox.showinfo("Tool is outdated", "New version is available on github repository. It is highly recommended to update the tool!")
            bo.destroy()
    except:
        print("Unable to check for updates. Check your internet connection.")

def open_donate_link():
    """Open donation page in browser."""
    webbrowser.open_new(r"https://www.buymeacoffee.com/nikolakis1919")

def open_discord_link():
    """Open Discord invite link in browser."""
    webbrowser.open_new(r"https://discord.gg/CvU96gVfjS")

def create_input_gui(ldplayer_id):
    """Create a GUI for user input."""
    root = tk.Tk()
    root.title('RokTracker for LDPlayer')
    root.geometry("400x350")

    variable = tk.StringVar(root)
    variable2 = tk.IntVar(root)
    var1 = tk.IntVar()
    scan_option_var = tk.IntVar(value=1)  # Default to full scan

    options = [50 + i * 25 for i in range(38)]
    variable2.set(options[0])

    def search():
        if variable.get():
            global kingdom, search_range, resume_scanning, scan_option
            kingdom = variable.get()
            search_range = variable2.get()
            resume_scanning = var1.get()
            scan_option = scan_option_var.get()
            root.destroy()
            print("Scanning Started...")
        else:
            print("You need to fill filename!")
            kingdom_entry.focus_set()

    tk.Label(root, text='Kingdom Name', font=('calibre', 10, 'bold')).grid(row=0, column=0)
    kingdom_entry = tk.Entry(root, textvariable=variable, font=('calibre', 10, 'normal'))
    kingdom_entry.grid(row=0, column=1)
    
    tk.Label(root, text='Search Amount', font=('calibre', 10, 'bold')).grid(row=1, column=0)
    tk.OptionMenu(root, variable2, *options).grid(row=1, column=1)
    
    tk.Checkbutton(root, text="Resume Scan", variable=var1, font=('calibre', 10, 'bold')).grid(row=2, column=1, pady=4)
    
    tk.Label(root, text='Scan Option', font=('calibre', 10, 'bold')).grid(row=3, column=0)
    tk.Radiobutton(root, text="Full Scan", variable=scan_option_var, value=1).grid(row=3, column=1, sticky="w")
    tk.Radiobutton(root, text="Power + Kill Points Only", variable=scan_option_var, value=2).grid(row=4, column=1, sticky="w")
    
    tk.Button(root, text="Start Scan", command=search).grid(row=5, column=1, pady=5)
    tk.Label(root, text=f"LDPlayer ID: {ldplayer_id}", font=('calibre', 10, 'bold')).grid(row=6, column=1, pady=10)
    tk.Label(root, text=u"\u00A9 nikolakis1919", font=('calibre', 10, 'bold')).grid(row=7, column=1, pady=10)
    tk.Button(root, foreground='Green', text='Donate', command=open_donate_link, font=('calibre', 10, 'bold')).grid(row=8, column=1, pady=10)
    tk.Label(root, text='Find me on discord: nikos#4469', font=('calibre', 10, 'bold')).grid(row=9, column=0, columnspan=2, pady=10)
    tk.Button(root, foreground='Blue', text='Join Discord', command=open_discord_link, font=('calibre', 10, 'bold')).grid(row=10, column=1, pady=10)
    
    root.mainloop()
    return kingdom, search_range, resume_scanning, scan_option

def setup_excel(scanOption):
    wb = xlwt.Workbook()
    sheet1 = wb.add_sheet(str(today))
    style = xlwt.XFStyle()
    font = xlwt.Font()
    font.bold = True
    style.font = font
    if scanOption == 1:
        headers = ['Governor Name', 'Governor ID', 'Power', 'Kill Points', 'Deads', 'Tier 1 Kills', 'Tier 2 Kills', 'Tier 3 Kills', 'Tier 4 Kills', 'Tier 5 Kills', 'Rss Assistance', 'Alliance Helps', 'Alliance','KvK Kills High', 'KvK Deads High', 'KvK Severely Wounds High']
    if scanOption == 2:
        headers = ['Governor Name', 'Governor ID', 'Power', 'Kill Points']
    for col, header in enumerate(headers):
        sheet1.write(0, col, header, style)
    return wb, sheet1

def capture_image(device, filename):
    current_path = os.path.dirname(os.path.realpath(__file__))
    screenshot_path = os.path.join(current_path, filename)
    device.screencap(screenshot_path)
    return

def randomize_time(max_time: float):
    """
    Pauses the program execution for a random duration between max_time and 2/3 of max_time.
    
    Parameters:
    max_time (float): The maximum time in seconds.
    """
    lower_limit = max_time * 2 / 3
    sleep_time = random.uniform(lower_limit, max_time)
    time.sleep(sleep_time)

def match_template(image: np.ndarray, template: np.ndarray, method=cv2.TM_CCOEFF_NORMED):
    """
    Match a template in an image and return the best match location and score.

    Parameters:
        image (np.ndarray): The source image.
        template (np.ndarray): The template to search for.
        method (int): Matching method (default: cv2.TM_CCOEFF_NORMED).

    Returns:
        (tuple): center corner of the best match and the matching score.
    """
    try:
        # Perform template matching
        result = cv2.matchTemplate(image, template, method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # Select the best match based on method
        if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
            best_match_loc = min_loc
            score = min_val
        else:
            best_match_loc = max_loc
            score = max_val

        return (best_match_loc[0] + template.shape[1] // 2, best_match_loc[1] + template.shape[0] // 2), score
    except Exception as e:
        print(f"Error during template matching: {str(e)}")
        return None, None

def preprocess_image(filename, roi):
    """
    Reads an image from a file, crops it based on ROI, and preprocesses it for OCR.
    
    Parameters:
        filename: The path to the file containing the image.
        roi: A tuple (x, y, width, height) representing the region of interest.
    
    Returns:
        numpy.ndarray: The preprocessed binary image.
    """
    img = cv2.imread(filename)
    
    # Crop the image based on ROI
    x, y, w, h = roi
    cropped_image = img[y:y+h, x:x+w]
    
    # Convert to grayscale
    gray_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
    
    # Improved preprocessing for better OCR accuracy
    _, binary_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return binary_image

def read_cut_image(image, roi):
    img = cv2.imread(image)
    x, y, w, h = roi
    return img[y:y+h, x:x+w]

def preprocess_image2(filename, roi):
    """
    Reads an image from a file, crops it based on ROI, and preprocesses it for OCR.
    
    Parameters:
        filename: The path to the file containing the image.
        roi: A tuple (x, y, width, height) representing the region of interest.
    
    Returns:
        numpy.ndarray: The preprocessed binary image.
    """
    img = cv2.imread(filename)
    
    # Check if image was loaded successfully
    if img is None:
        print(f"ERROR: Could not load image {filename}. Creating blank image.")
        # Create a blank image with the ROI dimensions as fallback
        blank_img = np.zeros((roi[3], roi[2]), dtype=np.uint8)
        return blank_img
    
    try:
        # Crop the image based on ROI
        x, y, w, h = roi
        cropped_image = img[y:y+h, x:x+w]
        
        # Convert to grayscale
        gray_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
        
        # Improved preprocessing for better OCR accuracy
        _, binary_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        return binary_image
    except Exception as e:
        print(f"Error processing image {filename}: {e}")
        # Create a blank image with the ROI dimensions as fallback
        blank_img = np.zeros((roi[3], roi[2]), dtype=np.uint8)
        return blank_img

def preprocess_image3(filename, roi):
    """
    Reads an image from a file, crops it based on ROI, and preprocesses it for OCR.
    
    Parameters:
        filename: The path to the file containing the image.
        roi: A tuple (x, y, width, height) representing the region of interest.
    
    Returns:
        numpy.ndarray: The preprocessed binary image.
    """
    img = cv2.imread(filename)
    
    # Crop the image based on ROI
    x, y, w, h = roi
    cropped_image = img[y:y+h, x:x+w]
    
    # Convert to grayscale
    gray_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
    
    gray_image = cv2.medianBlur(gray_image, 3)
    _, binary_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    return binary_image

def read_ocr_from_image(image, config=""):
    return pytesseract.image_to_string(image, config=config)

def get_clip_board():
    retry_attempts = 5
    for attempt in range(retry_attempts):
        try:
            root = tk.Tk()
            root.withdraw()  # Hide main Tkinter window
            data = root.clipboard_get()
            root.destroy()
            return data
        except tk.TclError:
            print("Can't access clipboard. Retrying...")
            time.sleep(0.5)  # Wait 0.5 seconds before retrying
    print("Unable to access clipboard after multiple attempts.")
    return "Null"

def print_progress_bar(iteration, total, bar_length=40):
    """Prints a progress bar to the console.
    
    Parameters:
        iteration (int): The current iteration number.
        total (int): The total number of iterations.
        bar_length (int): The length of the progress bar.
    """
    progress = (iteration / total)
    arrow = '=' * int(round(progress * bar_length) - 1)
    spaces = ' ' * (bar_length - len(arrow))
    sys.stdout.write(f'\r[{arrow}{spaces}] {iteration} out of {total} Scanned\n\n')
    sys.stdout.flush()

def format_time(seconds):
    """Helper function to format time in MM:SS format."""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

def main_loop(device,wb, sheet1, kingdom, search_range, resume_scanning, scan_option):
    stop = False

    def onkeypress(event):
        nonlocal stop
        if event.name == '\\':
            print("Your scan will be terminated when current governor scan is over!")
            stop = True

    keyboard.on_press(onkeypress)

    j = 4 if resume_scanning else 0
    try:
        start_time = time.time()
        for i in range(j, search_range + j):
            if stop:
                print("Scan Terminated! Saving the current progress...")
                break

            k = min(i, 4)
            device.shell(f'input tap 690 {Y[k]}')
            randomize_time(1.3)

            # Open governor and ensure the tab is open
            for _ in range(5):
                capture_image(device, f'check_more_info_{device.id}.png')
                check_more_info_image = preprocess_image2(f'check_more_info_{device.id}.png', (170, 775, 116, 29))
                if 'MoreInfo' in read_ocr_from_image(check_more_info_image, "-c tessedit_char_whitelist=MoreInfo"):
                    break
                device.shell(f'input swipe 690 605 690 540')
                device.shell(f'input tap 690 {Y[k]}')
                randomize_time(1.2)
            
            #copy nickname
            device.shell(f'input tap 654 228')
            gov_id_image = preprocess_image2(f'check_more_info_{device.id}.png', (720, 176, 200, 34))
            gov_id = read_ocr_from_image(gov_id_image, "-c tessedit_char_whitelist=0123456789")

            gov_name = get_clip_board()  # Using the improved clipboard function
            
            #read kvk stats
            device.shell(f'input tap 1226 486')
            gov_killpoints_image = preprocess_image2(f'check_more_info_{device.id}.png', (1120, 320, 244, 40))
            gov_killpoints = read_ocr_from_image(gov_killpoints_image, "-c tessedit_char_whitelist=0123456789")
            gov_power_image = preprocess_image2(f'check_more_info_{device.id}.png', (856, 320, 240, 40))
            gov_power = read_ocr_from_image(gov_power_image, "--psm 6 -c tessedit_char_whitelist=0123456789")
            
            # If only basic scan is needed, skip the rest
            if scan_option == 2:
                print(f'Governor ID: {gov_id}\nGovernor Name: {gov_name}\nGovernor Power: {tointprint(gov_power)}\nGovernor Killpoints: {tointprint(gov_killpoints)}')
                
                # Update progress bar
                print_progress_bar(i + 1 - j, search_range)
                randomize_time(0.3)
                
                device.shell(f'input tap 1453 88')  # close governor info
                
                # Write basic data to Excel
                sheet1.write(i - j + 1, 0, gov_name)
                sheet1.write(i - j + 1, 1, tointcheck(gov_id))
                sheet1.write(i - j + 1, 2, tointcheck(gov_power))
                sheet1.write(i - j + 1, 3, tointcheck(gov_killpoints))
                
                # ETA calculation
                elapsed_time = time.time() - start_time
                loops_completed = i + 1 - j
                remaining_loops = search_range - loops_completed
                average_time_per_loop = elapsed_time / loops_completed
                estimated_remaining_time = remaining_loops * average_time_per_loop
                estimated_remaining_minutes = estimated_remaining_time / 60
                print(f"Time running: {elapsed_time:.2f}s | Estimated remaining time: {estimated_remaining_minutes:.2f} mins\n")
                print('----------------------------------------------------------------\n')
                
                randomize_time(1)
                continue
            
            # Full scan continues here
            randomize_time(0.3)
            capture_image(device, f'kvk_stats_{device.id}.png')
            gov_kills_high_image = preprocess_image(f'kvk_stats_{device.id}.png', (1000, 380, 180, 50))
            gov_kills_high = read_ocr_from_image(gov_kills_high_image, "--psm 6 -c tessedit_char_whitelist=0123456789")
            
            alliance_tag_image = preprocess_image(f'check_more_info_{device.id}.png', (580, 320, 250, 40))
            alliance_tag = read_ocr_from_image(alliance_tag_image)

            gov_deads_high_image = preprocess_image(f'kvk_stats_{device.id}.png', (1020, 460 , 200, 35))
            gov_deads_high = read_ocr_from_image(gov_deads_high_image, "-c tessedit_char_whitelist=0123456789")

            for _ in range(2):
                randomize_time(0.6)
                device.shell(f'input tap 1174 304')
                
            gov_sevs_high_image = preprocess_image(f'kvk_stats_{device.id}.png', (1020, 510 , 200, 35))
            gov_sevs_high = read_ocr_from_image(gov_sevs_high_image, "-c tessedit_char_whitelist=0123456789")
            randomize_time(0.2)
            capture_image(device, f'kills_tier_{device.id}.png')
            device.shell(f'input tap 226 724')
            
            kills_tiers = []
            for y in range(420, 620, 45):
                kills_tiers_image = preprocess_image(f'kills_tier_{device.id}.png', (916, y, 215, 26))
                kills_tiers.append(read_ocr_from_image(kills_tiers_image, "--psm 6 -c tessedit_char_whitelist=0123456789"))
            randomize_time(0.3)
            capture_image(device, f'more_info_{device.id}.png')
            gov_dead_image = preprocess_image3(f'more_info_{device.id}.png', (1130, 443, 183, 40))
            gov_dead = read_ocr_from_image(gov_dead_image, "--psm 6 -c tessedit_char_whitelist=0123456789")

            gov_rss_assistance_image = preprocess_image3(f'more_info_{device.id}.png', (1130, 668, 183, 40))
            gov_rss_assistance = read_ocr_from_image(gov_rss_assistance_image, "--psm 6 -c tessedit_char_whitelist=0123456789")

            device.shell(f'input tap 1396 58') #close more info
            
            gov_helps_image = preprocess_image3(f'more_info_{device.id}.png', (1148, 732, 164, 44))
            gov_alliance_helps = read_ocr_from_image(gov_helps_image, "--psm 6 -c tessedit_char_whitelist=0123456789")

            print(f'Governor ID: {gov_id}\nGovernor Name: {gov_name}\nGovernor Power: {tointprint(gov_power)}\nGovernor Killpoints: {tointprint(gov_killpoints)}\nTier 1 kills: {tointprint(kills_tiers[0])}\nTier 2 kills: {tointprint(kills_tiers[1])}\nTier 3 kills: {tointprint(kills_tiers[2])}\nTier 4 kills: {tointprint(kills_tiers[3])}\nTier 5 kills: {tointprint(kills_tiers[4])}\nGovernor Deads: {tointprint(gov_dead)}\nGovernor RSS Assistance: {tointprint(gov_rss_assistance)}\nGovernor Alliance Helps: {tointprint(gov_alliance_helps)}\nGovernor Alliance: {alliance_tag}\nGovernor KvK High Kill: {tointprint(gov_kills_high)}\nGovernor KvK High Deads: {tointprint(gov_deads_high)}\nGovernor KvK High Severely Wounded: {tointprint(gov_sevs_high)}')
            
            # Update progress bar
            print_progress_bar(i + 1 - j, search_range)
            randomize_time(0.3)
            
            device.shell(f'input tap 1453 88') #close governor info
            # Write data to Excel
            sheet1.write(i - j + 1, 0, gov_name)
            sheet1.write(i - j + 1, 1, tointcheck(gov_id))
            sheet1.write(i - j + 1, 2, tointcheck(gov_power))
            sheet1.write(i - j + 1, 3, tointcheck(gov_killpoints))
            sheet1.write(i - j + 1, 4, tointcheck(gov_dead))
            sheet1.write(i - j + 1, 5, tointcheck(kills_tiers[0]))
            sheet1.write(i - j + 1, 6, tointcheck(kills_tiers[1]))
            sheet1.write(i - j + 1, 7, tointcheck(kills_tiers[2]))
            sheet1.write(i - j + 1, 8, tointcheck(kills_tiers[3]))
            sheet1.write(i - j + 1, 9, tointcheck(kills_tiers[4]))
            sheet1.write(i - j + 1, 10, tointcheck(gov_rss_assistance))
            sheet1.write(i - j + 1, 11, tointcheck(gov_alliance_helps))
            sheet1.write(i - j + 1, 12, alliance_tag)
            sheet1.write(i - j + 1, 13, tointcheck(gov_kills_high))
            sheet1.write(i - j + 1, 14, tointcheck(gov_deads_high))
            sheet1.write(i - j + 1, 15, tointcheck(gov_sevs_high))

            #ETA
            elapsed_time = time.time() - start_time
            loops_completed = i + 1 - j
            remaining_loops = search_range - loops_completed
            average_time_per_loop = elapsed_time / loops_completed
            estimated_remaining_time = remaining_loops * average_time_per_loop
            estimated_remaining_minutes = estimated_remaining_time / 60
            print(f"Time running: {elapsed_time:.2f}s | Estimated remaining time: {estimated_remaining_minutes:.2f} mins\n")
            print('----------------------------------------------------------------\n')

            randomize_time(1)
            
    except Exception as e:
        print('An issue has occurred. Please rerun the tool and use "resume scan option" from where tool stopped. If issue seems to remain, please contact me on discord!')
        print(f"Error details: {str(e)}")
        #Save the excel file in the following format e.g. TOP300-2021-12-25-1253.xls or NEXT300-2021-12-25-1253.xls
        traceback.print_exc()
    
    if resume_scanning:
        file_name_prefix = 'NEXT'
    else:
        file_name_prefix = 'TOP'
    
    wb.save(f'Governor_Scan_{file_name_prefix}-{search_range-j}_{kingdom}_{today}.xls')
    print("Governor Scan Completed.")

def main():
    """Main function to run the application."""
    parser = argparse.ArgumentParser(description='RokTracker for LDPlayer')
    parser.add_argument('--id', type=int, required=True, help='LDPlayer instance ID')
    parser.add_argument('--cli', action='store_true', help='Use command line interface instead of GUI')
    
    args = parser.parse_args()
    
    # Check for updates
    check_for_updates()
    
    ldplayer_id = args.id
    device = Device(ldplayer_id, r'C:\LDPlayer\LDPlayer4.0')
    
    if args.cli:
        # Command line interface option
        kd = input("Enter the kingdom name: ")
        search_range = int(input("Enter the search range: "))
        resume_scanning = int(input("Enter 1 to resume scanning from where it stopped, 0 to start from beginning: "))
        print("""
        Choose scan option:
            1. Full scan
            2. Power + Kill Points only
        """)
        scan_option = int(input("Enter the scan option: "))
    else:
        # GUI interface
        kd, search_range, resume_scanning, scan_option = create_input_gui(ldplayer_id)
    
    wb, sheet1 = setup_excel(scanOption=scan_option)
    # Corrected parameter order
    main_loop(device, wb, sheet1, kd, search_range, resume_scanning, scan_option)

if __name__ == "__main__":
    main()
from playwright.sync_api import sync_playwright
import tkinter as tk
from tkinter import messagebox
import os
import schedule
import time
from datetime import datetime

# Suppress Tk deprecation warning
os.environ["TK_SILENCE_DEPRECATION"] = "1"

# Parking constants
START_DATE = "2025-12-12"
END_DATE = "2026-1-12"
START_TIME = "09:00"
END_TIME = "09:00"
PARKING_SITE_URL = "https://parken.munich-airport.de/book/MUC/Parking?parkingCmd=collectParkingDetails"
SPOT_NAME = "Economy Parken Nord P44 Parkhaus"
START_DATE_UI = datetime.strptime(START_DATE, "%Y-%m-%d").strftime("%d.%m.%Y")
END_DATE_UI = datetime.strptime(END_DATE, "%Y-%m-%d").strftime("%d.%m.%Y")

def send_gui_alert(spot_name, price="Unknown"):
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(
            "Parking Spot Found!",
            f"{spot_name} is available for {START_DATE_UI} to {END_DATE_UI}, {START_TIME}-{END_TIME}.\nPrice: {price}\nBook now: {PARKING_SITE_URL}"
        )
        root.destroy()
        print(f"GUI alert displayed for {spot_name} with price: {price}")
    except Exception as e:
        print(f"Failed to display GUI alert: {e}")

def check_parking_availability(page):
    try:
        page.goto(PARKING_SITE_URL, timeout=30000)
    except Exception as e:
        print(f"Error loading page: {e}")
        return False

    try:
        page.wait_for_selector(".cmpboxbtn.cmpboxbtnno", timeout=2000)
        page.click(".cmpboxbtn.cmpboxbtnno")
    except Exception:
        pass

    try:
        page.wait_for_selector("#changeEntryDate", timeout=5000)
        page.evaluate(f'''
            document.getElementById("changeEntryDate").removeAttribute("readonly");
            if (document.getElementById("changeEntryDate")._flatpickr) {{
                document.getElementById("changeEntryDate")._flatpickr.setDate("{START_DATE}", true);
            }}
            document.getElementById("changeEntryDate").value = "{START_DATE_UI}";
        ''')
        page.evaluate(f'''
            document.getElementById("changeExitDate").removeAttribute("readonly");
            if (document.getElementById("changeExitDate")._flatpickr) {{
                document.getElementById("changeExitDate")._flatpickr.setDate("{END_DATE}", true);
            }}
            document.getElementById("changeExitDate").value = "{END_DATE_UI}";
        ''')
        page.select_option("#changeEntryTime", START_TIME)
        page.select_option("#changeExitTime", END_TIME)
    except Exception as e:
        print(f"Error filling form: {e}")
        return False

    try:
        submit_button = page.query_selector(".btn.btn--submit.btn-primary.btn-desktop")
        if submit_button:
            with page.expect_navigation(timeout=10000):
                page.click(".btn.btn--submit.btn-primary.btn-desktop")
            page.wait_for_load_state("networkidle", timeout=10000)
        else:
            print("Submit button not found!")
            return False
    except Exception as e:
        print(f"Error submitting form: {e}")
        return False

    try:
        parking_options = page.query_selector_all(".item")
        for option in parking_options:
            header = option.query_selector(".item__header h2 span")
            if header and SPOT_NAME.lower() in header.inner_text().lower():
                price_element = option.query_selector(".item__price__val")
                price = price_element.inner_text() if price_element else "Unknown"
                send_gui_alert(SPOT_NAME, price)
                return True
        print(f"'{SPOT_NAME}' not found.")
    except Exception as e:
        print(f"Error checking results: {e}")
        return False

    return False

def job():
    print(f"Starting check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()
        result = check_parking_availability(page)
        print("Search completed:", result)
        context.close()
        browser.close()
        if result:
            print("Spot found, stopping scheduler.")
            return schedule.CancelJob
        return None

def main():
    schedule.every(1).hours.do(job)
    print(f"Scheduler started. Next run at {schedule.next_run().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Checking availability for {START_DATE_UI} to {END_DATE_UI}, {START_TIME}-{END_TIME}")

    if job():
        print("Spot found on first run. Stopping scheduler.")
        return

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("Scheduler stopped manually.")

if __name__ == "__main__":
    main()

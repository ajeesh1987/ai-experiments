import json
import os
from datetime import datetime
from playwright.sync_api import sync_playwright
import tkinter as tk
from tkinter import messagebox

# Suppress Tkinter deprecation warning
os.environ["TK_SILENCE_DEPRECATION"] = "1"

# GUI alert function
def send_gui_alert(title, message):
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(title, message)
    root.destroy()

# Load configuration from config.json
def load_config():
    try:
        with open("config.json", "r") as f:
            return json.load(f)["bookings"]
    except (FileNotFoundError, KeyError) as e:
        print(f"Error loading config.json: {e}")
        exit(1)

# Click an element with retries (accepts selector string or ElementHandle)
def click_with_retry(page, target, timeout=5000, retries=2):
    for attempt in range(retries):
        try:
            if isinstance(target, str):  # If target is a selector string
                element = page.wait_for_selector(target, timeout=timeout)
            else:  # If target is an ElementHandle
                element = target
            element.scroll_into_view_if_needed()
            element.click(force=True)
            return True
        except Exception as e:
            print(f"Click attempt {attempt + 1}/{retries} failed: {e}")
    raise Exception(f"Failed to click element after {retries} retries")

# Handle cookie popup
def handle_cookies(page):
    cookie_selectors = [
        "button#onetrust-accept-btn-handler",
        "button:has-text('Accept All Cookies')",
        "button[class*='accept']",
    ]
    for selector in cookie_selectors:
        try:
            click_with_retry(page, selector, timeout=5000)
            return
        except:
            continue

# Scrape Vue website for movie availability
def scrape_myvue(page, booking):
    url = booking["url"]
    preferences = booking["preferences"]
    booking_type = booking["type"]

    page.goto(url, timeout=60000, wait_until="networkidle")
    handle_cookies(page)

    # Step 1: Select theater
    click_with_retry(page, "button[data-test='dropdown-opener'] span:has-text('VENUE')")
    theater_selector = f"ul.venue-selector-dropdown-content li.dropdown-item:has-text('{preferences['theater']}')"
    click_with_retry(page, theater_selector)

    # Step 2: Search and select movie
    click_with_retry(page, "[data-test='quick-book-film-selector'] button[data-test='dropdown-opener']")
    page.fill("[data-test='quick-book-dropdown-search-input']", preferences["movie_title"])
    page.wait_for_timeout(2000)

    film_container = "[data-test='quick-book-film-selector'] ul[class*='items-selector-content']"
    film_items = page.query_selector_all(f"{film_container} li[class*='items-selector-content__item']")
    target_movie = preferences["movie_title"].lower()
    for item in film_items:
        movie_text = item.inner_text().strip().lower()
        if target_movie in movie_text or f"{target_movie} (hindi)" in movie_text:
            click_with_retry(page, item)
            break
    else:
        print(f"Movie {preferences['movie_title']} not found")
        return False

    # Step 3: Check date dropdown
    click_with_retry(page, "[data-test='quick-book-date-selector'] button[data-test='dropdown-opener']")
    date_items = page.query_selector_all("[data-test='quick-book-date-selector'] ul[class*='items-selector-content'] li[class*='items-selector-content__item']")
    available_dates = [item.inner_text().strip() for item in date_items if item.inner_text().strip()]
    
    if available_dates:
        send_gui_alert(
            f"{booking_type.capitalize()} Booking Available!",
            "Movie booking has opened, check showtimes and book."
        )
        print("GUI alert sent: Movie booking has opened, check showtimes and book.")
        return True
    else:
        print(f"No dates available for {preferences['movie_title']} at {preferences['theater']}")
        return False

def main():
    print(f"Starting check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    bookings = load_config()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        try:
            for booking in bookings:
                if booking["type"] != "movie":
                    continue
                result = scrape_myvue(page, booking)
                print(f"Search completed: {result}")
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    main()
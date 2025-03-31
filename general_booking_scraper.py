import tkinter as tk
from tkinter import messagebox
from playwright.sync_api import sync_playwright
from datetime import datetime
import json
import time

# Suppress Tk deprecation warning
import os
os.environ["TK_SILENCE_DEPRECATION"] = "1"

def get_user_input():
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        print("Loaded inputs from config.json:")
        print(json.dumps(config, indent=4))
        return {
            "type": config["booking_type"],
            "url": config["booking_url"],
            "preferences": {
                "movie_title": config["movie_title"],
                "show_date": config["show_date"],
                "show_time": config["show_time"],
                "theater": config["preferred_theater"]
            }
        }
    except FileNotFoundError:
        print("Welcome to the General Booking Scraper!")
        booking_type = input("Enter the booking type (e.g., movie, flight, parking): ").strip().lower()
        
        if booking_type != "movie":
            print("Sorry, only 'movie' is supported right now. Exiting.")
            exit(1)

        url = input("Enter the movie booking site URL (e.g., https://example-movies.com/book): ").strip()
        movie_title = input("Enter the movie title (e.g., Dune: Part Two): ").strip()
        show_date = input("Enter the show date (YYYY-MM-DD, e.g., 2025-12-12): ").strip()
        show_time = input("Enter the preferred show time (HH:MM, e.g., 19:00): ").strip()
        theater = input("Enter the preferred theater (e.g., AMC Downtown): ").strip()

        return {
            "type": booking_type,
            "url": url,
            "preferences": {
                "movie_title": movie_title,
                "show_date": show_date,
                "show_time": show_time,
                "theater": theater
            }
        }

def send_gui_alert(booking_type, target, details=""):
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(
            f"{booking_type.capitalize()} Found!",
            f"{target} is available.\nDetails: {details}\nBook now at the provided URL."
        )
        root.destroy()
        print(f"GUI alert displayed for {target} with details: {details}")
    except Exception as e:
        print(f"Failed to display GUI alert: {e}")

def find_element(page, selectors, timeout=5000, retries=3, delay=1):
    """Try multiple selectors to find an element with retries."""
    for attempt in range(retries):
        for selector in selectors:
            try:
                page.wait_for_selector(selector, timeout=timeout)
                return selector
            except:
                continue
        print(f"Retry {attempt + 1}/{retries} for selectors: {selectors}")
        time.sleep(delay)
    raise Exception(f"Could not find element with selectors: {selectors} after {retries} retries")

def find_search_bar(page):
    search_selectors = [
        "input[id*='search']",
        "input[class*='search']",
        "input[placeholder*='search' i]",
        "input[aria-label*='search' i]",
        "button[class*='search']",
        "button[aria-label*='search' i]",
        "[data-test*='search']",
        "input[name*='query']",
    ]
    selector = find_element(page, search_selectors)
    return selector

def find_date_picker(page, target_date):
    date_selectors = [
        "select[id*='date']",
        "input[id*='date']",
        "div[class*='date']",
        "[aria-label*='date' i]",
        "[data-test*='date']",
    ]
    selector = find_element(page, date_selectors)
    date_ui = datetime.strptime(target_date, "%Y-%m-%d").strftime("%d %b")
    return selector, date_ui

def find_theater_selector(page, theater_name):
    theater_selectors = [
        "select[id*='venue']",
        "select[id*='theater']",
        "div[class*='venue']",
        "div[class*='theater']",
        "[aria-label*='theater' i]",
        "[data-test*='venue']",
    ]
    selector = find_element(page, theater_selectors)
    return selector

def find_submit_button(page):
    submit_selectors = [
        "button[type='submit']",
        "button[id*='submit']",
        "button[class*='submit']",
        "button[aria-label*='submit' i]",
        "button:has-text('Find')",
        "button:has-text('Search')",
        "button:has-text('Book')",
    ]
    selector = find_element(page, submit_selectors)
    return selector

def scrape_booking_site(page, booking):
    url = booking["url"]
    preferences = booking["preferences"]
    booking_type = booking["type"]

    try:
        page.goto(url, timeout=20000)
    except Exception as e:
        print(f"Error loading page: {e}")
        return False

    # Handle cookie pop-ups (improved for OneTrust)
    try:
        cookie_selectors = [
            "[aria-label*='cookie' i]",
            "[id*='cookie']",
            "[class*='cookie']",
            "button:has-text('Accept')",
            "button:has-text('Agree')",
            "button:has-text('I Accept')",
            "button:has-text('Accept All Cookies')",
            "button:has-text('Allow')",
            "button:has-text('Confirm')",
            "button:has-text('OK')",
            "button#onetrust-accept-btn-handler",
            "button#onetrust-pc-btn-handler",
            "button[class*='accept']",
            "button[class*='agree']",
            "button[class*='ot-btn']",
            "button[id*='accept']",
            "button[role='button'][class*='cookie']",
            "button[class*='save-preference-btn']",  # OneTrust save button
        ]
        cookie_selector = find_element(page, cookie_selectors, timeout=10000, retries=3, delay=2)
        print(f"Found cookie popup button with selector: {cookie_selector}")

        # Try Playwright click first
        try:
            page.click(cookie_selector)
        except Exception as e:
            print(f"Playwright click failed: {e}, trying JavaScript click")
            # Fallback to JavaScript click
            page.evaluate(f"document.querySelector('{cookie_selector}').click()")

        # If we clicked the preferences button, we might need to save or accept
        if "onetrust-pc-btn-handler" in cookie_selector or "save-preference" in cookie_selector:
            save_selectors = [
                "button:has-text('Save')",
                "button:has-text('Accept')",
                "button:has-text('Confirm')",
                "button[class*='save']",
                "button[class*='ot-btn']",
            ]
            save_selector = find_element(page, save_selectors, timeout=3000)
            page.click(save_selector)

        # Wait for the popup to disappear
        page.wait_for_selector(".onetrust-pc-dark-filter", state="hidden", timeout=10000)
        print("Cookie popup dismissed successfully")
    except Exception as e:
        print(f"Failed to handle cookie popup: {e}")
        pass

    # Find and interact with the search bar
    try:
        search_selector = find_search_bar(page)
        if "button" in search_selector:
            page.click(search_selector)
            search_input_selectors = [
                "input[id*='search']",
                "input[class*='search']",
                "input[placeholder*='search' i]",
                "input[aria-label*='search' i]",
            ]
            search_selector = find_element(page, search_input_selectors)
        page.fill(search_selector, preferences["movie_title"])
        page.press(search_selector, "Enter")
    except Exception as e:
        print(f"Error interacting with search bar: {e}")
        return False

    # Find and select the date
    try:
        date_selector, date_ui = find_date_picker(page, preferences["show_date"])
        page.click(f"{date_selector}:has-text('{date_ui}')")
    except Exception as e:
        print(f"Error selecting date: {e}")
        return False

    # Find and select the theater
    try:
        theater_selector = find_theater_selector(page, preferences["theater"])
        page.click(f"{theater_selector}:has-text('{preferences['theater']}')")
    except Exception as e:
        print(f"Error selecting theater: {e}")
        return False

    # Find and click the submit button
    try:
        submit_selector = find_submit_button(page)
        page.click(submit_selector)
        page.wait_for_load_state("networkidle", timeout=8000)
    except Exception as e:
        print(f"Error submitting form: {e}")
        return False

    # Scrape results
    try:
        result_selectors = [
            "div[class*='showtime']",
            "div[class*='ticket']",
            "div[class*='session']",
        ]
        result_selector = find_element(page, result_selectors)
        results = page.query_selector_all(result_selector)
        for result in results:
            movie_element = result.query_selector(f":has-text('{preferences['movie_title']}')")
            time_element = result.query_selector(f":has-text('{preferences['show_time']}')")
            theater_element = result.query_selector(f":has-text('{preferences['theater']}')")

            if (movie_element and preferences["movie_title"].lower() in movie_element.inner_text().lower() and
                time_element and preferences["show_time"] in time_element.inner_text() and
                theater_element and preferences["theater"].lower() in theater_element.inner_text().lower()):
                availability = result.query_selector(":has-text('available')") or result.query_selector("button:has-text('Book')")
                if availability:
                    details = f"{preferences['show_date']} at {preferences['show_time']} in {preferences['theater']}"
                    send_gui_alert(booking_type, preferences["movie_title"], details)
                    return True
        print(f"'{preferences['movie_title']}' not found for {preferences['show_date']} at {preferences['show_time']} in {preferences['theater']}.")
    except Exception as e:
        print(f"Error checking results: {e}")
        return False

    return False

def main():
    print(f"Starting check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    booking = get_user_input()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        print(f"Checking {booking['type']} booking for {booking['preferences']['movie_title']}...")
        result = scrape_booking_site(page, booking)
        print(f"Search completed for {booking['type']}: {result}")
        if result:
            print(f"{booking['type'].capitalize()} found.")

        context.close()
        browser.close()

if __name__ == "__main__":
    main()
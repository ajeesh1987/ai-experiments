import json
import time
import os
from datetime import datetime
from playwright.sync_api import sync_playwright
import tkinter as tk
from tkinter import messagebox

# Suppress Tkinter deprecation warning
os.environ["TK_SILENCE_DEPRECATION"] = "1"

# GUI alert function using tkinter (only for successful finds)
def send_gui_alert(title, message):
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    messagebox.showinfo(title, message)
    root.destroy()

def load_config():
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        print("Loaded config.json:")
        print(json.dumps(config, indent=4))
        return config["bookings"]
    except FileNotFoundError:
        print("config.json not found. Please create it with booking details.")
        exit(1)
    except KeyError:
        print("Invalid config.json format. Expected a 'bookings' key with a list.")
        exit(1)

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

def handle_cookies(page):
    cookie_selectors = [
        "button#onetrust-accept-btn-handler",
        "button:has-text('Accept All Cookies')",
        "button[class*='accept']",
    ]
    try:
        cookie_selector = find_element(page, cookie_selectors, timeout=10000)
        page.click(cookie_selector)
        print("Cookie popup dismissed")
        page.wait_for_timeout(1000)
    except Exception as e:
        print(f"No cookie popup found or failed to dismiss: {e}")

def click_with_retry(page, element, retries=3, delay=1):
    """Click an element with retries to handle pointer interception."""
    for attempt in range(retries):
        try:
            if element:
                element.scroll_into_view_if_needed()
                page.wait_for_timeout(500)
                element.click(force=True)
                return True
            else:
                raise Exception("Element is None")
        except Exception as e:
            print(f"Click attempt {attempt + 1}/{retries} failed: {e}")
            time.sleep(delay)
    raise Exception(f"Failed to click element after {retries} retries")

def normalize_text(text):
    """Normalize text by stripping whitespace and replacing special characters."""
    return text.strip().replace('\u00A0', ' ').replace('\n', ' ')

def scrape_myvue(page, booking):
    global url
    url = booking["url"]
    preferences = booking["preferences"]
    booking_type = booking["type"]

    print(f"Navigating to {url}")
    try:
        page.goto(url, timeout=60000, wait_until="networkidle")
    except Exception as e:
        print(f"Failed to load page: {e}")
        page.goto(url, timeout=60000, wait_until="domcontentloaded")
    handle_cookies(page)

    try:
        # Step 1: Open venue dropdown
        venue_button = find_element(page, ["button[data-test='dropdown-opener'] span:has-text('VENUE')"])
        page.click(venue_button)
        print("Opened venue dropdown")
        page.wait_for_timeout(3000)

        # Ensure dropdown is open
        dropdown_body = find_element(page, ["div.dropdown-body.show"], timeout=10000)
        print("Dropdown body is visible")

        # Target venue items
        venue_container = "ul.venue-selector-dropdown-content"
        venue_items = page.query_selector_all(f"{venue_container} li.dropdown-item:not(.disabled)")
        print("Available venues:")
        available_venues = []
        for item in venue_items:
            venue_text = item.query_selector("span.dropdown-item__value").inner_text().strip()
            if venue_text not in available_venues:
                print(f" - {venue_text}")
                available_venues.append(venue_text)

        # Select theater
        theater = preferences["theater"]
        venue_selector = f"{venue_container} li.dropdown-item:has-text('{theater}')"
        elements = page.query_selector_all(venue_selector)
        if not elements:
            raise Exception("No matching theater found")
        for element in elements:
            if element.is_visible():
                element.scroll_into_view_if_needed()
                page.wait_for_timeout(500)
                element.click(force=True)
                print(f"Selected theater: {theater}")
                break
        else:
            raise Exception("No visible theater option found")

        # Step 2: Open film dropdown
        film_button = find_element(page, ["[data-test='quick-book-film-selector'] button[data-test='dropdown-opener']"])
        page.click(film_button)
        print("Opened film dropdown")
        page.wait_for_timeout(5000)  # Increased wait time for dropdown to load

        # Ensure dropdown is open
        film_dropdown_body = find_element(page, ["[data-test='quick-book-film-selector'] div.dropdown-body.show"], timeout=10000)
        print("Film dropdown body is visible")

        # Debug: List all available movies
        film_container = "[data-test='quick-book-film-selector'] ul[class*='items-selector-content']"
        film_items = page.query_selector_all(f"{film_container} li[class*='items-selector-content__item']")
        print("Available movies:")
        available_movies = []
        for item in film_items:
            movie_text = normalize_text(item.inner_text())
            if movie_text:
                print(f" - {movie_text} (raw: '{item.inner_text()}')")
                available_movies.append(movie_text)

        # Search for movie
        film_input = find_element(page, ["[data-test='quick-book-dropdown-search-input']"])
        page.fill(film_input, preferences["movie_title"])
        page.wait_for_timeout(3000)  # Increased wait for search to filter results

        # Re-check dropdown state
        page.wait_for_selector("[data-test='quick-book-film-selector'] div.dropdown-body.show", timeout=5000)
        print("Film dropdown still open after search")

        # Re-fetch dropdown items after search
        film_items = page.query_selector_all(f"{film_container} li[class*='items-selector-content__item']")
        print("Movies after search:")
        movie_found = False
        for item in film_items:
            movie_text = normalize_text(item.inner_text())
            print(f" - {movie_text} (raw: '{item.inner_text()}')")
            if normalize_text(preferences["movie_title"]).lower() == movie_text.lower():
                click_with_retry(page, item)
                print(f"Selected movie: {movie_text}")
                movie_found = True
                break
        if not movie_found:
            # Fallback: Partial match
            for item in film_items:
                movie_text = normalize_text(item.inner_text())
                if normalize_text(preferences["movie_title"]).lower() in movie_text.lower():
                    click_with_retry(page, item)
                    print(f"Selected movie (partial match): {movie_text}")
                    movie_found = True
                    break
        if not movie_found:
            error_msg = f"Movie {preferences['movie_title']} not found in dropdown. Available movies: {', '.join(available_movies)}"
            print(error_msg)
            return False

        # Step 3: Open date dropdown
        date_button = find_element(page, ["[data-test='quick-book-date-selector'] button[data-test='dropdown-opener']"])
        page.click(date_button)
        print("Opened date dropdown")
        page.wait_for_timeout(1000)

        # Get all available dates
        date_container = "[data-test='quick-book-date-selector'] ul[class*='items-selector-content']"
        date_items = page.query_selector_all(f"{date_container} li[class*='items-selector-content__item']")
        available_dates = []
        for item in date_items:
            date_text = item.inner_text().strip()
            available_dates.append(date_text)
        print("Available dates:")
        for date in available_dates:
            print(f" - {date}")

        # Step 4: Check showtimes for each date
        showtimes_found = False
        showtimes_by_date = {}
        for date_text in available_dates:
            # Select the date with retry
            date_selector = f"{date_container} li[class*='items-selector-content__item']:has-text('{date_text}')"
            date_element = page.query_selector(date_selector)
            try:
                click_with_retry(page, date_element)
                print(f"Selected date: {date_text}")
            except Exception as e:
                print(f"Failed to select date {date_text}: {e}")
                continue

            # Wait for the page to update
            page.wait_for_timeout(2000)

            # Check if time dropdown is enabled
            time_selector_container = "[data-test='quick-book-time-selector']"
            time_button = f"{time_selector_container} button[data-test='dropdown-opener']"
            time_container = page.query_selector(time_selector_container)
            if time_container and "quick-book__list-item-disabled" in time_container.get_attribute("class"):
                print(f"No showtimes available for {date_text} (time dropdown disabled)")
                # Reopen date dropdown for the next iteration
                page.click(date_button, force=True)
                page.wait_for_timeout(1000)
                continue

            # Open time dropdown
            time_element = page.query_selector(time_button)
            try:
                click_with_retry(page, time_element)
                print("Opened time dropdown")
                page.wait_for_timeout(1000)
            except Exception as e:
                print(f"Failed to open time dropdown for {date_text}: {e}")
                # Reopen date dropdown for the next iteration
                page.click(date_button, force=True)
                page.wait_for_timeout(1000)
                continue

            # Get available times
            time_items = page.query_selector_all(f"{time_selector_container} li[class*='items-selector-content__item']")
            available_times = []
            for item in time_items:
                time_text = item.inner_text().strip()
                if time_text:
                    available_times.append(time_text)
            if available_times:
                showtimes_found = True
                showtimes_by_date[date_text] = available_times
                print(f"Showtimes for {date_text}: {', '.join(available_times)}")
            else:
                print(f"No showtimes available for {date_text} (no times listed)")

            # Reopen date dropdown for the next iteration
            page.click(date_button, force=True)
            page.wait_for_timeout(1000)

        # Step 5: Send GUI alert if showtimes are found
        if showtimes_found:
            details = "\n".join([f"{date}: {', '.join(times)}" for date, times in showtimes_by_date.items()])
            send_gui_alert(
                f"{booking_type.capitalize()} Found!",
                f"{preferences['movie_title']} is available at {theater}.\nDetails:\n{details}\nBook now at {url}."
            )
            return True
        else:
            print(f"No showtimes found for {preferences['movie_title']} at {theater}")
            return False

    except Exception as e:
        print(f"Error during scraping: {e}")
        return False

def main():
    print(f"Starting check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    bookings = load_config()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        for booking in bookings:
            if booking["type"] != "movie":
                print(f"Skipping {booking['type']} - only 'movie' supported")
                continue
            print(f"Checking {booking['type']} booking for {booking['preferences']['movie_title']}...")
            result = scrape_myvue(page, booking)
            print(f"Search completed: {result}")
            if result:
                print(f"{booking['type'].capitalize()} found!")

        context.close()
        browser.close()

if __name__ == "__main__":
    main()
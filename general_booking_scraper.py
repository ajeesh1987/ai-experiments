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
        page.wait_for_timeout(5000)

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

        # Search for movie with flexible matching
        film_input = find_element(page, ["[data-test='quick-book-dropdown-search-input']"])
        page.fill(film_input, preferences["movie_title"])
        page.wait_for_timeout(3000)

        # Re-check dropdown state
        page.wait_for_selector("[data-test='quick-book-film-selector'] div.dropdown-body.show", timeout=5000)
        print("Film dropdown still open after search")

        # Re-fetch dropdown items after search
        film_items = page.query_selector_all(f"{film_container} li[class*='items-selector-content__item']")
        print("Movies after search:")
        movie_found = False
        target_movie = preferences["movie_title"].lower()
        for item in film_items:
            movie_text = normalize_text(item.inner_text()).lower()
            print(f" - {movie_text} (raw: '{item.inner_text()}')")
            # Match "Sikandar" with or without "(Hindi)"
            if target_movie in movie_text or f"{target_movie} (hindi)" in movie_text:
                click_with_retry(page, item)
                print(f"Selected movie: {movie_text}")
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

            # Wait for the page to update (increased wait time)
            page.wait_for_timeout(10000)

            # Check for loading state
            loading_selector = "[data-test='quick-book-time-selector'] .loading"
            try:
                page.wait_for_selector(loading_selector, state="detached", timeout=15000)
                print(f"Loading indicator for {date_text} has disappeared")
            except Exception:
                print(f"No loading indicator found or it did not disappear for {date_text}")

            # Wait for and capture the showtime API response
            showtime_api_url_pattern = "*/api/microservice/showings/cinemas?filmId=*"
            try:
                response = page.wait_for_response(showtime_api_url_pattern, timeout=15000)
                response_json = response.json()
                print(f"Showtime API response for {date_text}: {json.dumps(response_json, indent=2)}")
            except Exception as e:
                print(f"Failed to capture showtime API response for {date_text}: {e}")
                response_json = {}

            # Wait longer after API response to ensure DOM updates
            page.wait_for_timeout(10000)

            # Check time dropdown state
            time_selector_container = "[data-test='quick-book-time-selector']"
            time_button = f"{time_selector_container} button[data-test='dropdown-opener']"
            time_container = page.query_selector(time_selector_container)
            if time_container:
                time_classes = time_container.get_attribute("class")
                print(f"Time dropdown classes for {date_text}: {time_classes}")
            else:
                print(f"Time dropdown not found for {date_text}")
                page.click(date_button, force=True)
                page.wait_for_timeout(1000)
                continue

            # Attempt to open time dropdown
            time_element = page.query_selector(time_button)
            try:
                click_with_retry(page, time_element)
                print("Opened time dropdown")
                page.wait_for_timeout(1000)
            except Exception as e:
                print(f"Failed to open time dropdown for {date_text}: {e}")
                if time_container:
                    time_html = time_container.inner_html()
                    print(f"Time dropdown HTML for {date_text}: {time_html}")
                page.click(date_button, force=True)
                page.wait_for_timeout(1000)
                continue

            # Wait for showtimes to load (increased timeout)
            showtime_selector = f"{time_selector_container} li.dropdown-item.items-selector-content__item.time-selector-item"
            for attempt in range(3):
                try:
                    page.wait_for_selector(showtime_selector, timeout=15000)
                    print(f"Showtimes loaded for {date_text}")
                    break
                except Exception:
                    print(f"Attempt {attempt + 1}/3: No showtimes loaded for {date_text} after waiting")
                    page.wait_for_timeout(5000)
            else:
                print(f"No showtimes loaded for {date_text} after all attempts")
                if time_container:
                    time_html = time_container.inner_html()
                    print(f"Time dropdown HTML for {date_text}: {time_html}")
                page.click(date_button, force=True)
                page.wait_for_timeout(1000)
                continue

            # Get available times
            time_items = page.query_selector_all(showtime_selector)
            available_times = []
            for item in time_items:
                start_time_elem = item.query_selector("span.session-time-start")
                start_time = start_time_elem.inner_text().strip() if start_time_elem else "Unknown start time"
                
                session_time_elem = item.query_selector("span.session-time")
                if session_time_elem:
                    session_time_text = session_time_elem.inner_text().strip()
                    time_parts = session_time_text.split(" - ")
                    end_time = time_parts[1].strip() if len(time_parts) > 1 else "Unknown end time"
                else:
                    end_time = "Unknown end time"

                screen_elem = item.query_selector("span.session-screen-name")
                screen = screen_elem.inner_text().strip() if screen_elem else "Unknown screen"

                attributes = []
                language_elem = item.query_selector("span.session-attributes-language span")
                if language_elem:
                    attributes.append(language_elem.inner_text().strip())
                special_elem = item.query_selector("span.session-attributes-special span")
                if special_elem:
                    attributes.append(special_elem.inner_text().strip())
                attributes_str = ", ".join(attributes) if attributes else "No attributes"

                time_info = f"{start_time} - {end_time} ({screen}, {attributes_str})"
                available_times.append(time_info)

            if available_times:
                showtimes_found = True
                showtimes_by_date[date_text] = available_times
                print(f"Showtimes for {date_text}: {', '.join(available_times)}")
            else:
                print(f"No showtimes available for {date_text} (no times listed)")
                if time_container:
                    time_html = time_container.inner_html()
                    print(f"Time dropdown HTML for {date_text}: {time_html}")

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
            print(f"No showtimes found for {preferences['movie_title']} at {theater} from {available_dates[0]} to {available_dates[-1]}")
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

        context.close()
        browser.close()

if __name__ == "__main__":
    main()
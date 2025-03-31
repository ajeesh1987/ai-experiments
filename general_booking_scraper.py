import tkinter as tk
from tkinter import messagebox
from playwright.sync_api import sync_playwright
from datetime import datetime

# Suppress Tk deprecation warning
import os
os.environ["TK_SILENCE_DEPRECATION"] = "1"

def get_user_input():
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

def find_element(page, selectors, timeout=5000):
    """Try multiple selectors to find an element."""
    for selector in selectors:
        try:
            page.wait_for_selector(selector, timeout=timeout)
            return selector
        except:
            continue
    raise Exception(f"Could not find element with selectors: {selectors}")

def find_search_bar(page):
    """Dynamically find the search bar or search icon."""
    # Possible selectors for search bar or icon
    search_selectors = [
        "input[id*='search']",  # ID contains "search"
        "input[class*='search']",  # Class contains "search"
        "input[placeholder*='search' i]",  # Placeholder contains "search" (case-insensitive)
        "input[aria-label*='search' i]",  # Aria-label contains "search"
        "button[class*='search']",  # Button with class containing "search"
        "button[aria-label*='search' i]",  # Button with aria-label containing "search"
        "[data-test*='search']",  # Data-test attribute containing "search"
        "input[name*='query']",  # Input with name containing "query"
    ]
    selector = find_element(page, search_selectors)
    return selector

def find_date_picker(page, target_date):
    """Dynamically find the date picker and select the target date."""
    date_selectors = [
        "select[id*='date']",  # ID contains "date"
        "input[id*='date']",  # ID contains "date"
        "div[class*='date']",  # Class contains "date"
        "[aria-label*='date' i]",  # Aria-label contains "date"
        "[data-test*='date']",  # Data-test attribute containing "date"
    ]
    selector = find_element(page, date_selectors)
    # Format the date for UI (e.g., "12 Dec")
    date_ui = datetime.strptime(target_date, "%Y-%m-%d").strftime("%d %b")
    return selector, date_ui

def find_theater_selector(page, theater_name):
    """Dynamically find the theater selector."""
    theater_selectors = [
        "select[id*='venue']",  # ID contains "venue"
        "select[id*='theater']",  # ID contains "theater"
        "div[class*='venue']",  # Class contains "venue"
        "div[class*='theater']",  # Class contains "theater"
        "[aria-label*='theater' i]",  # Aria-label contains "theater"
        "[data-test*='venue']",  # Data-test attribute containing "venue"
    ]
    selector = find_element(page, theater_selectors)
    return selector

def find_submit_button(page):
    """Dynamically find the submit button."""
    submit_selectors = [
        "button[type='submit']",  # Standard submit button
        "button[id*='submit']",  # ID contains "submit"
        "button[class*='submit']",  # Class contains "submit"
        "button[aria-label*='submit' i]",  # Aria-label contains "submit"
        "button:has-text('Find')",  # Button with text "Find"
        "button:has-text('Search')",  # Button with text "Search"
        "button:has-text('Book')",  # Button with text "Book"
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

    # Handle cookie pop-ups (if any)
    try:
        cookie_selectors = [
            "[aria-label*='cookie' i]",
            "[id*='cookie']",
            "[class*='cookie']",
            "button:has-text('Accept')",
            "button:has-text('Agree')",
        ]
        cookie_selector = find_element(page, cookie_selectors, timeout=1000)
        page.click(cookie_selector)
    except:
        pass

    # Find and interact with the search bar
    try:
        search_selector = find_search_bar(page)
        # If it's a button (e.g., search icon), click it to reveal the input
        if "button" in search_selector:
            page.click(search_selector)
            # Look for the input field that appears
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
        # Try clicking the date if it's a list of dates
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
            movie_element = result.query_selector(":has-text('preferences['movie_title']')")
            time_element = result.query_selector(":has-text('preferences['show_time']')")
            theater_element = result.query_selector(":has-text('preferences['theater']')")

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
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
        "select[name*='date']",
        "input[id*='date']",
        "input[type='date']",
        "div[class*='date']",
        "div[class*='calendar']",
        "div[class*='day']",
        "button[class*='date']",
        "a[class*='date']",
        "[aria-label*='date' i]",
        "[data-test*='date']",
        "div[role='option'][class*='date']",
        "a[role='option'][class*='date']",
        "div[class*='showtime-date']",
        "button[class*='showtime-date']",
    ]
    selector = find_element(page, date_selectors)
    # Try multiple date formats
    date_obj = datetime.strptime(target_date, "%Y-%m-%d")
    date_formats = [
        date_obj.strftime("%d %b"),  # 26 May
        date_obj.strftime("%b %d"),  # May 26
        date_obj.strftime("%d/%m/%Y"),  # 26/05/2025
        date_obj.strftime("%Y-%m-%d"),  # 2025-05-26
        date_obj.strftime("%dth %b"),  # 26th May
        date_obj.strftime("%d %B"),  # 26 May
        date_obj.strftime("%B %d"),  # May 26
        f"{date_obj.day}",  # 26 (for calendar days)
    ]
    return selector, date_formats

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

    # Handle cookie pop-ups
    try:
        cookie_selectors = [
            "button#onetrust-accept-btn-handler",
            "button:has-text('Accept All Cookies')",
            "button:has-text('Accept')",
            "button:has-text('I Accept')",
            "button:has-text('Agree')",
            "button:has-text('Allow')",
            "button:has-text('Confirm')",
            "button:has-text('OK')",
            "button[class*='accept']",
            "button[class*='agree']",
            "button[class*='ot-btn']",
            "button[id*='accept']",
            "button[role='button'][class*='cookie']",
            "[aria-label*='cookie' i]",
            "[id*='cookie']",
            "[class*='cookie']",
            "button#onetrust-pc-btn-handler",
            "button[class*='save-preference-btn']",
        ]
        cookie_selector = find_element(page, cookie_selectors, timeout=10000, retries=3, delay=2)
        print(f"Found cookie popup button with selector: {cookie_selector}")

        button_text = page.evaluate(f"document.querySelector('{cookie_selector}').innerText")
        print(f"Clicked button with text: {button_text}")

        try:
            page.click(cookie_selector)
        except Exception as e:
            print(f"Playwright click failed: {e}, trying JavaScript click")
            page.evaluate(f"document.querySelector('{cookie_selector}').click()")

        if "onetrust-pc-btn-handler" in cookie_selector or "save-preference" in cookie_selector or "cookie-setting" in button_text.lower():
            print("Detected preferences button, looking for save/confirm button")
            save_selectors = [
                "button:has-text('Save')",
                "button:has-text('Accept')",
                "button:has-text('Confirm')",
                "button:has-text('OK')",
                "button[class*='save']",
                "button[class*='ot-btn']",
                "button[class*='confirm']",
                "button[id*='confirm']",
            ]
            save_selector = find_element(page, save_selectors, timeout=5000)
            print(f"Found save/confirm button with selector: {save_selector}")
            page.click(save_selector)

        try:
            page.wait_for_selector(".onetrust-pc-dark-filter", state="hidden", timeout=15000)
            print("Cookie popup dismissed successfully")
        except Exception as e:
            print(f"Overlay still present: {e}, attempting to hide via JavaScript")
            page.evaluate("document.querySelector('.onetrust-pc-dark-filter').style.display = 'none';")
            page.evaluate("document.querySelector('#onetrust-consent-sdk').style.display = 'none';")
            print("Overlay hidden via JavaScript")
    except Exception as e:
        print(f"Failed to handle cookie popup: {e}")
        pass

    # Find and interact with the search bar
    try:
        search_selector = find_search_bar(page)
        if "button" in search_selector:
            page.click(search_selector)
            page.wait_for_timeout(2000)  # Wait for dynamic content

            search_input_selectors = [
                "input[id*='search']",
                "input[class*='search']",
                "input[placeholder*='search' i]",
                "input[aria-label*='search' i]",
                "input[name*='search']",
                "input[type='search']",
            ]
            try:
                search_selector = find_element(page, search_input_selectors, timeout=3000)
                print(f"Found search input directly on page with selector: {search_selector}")
                page.fill(search_selector, preferences["movie_title"])
                page.press(search_selector, "Enter")
            except Exception as e:
                print(f"No search input found directly on page: {e}, trying slider/sidebar mechanism")

                slider_selectors = [
                    "div[class*='slider']",
                    "div[class*='sidebar']",
                    "div[class*='panel']",
                    "div[id*='search']",
                    "div[class*='search']",
                    "div[role='dialog']",
                    "div[class*='overlay']",
                    "div[class*='drawer']",
                ]
                try:
                    slider_selector = find_element(page, slider_selectors, timeout=5000)
                    print(f"Found slider/sidebar with selector: {slider_selector}")
                    slider_input_selectors = [
                        f"{slider_selector} input[id*='search']",
                        f"{slider_selector} input[class*='search']",
                        f"{slider_selector} input[placeholder*='search' i]",
                        f"{slider_selector} input[aria-label*='search' i]",
                        f"{slider_selector} input[name*='search']",
                        f"{slider_selector} input[type='search']",
                        f"{slider_selector} input[type='text']",
                    ]
                    slider_input_selector = find_element(page, slider_input_selectors, timeout=3000)
                    print(f"Found input field in slider with selector: {slider_input_selector}")
                    page.fill(slider_input_selector, preferences["movie_title"])
                    page.press(slider_input_selector, "Enter")
                except Exception as e:
                    print(f"No slider/sidebar input found: {e}, looking for movie list instead")

                    movie_list_selectors = [
                        "div[class*='film']",
                        "div[class*='movie']",
                        "li[class*='film']",
                        "li[class*='movie']",
                        "a[class*='film']",
                        "a[class*='movie']",
                        "[data-test*='film']",
                        "[data-test*='movie']",
                        "div[class*='search-result']",
                        "li[class*='search-result']",
                        "a[class*='search-result']",
                        "div[class*='dropdown']",
                        "li[class*='dropdown']",
                        "a[class*='dropdown']",
                        "div[role='option']",
                        "a[role='option']",
                        "div[class*='item']",
                        "a[class*='item']",
                    ]
                    try:
                        movie_list_selector = find_element(page, movie_list_selectors, timeout=5000)
                        print(f"Found movie list with selector: {movie_list_selector}")
                        movie_elements = page.query_selector_all(movie_list_selector)
                        for element in movie_elements:
                            element_text = element.inner_text().lower()
                            print(f"Checking movie element: {element_text}")
                            if preferences["movie_title"].lower() in element_text:
                                print(f"Found movie: {preferences['movie_title']}")
                                element.click()
                                break
                        else:
                            print(f"Movie '{preferences['movie_title']}' not found in list")
                            return False
                    except Exception as e:
                        print(f"Failed to find movie list: {e}")
                        return False

            # Wait for search results to load after pressing Enter
            page.wait_for_load_state("networkidle", timeout=10000)
    except Exception as e:
        print(f"Error interacting with search bar: {e}")
        return False

    # Find and select the date
    try:
        date_selector, date_formats = find_date_picker(page, preferences["show_date"])
        # Try each date format until a match is found
        for date_ui in date_formats:
            try:
                date_elements = page.query_selector_all(date_selector)
                for element in date_elements:
                    element_text = element.inner_text().lower()
                    print(f"Checking date element: {element_text}")
                    if date_ui.lower() in element_text:
                        print(f"Found date: {date_ui}")
                        element.click()
                        break
                else:
                    continue
                break
            except Exception as e:
                print(f"Failed to find date with format {date_ui}: {e}")
                continue
        else:
            raise Exception(f"Could not find date {preferences['show_date']} in any format")
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
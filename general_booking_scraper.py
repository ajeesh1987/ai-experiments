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

    # Try using the Quick Book section first (e.g., on myvue.com)
    try:
        quick_book_selectors = [
            "div[class*='quick-book']",
            "[data-test*='quick-book']",
        ]
        quick_book_selector = find_element(page, quick_book_selectors, timeout=5000)
        print(f"Found Quick Book section with selector: {quick_book_selector}")

        # Step 1: Select the venue
        try:
            venue_selector_button = find_element(page, ["[data-test='quick-book-venue-selector'] button[data-test='dropdown-opener']"], timeout=3000)
            print(f"Found venue dropdown button with selector: {venue_selector_button}")
            page.click(venue_selector_button)
            venue_selector = find_theater_selector(page, preferences["theater"])
            page.click(f"{venue_selector}:has-text('{preferences['theater']}')")
            print(f"Selected venue: {preferences['theater']}")
        except Exception as e:
            print(f"Error selecting venue: {e}, assuming default venue is already selected")

        # Step 2: Select the film
        try:
            film_selector_button = find_element(page, ["[data-test='quick-book-film-selector'] button[data-test='dropdown-opener']"], timeout=3000)
            print(f"Found film dropdown button with selector: {film_selector_button}")
            page.click(film_selector_button)

            # Look for the search input in the film dropdown
            film_search_input = find_element(page, ["[data-test='quick-book-dropdown-search-input']"], timeout=3000)
            print(f"Found film search input with selector: {film_search_input}")
            page.fill(film_search_input, preferences["movie_title"])

            # Wait for the filtered list and select the movie
            film_item_selector = "li[class*='items-selector-content__item']"
            page.wait_for_timeout(1000)  # Wait for the list to filter
            film_items = page.query_selector_all(film_item_selector)
            for item in film_items:
                item_text = item.inner_text().lower()
                print(f"Checking film item: {item_text}")
                if preferences["movie_title"].lower() in item_text:
                    print(f"Found movie: {preferences['movie_title']}")
                    item.click()
                    break
            else:
                print(f"Movie '{preferences['movie_title']}' not found in Quick Book list, falling back to search bar")
                raise Exception("Movie not found in Quick Book list")
        except Exception as e:
            print(f"Error selecting film in Quick Book: {e}, falling back to search bar")

            # Fallback to search bar/slider mechanism
            try:
                search_selector = find_search_bar(page)
                if "button" in search_selector:
                    page.click(search_selector)
                    page.wait_for_timeout(2000)

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
                            print("Pressed Enter in slider input")

                            result_indicators = [
                                f":has-text('{preferences['movie_title']}')",
                                "div[class*='film']",
                                "div[class*='movie']",
                                "div[class*='search-result']",
                                "div[class*='showtime']",
                            ]
                            try:
                                result_selector = find_element(page, result_indicators, timeout=15000)
                                print(f"Search results loaded, found element with selector: {result_selector}")
                            except Exception as e:
                                print(f"Search results not found after pressing Enter: {e}, trying to click a submit button")
                                submit_selectors = [
                                    f"{slider_selector} button[type='submit']",
                                    f"{slider_selector} button[class*='submit']",
                                    f"{slider_selector} button[class*='search']",
                                    f"{slider_selector} button:has-text('Search')",
                                    f"{slider_selector} button:has-text('Find')",
                                ]
                                try:
                                    submit_selector = find_element(page, submit_selectors, timeout=3000)
                                    print(f"Found submit button in slider with selector: {submit_selector}")
                                    page.click(submit_selector)
                                    result_selector = find_element(page, result_indicators, timeout=15000)
                                    print(f"Search results loaded after clicking submit, found element with selector: {result_selector}")
                                except Exception as e:
                                    print(f"Failed to load search results after clicking submit: {e}")
                                    return False
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
                                        result_selector = find_element(page, result_indicators, timeout=15000)
                                        print(f"Movie details loaded, found element with selector: {result_selector}")
                                        break
                                else:
                                    print(f"Movie '{preferences['movie_title']}' not found in list")
                                    return False
                            except Exception as e:
                                print(f"Failed to find movie list: {e}")
                                return False
            except Exception as e:
                print(f"Error interacting with search bar: {e}")
                return False

        # Step 3: Select the date
        try:
            date_selector_button = find_element(page, ["[data-test='quick-book-date-selector'] button[data-test='dropdown-opener']"], timeout=3000)
            print(f"Found date dropdown button with selector: {date_selector_button}")
            page.click(date_selector_button)

            date_selector, date_formats = find_date_picker(page, preferences["show_date"])
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

        # Step 4: Select the time
        try:
            # Wait for the time dropdown to be enabled after selecting the date
            page.wait_for_timeout(2000)  # Wait for the time dropdown to populate
            time_selector_button = find_element(page, ["[data-test='quick-book-time-selector'] button[data-test='dropdown-opener']"], timeout=5000)
            print(f"Found time dropdown button with selector: {time_selector_button}")

            # Check if the time dropdown is disabled
            is_disabled = page.eval_on_selector(time_selector_button, "el => el.closest('.quick-book__list-item').classList.contains('quick-book__list-item-disabled')")
            if is_disabled:
                print("Time dropdown is still disabled, waiting longer")
                page.wait_for_timeout(3000)  # Wait longer for the dropdown to enable
                is_disabled = page.eval_on_selector(time_selector_button, "el => el.closest('.quick-book__list-item').classList.contains('quick-book__list-item-disabled')")
                if is_disabled:
                    raise Exception("Time dropdown remained disabled after waiting")

            page.click(time_selector_button)

            time_selector, time_formats = find_time_picker(page, preferences["show_time"])
            for time_ui in time_formats:
                try:
                    time_elements = page.query_selector_all(time_selector)
                    for element in time_elements:
                        element_text = element.inner_text().lower()
                        print(f"Checking time element: {element_text}")
                        if time_ui.lower() in element_text:
                            print(f"Found time: {time_ui}")
                            element.click()
                            break
                    else:
                        continue
                    break
                except Exception as e:
                    print(f"Failed to find time with format {time_ui}: {e}")
                    continue
            else:
                raise Exception(f"Could not find time {preferences['show_time']} in any format")
        except Exception as e:
            print(f"Error selecting time: {e}")
            return False

        # Step 5: Click the Search button
        try:
            submit_selector = find_submit_button(page)
            print(f"Found submit button with selector: {submit_selector}")
            page.click(submit_selector)
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception as e:
            print(f"Error submitting Quick Book form: {e}")
            return False

    except Exception as e:
        print(f"Quick Book section not found or failed: {e}, falling back to search bar mechanism")
        # Fallback to search bar/slider mechanism
        try:
            search_selector = find_search_bar(page)
            if "button" in search_selector:
                page.click(search_selector)
                page.wait_for_timeout(2000)

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
                        print("Pressed Enter in slider input")

                        result_indicators = [
                            f":has-text('{preferences['movie_title']}')",
                            "div[class*='film']",
                            "div[class*='movie']",
                            "div[class*='search-result']",
                            "div[class*='showtime']",
                        ]
                        try:
                            result_selector = find_element(page, result_indicators, timeout=15000)
                            print(f"Search results loaded, found element with selector: {result_selector}")
                        except Exception as e:
                            print(f"Search results not found after pressing Enter: {e}, trying to click a submit button")
                            submit_selectors = [
                                f"{slider_selector} button[type='submit']",
                                f"{slider_selector} button[class*='submit']",
                                f"{slider_selector} button[class*='search']",
                                f"{slider_selector} button:has-text('Search')",
                                f"{slider_selector} button:has-text('Find')",
                            ]
                            try:
                                submit_selector = find_element(page, submit_selectors, timeout=3000)
                                print(f"Found submit button in slider with selector: {submit_selector}")
                                page.click(submit_selector)
                                result_selector = find_element(page, result_indicators, timeout=15000)
                                print(f"Search results loaded after clicking submit, found element with selector: {result_selector}")
                            except Exception as e:
                                print(f"Failed to load search results after clicking submit: {e}")
                                return False
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
                                    result_selector = find_element(page, result_indicators, timeout=15000)
                                    print(f"Movie details loaded, found element with selector: {result_selector}")
                                    break
                            else:
                                print(f"Movie '{preferences['movie_title']}' not found in list")
                                return False
                        except Exception as e:
                            print(f"Failed to find movie list: {e}")
                            return False
            except Exception as e:
                print(f"Error interacting with search bar: {e}")
                return False

            # Find and select the date (for fallback path)
            try:
                date_selector, date_formats = find_date_picker(page, preferences["show_date"])
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

            # Find and select the theater (for fallback path)
            try:
                theater_selector = find_theater_selector(page, preferences["theater"])
                page.click(f"{theater_selector}:has-text('{preferences['theater']}')")
            except Exception as e:
                print(f"Error selecting theater: {e}")
                return False

            # Find and click the submit button (for fallback path)
            try:
                submit_selector = find_submit_button(page)
                page.click(submit_selector)
                page.wait_for_load_state("networkidle", timeout=15000)
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
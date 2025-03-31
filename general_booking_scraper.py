{\rtf1\ansi\ansicpg1252\cocoartf2821
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import tkinter as tk\
from tkinter import messagebox\
from playwright.sync_api import sync_playwright\
import schedule\
import time\
from datetime import datetime\
\
# Suppress Tk deprecation warning\
import os\
os.environ["TK_SILENCE_DEPRECATION"] = "1"\
\
def get_user_input():\
    print("Welcome to the General Booking Scraper!")\
    booking_type = input("Enter the booking type (e.g., movie, flight, parking): ").strip().lower()\
    \
    # For now, we only support movie booking\
    if booking_type != "movie":\
        print("Sorry, only 'movie' is supported right now. Exiting.")\
        exit(1)\
\
    url = input("Enter the movie booking site URL (e.g., https://example-movies.com/book): ").strip()\
    movie_title = input("Enter the movie title (e.g., Dune: Part Two): ").strip()\
    show_date = input("Enter the show date (YYYY-MM-DD, e.g., 2025-12-12): ").strip()\
    show_time = input("Enter the preferred show time (HH:MM, e.g., 19:00): ").strip()\
    theater = input("Enter the preferred theater (e.g., AMC Downtown): ").strip()\
\
    return \{\
        "type": booking_type,\
        "url": url,\
        "preferences": \{\
            "movie_title": movie_title,\
            "show_date": show_date,\
            "show_time": show_time,\
            "theater": theater\
        \}\
    \}\
\
def send_gui_alert(booking_type, target, details=""):\
    try:\
        root = tk.Tk()\
        root.withdraw()\
        messagebox.showinfo(\
            f"\{booking_type.capitalize()\} Found!",\
            f"\{target\} is available.\\nDetails: \{details\}\\nBook now at the provided URL."\
        )\
        root.destroy()\
        print(f"GUI alert displayed for \{target\} with details: \{details\}")\
    except Exception as e:\
        print(f"Failed to display GUI alert: \{e\}")\
\
def scrape_booking_site(page, booking):\
    url = booking["url"]\
    preferences = booking["preferences"]\
    booking_type = booking["type"]\
\
    try:\
        page.goto(url, timeout=20000)\
    except Exception as e:\
        print(f"Error loading page: \{e\}")\
        return False\
\
    # Handle cookie pop-ups (if any)\
    try:\
        page.wait_for_selector(".cmpboxbtn.cmpboxbtnno", timeout=1000)\
        page.click(".cmpboxbtn.cmpboxbtnno")\
    except Exception:\
        pass\
\
    # Fill form fields (customize these selectors for the movie booking site)\
    try:\
        # Search for the movie\
        page.wait_for_selector("#movie-search", timeout=3000)  # Replace with actual selector\
        page.fill("#movie-search", preferences["movie_title"])  # Replace with actual selector\
\
        # Select the date\
        show_date_ui = datetime.strptime(preferences["show_date"], "%Y-%m-%d").strftime("%Y-%m-%d")\
        page.evaluate(f'''\
            document.querySelector("#show-date").removeAttribute("readonly");\
            if (document.querySelector("#show-date")._flatpickr) \{\{\
                document.querySelector("#show-date")._flatpickr.setDate("\{preferences["show_date"]\}", true);\
            \}\}\
            document.querySelector("#show-date").value = "\{show_date_ui\}";\
        ''')  # Replace "#show-date" with actual selector\
\
        # Select the theater (if applicable)\
        page.select_option("#theater-select", preferences["theater"])  # Replace with actual selector\
\
        # Submit the search\
        page.click("button[type='submit']")  # Replace with actual selector\
        page.wait_for_load_state("networkidle", timeout=8000)\
    except Exception as e:\
        print(f"Error filling form: \{e\}")\
        return False\
\
    # Scrape results\
    try:\
        results = page.query_selector_all(".showtime")  # Replace with actual selector\
        for result in results:\
            # Check if the movie, date, time, and theater match\
            movie_element = result.query_selector(".movie-title")  # Replace with actual selector\
            time_element = result.query_selector(".show-time")  # Replace with actual selector\
            theater_element = result.query_selector(".theater-name")  # Replace with actual selector\
\
            if (movie_element and preferences["movie_title"].lower() in movie_element.inner_text().lower() and\
                time_element and preferences["show_time"] in time_element.inner_text() and\
                theater_element and preferences["theater"].lower() in theater_element.inner_text().lower()):\
                # Check if tickets are available\
                availability = result.query_selector(".availability")  # Replace with actual selector\
                if availability and "available" in availability.inner_text().lower():\
                    details = f"\{preferences['show_date']\} at \{preferences['show_time']\} in \{preferences['theater']\}"\
                    send_gui_alert(booking_type, preferences["movie_title"], details)\
                    return True\
        print(f"'\{preferences['movie_title']\}' not found for \{preferences['show_date']\} at \{preferences['show_time']\} in \{preferences['theater']\}.")\
    except Exception as e:\
        print(f"Error checking results: \{e\}")\
        return False\
\
    return False\
\
def job():\
    print(f"Starting check at \{datetime.now().strftime('%Y-%m-%d %H:%M:%S')\}")\
    booking = get_user_input()\
    \
    with sync_playwright() as p:\
        browser = p.chromium.launch(headless=True)\
        context = browser.new_context(viewport=\{"width": 1280, "height": 720\})\
        page = context.new_page()\
\
        print(f"Checking \{booking['type']\} booking for \{booking['preferences']['movie_title']\}...")\
        result = scrape_booking_site(page, booking)\
        print(f"Search completed for \{booking['type']\}: \{result\}")\
        if result:\
            print(f"\{booking['type'].capitalize()\} found, stopping scheduler.")\
            return schedule.CancelJob\
\
        context.close()\
        browser.close()\
    return None\
\
def main():\
    schedule.every(1).hours.do(job)\
    print(f"Scheduler started. Next run at \{schedule.next_run().strftime('%Y-%m-%d %H:%M:%S')\}")\
    \
    if job():\
        print("Target found on first run. Stopping scheduler.")\
        return\
\
    try:\
        while True:\
            schedule.run_pending()\
            time.sleep(60)\
    except KeyboardInterrupt:\
        print("Scheduler stopped manually.")\
\
if __name__ == "__main__":\
    main()}
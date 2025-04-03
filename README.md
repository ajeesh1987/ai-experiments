AI Experiments
A collection of Python scripts to automate travel and booking tasks, such as checking parking availability and monitoring movie showtimes.

Project Overview
This repository houses automation scripts I developed to streamline my travel and booking tasks. I make 20-30 bookings yearly and wanted to cut down the hours spent searching for parking spots, flight deals, and movie showtimes. With the help of AI (Grok from xAI), I built scripts to automate these processes. The first script checks parking availability at Munich Airport, runs hourly, and alerts me when my desired spot is available. The second script monitors movie showtimes on the Vue Cinemas website and alerts me when a movie is available for booking. These projects showcase my ability to leverage AI, iterate on feedback, and build practical solutions.

Scripts
parking_alert.py
Automates parking spot checks for Munich Airport.

Features:

Scrapes parking availability for specific dates and times.
Runs hourly using the schedule library.
Displays a GUI alert when the spot ("Economy Parken Nord P44 Parkhaus") is found.
Future Plans:

Add text message alerts for instant notifications.
Expand to flight price monitoring based on airline availability and price criteria.
Potentially enable auto-booking with user confirmation.
general_booking_scraper.py
Automates movie showtime checks on the Vue Cinemas website (https://www.myvue.com/).

Features:

Searches for a specified movie at a chosen Vue theater.
Supports flexible movie name matching (e.g., "final reckoning" matches "Mission Impossible: Final Reckoning").
Displays a GUI alert when the movie is available for booking (e.g., "Sikandar booking has opened, check showtimes and book").
Designed to run once and can be scheduled using a cron job.

Setup:

Install Playwright:
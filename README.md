# AI Experiments

A collection of Python scripts to automate travel and booking tasks, such as checking parking availability and (in the future) monitoring flight prices.

## Project Overview

This repository houses automation scripts I developed to streamline my travel planning. I make 20-30 bookings yearly and wanted to cut down the hours spent searching for parking spots and flight deals. With the help of AI (Grok from xAI), I built a script that checks parking availability at Munich Airport, runs hourly, and alerts me when my desired spot is available. This project showcases my ability to leverage AI, iterate on feedback, and build practical solutions.



## Projects

### `parking_alert.py`
Automates parking spot checks for Munich Airport.

**Features:**
- Scrapes parking availability for specific dates and times.
- Runs hourly using the `schedule` library.
- Displays a GUI alert when the spot ("Economy Parken Nord P44 Parkhaus") is found.

### `general_booking_scraper.py`
Automates movie showtime checks on the Vue Cinemas website (https://www.myvue.com/).


**Features:**
Searches for a specified movie at a chosen Vue theater.
Supports flexible movie name matching (e.g., "final reckoning" matches "Mission Impossible: Final Reckoning").
Displays a GUI alert when the movie is available for booking (e.g., "Sikandar booking has opened, check showtimes and book").
Designed to run once and can be scheduled using a cron job.

**Future Plans:**
- Add text message alerts for instant notifications.
- Expand to flight price monitoring based on airline availability and price criteria.
- Potentially enable auto-booking with user confirmation.

## License
This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Setup


### 1. Clone the Repository and Run script
```bash
git clone https://github.com/damodaje/ai-experiments.git
cd ai-experiments
python3 general_booking_scraper.py


=

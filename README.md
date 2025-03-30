# AI Experiments

A collection of Python scripts to automate travel and booking tasks, such as checking parking availability and (in the future) monitoring flight prices.

## Project Overview

This repository houses automation scripts I developed to streamline my travel planning. I make 20-30 bookings yearly and wanted to cut down the hours spent searching for parking spots and flight deals. With the help of AI (Grok from xAI), I built a script that checks parking availability at Munich Airport, runs hourly, and alerts me when my desired spot is available. This project showcases my ability to leverage AI, iterate on feedback, and build practical solutions.

## Scripts

### `parking_alert.py`
Automates parking spot checks for Munich Airport.

**Features:**
- Scrapes parking availability for specific dates and times.
- Runs hourly using the `schedule` library.
- Displays a GUI alert when the spot ("Economy Parken Nord P44 Parkhaus") is found.

**Future Plans:**
- Add text message alerts for instant notifications.
- Expand to flight price monitoring based on airline availability and price criteria.
- Potentially enable auto-booking with user confirmation.

## Setup

### 1. Clone the Repository
```bash
git clone https://github.com/damodaje/ai-experiments.git
cd ai-experiments

## License
This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.


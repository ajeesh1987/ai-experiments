#  Automation Scripts

A collection of Python scripts to automate travel/booking-related tasks, such as checking parking availability and (in future) monitoring flight prices.

## Project Overview

This repository contains scripts I developed to streamline my travel planning. I make 20-30 bookings yearly and wanted to reduce the time spent searching for parking spots and flight deals. Using AI assistance (Grok from xAI), I built a script that checks parking availability at Munich Airport, runs hourly, and alerts me when my desired spot is available.

### Scripts

- **parking_alert.py**: Automates parking spot checks for Munich Airport.
  - Features:
    - Scrapes parking availability for specific dates and times.
    - Runs hourly using the `schedule` library.
    - Displays a GUI alert when the spot ("Economy Parken Nord P44 Parkhaus") is found.
  - Future Plans:
    - Add text message alerts.
    - Expand to flight price monitoring based on airline and price criteria.
    - Potentially auto-book with user confirmation.

## Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/damodaje/TravelAutomationScripts.git
   cd TravelAutomationScripts

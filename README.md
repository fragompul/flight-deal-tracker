# ✈️ Automated Flight Deal Tracker (RapidAPI Edition)

![Python](https://img.shields.io/badge/Python-3.10-blue?style=flat-square&logo=python)
![GitHub Actions](https://img.shields.io/badge/Automated-GitHub_Actions-2088FF?style=flat-square&logo=github-actions)
![Data](https://img.shields.io/badge/Storage-CSV-success?style=flat-square)
![API](https://img.shields.io/badge/API-RapidAPI-0055FF?style=flat-square)

An automated data pipeline and notification system that tracks flight prices to China. Built to find the optimal combination of dates, prices, and routing for a 4-person trip in November 2026.

## 🚀 Overview

Tracking flight prices manually for a wide range of dates and multiple destinations is inefficient. This project automates the workflow by:

1. **Scraping** daily flight offers using flight aggregators via **RapidAPI**.
2. **Filtering** the data based on strict criteria (max 1 stop, specific duration windows).
3. **Storing** the historical pricing data in a `.csv` file directly in this repository.
4. **Alerting** the user via a **Telegram Bot** when prices drop below a predefined threshold, automatically attaching the latest dataset.

The system is deployed completely serverless using **GitHub Actions**, running scheduled cron jobs twice a day.

## 🛠️ Tech Stack & Architecture
* **Language:** Python 3.10
* **Data Provider:** Booking API via RapidAPI Hub
* **Automation/CI:** GitHub Actions
* **Storage:** CSV (Version-controlled)
* **Notifications:** Telegram Bot API

## 📈 Data Science Roadmap

Since the project stores all historical queries in `flight_history.csv`, it serves as a foundational data collection tool for future Machine Learning applications:
- [ ] **Exploratory Data Analysis (EDA):** Identify which days of the week yield the cheapest bookings.
- [ ] **Price Prediction Modeling:** Train a Time-Series model (e.g., ARIMA or Prophet) to forecast price drops.
- [ ] **Expansion:** Integrate hotel APIs to track full vacation package costs.

## ⚙️ Setup & Local Usage

If you want to run this project locally or fork it:

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your environment variables locally in a .env file (ensure this is in your .gitignore):
   ```bash
   RAPIDAPI_KEY=your_rapidapi_key
   TELEGRAM_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   PRICE_THRESHOLD_PER_PERSON=650
   ```
4. Run the script:
   ```bash
   python main.py
   ```

**Note**: Ensure you subscribe to the corresponding Flight API on the RapidAPI platform to obtain a valid API Key and avoid hitting free-tier rate limits.

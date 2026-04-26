# Automated Flight Deal Tracker: Serverless ETL Pipeline

[![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python&logoColor=white)](https://www.python.org/)
[![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF?logo=github-actions&logoColor=white)](#)
[![API](https://img.shields.io/badge/Data_Provider-RapidAPI-0055FF?logo=api&logoColor=white)](#)
[![Telegram](https://img.shields.io/badge/Alerts-Telegram_Bot-2CA5E0?logo=telegram&logoColor=white)](#)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **A robust, serverless Data Engineering pipeline designed to automatically scrape, process, and alert on optimal flight pricing using GitHub Actions and the Telegram API.**

## 📖 Project Overview

Finding the optimal combination of dates, prices, and routing for international flights is a time-consuming mathematical optimization problem. Traditional flight trackers lack the programmatic flexibility to filter by specific routing constraints (e.g., maximum number of layovers) across a wide matrix of dates.

This project implements a fully automated **Extract, Transform, Load (ETL)** data pipeline deployed in a serverless environment. It queries live aviation data, processes nested and unstable JSON payloads, and builds a historical dataset of flight prices to China. When prices drop below a mathematically defined threshold, it pushes real-time alerts to a mobile device.

## ✨ Key Technical Features

1. **Serverless Automation (CI/CD):** Completely independent deployment using GitHub Actions cron-jobs, eliminating the need for dedicated cloud compute instances (AWS EC2/Heroku).
2. **Defensive API Integration:** Built-in fault tolerance. The pipeline dynamically handles RapidAPI rate-limits (HTTP 429) and mitigates silent API failures (e.g., string-wrapped JSON errors) using strict Python type-checking and exception handling.
3. **Advanced Data Transformation:** Deep parsing of complex nested JSON structures from the Booking.com API to accurately compute total trip duration, isolate operating carriers, and strictly filter out itineraries with >1 layover.
4. **Git-Backed Database:** Uses the repository itself as a storage layer. The automated bot natively commits and pushes newly appended data back to `flight_history.csv` after every successful run.
5. **Real-Time Telemetry & Alerting:** Integrates the Telegram Bot API to deliver formatted HTML payload alerts and directly attach the updated dataset to the user's smartphone.
6. **Interactive Analytics Dashboard:** Includes a supplementary Streamlit web application to visually explore the generated CSV dataset, featuring intelligent deduplication and Plotly-based price volatility matrices.

---

## 📂 Repository Architecture

```text
├── .github/workflows/
│   └── flight_tracker.yml      # CI/CD pipeline definition and Cron scheduling
├── main.py                     # Core ETL engine and API orchestration
├── app.py                      # Interactive Streamlit analytics dashboard
├── requirements.txt            # Python dependencies (Requests, Pandas, Streamlit, etc.)
└── flight_history.csv          # Self-updating database (Auto-committed by bot)
```

---

## ⚙️ How It Works (The Pipeline)

1. **Extract:** The GitHub Action boots a Ubuntu container, injects securely encrypted API Keys via Repository Secrets, and queries the RapidAPI Flight endpoint for predefined routes.
2. **Transform:** The Python engine validates the payload, discards malformed data, extracts base units and nanos to calculate exact Euro pricing, counts flight legs, and discards any route exceeding the strict layover threshold.
3. **Load & Alert:** Validated deals are appended to the CSV file. If the `Price_Per_Person_EUR` is $\le 650$€, a POST request triggers the Telegram Bot. Finally, the Git bot commits the new data state to the main branch.

---

## 🚀 Getting Started (Local Execution)

If you wish to fork this project and run the pipeline locally:

**1. Clone the repository:**
```bash
git clone [https://github.com/fragompul/flight-deal-tracker.git](https://github.com/fragompul/flight-deal-tracker.git)
cd flight-deal-tracker
```

**2. Install dependencies:**
```bash
pip install -r requirements.txt
```

**3. Configure Environment Variables:**
Set up your local `.env` file (ensure this is in your `.gitignore` to protect your credentials):
```text
RAPIDAPI_KEY=your_rapidapi_key
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
PRICE_THRESHOLD_PER_PERSON=650
```

**4. Execute the Tracker:**
```bash
python main.py
```

**5. Launch the Analytics Dashboard (Optional):**
```bash
streamlit run app.py
```

---

## 📈 Data Science & ML Roadmap

By continuously running this pipeline, `flight_history.csv` accumulates high-quality, normalized time-series data. Future iterations of this project will focus on predictive analytics:
- [ ] **Exploratory Data Analysis (EDA):** Visualizing historical price volatility based on the days left to departure.
- [ ] **Time-Series Forecasting:** Training an ARIMA or Prophet model to predict local price minima and algorithmically recommend the exact day to purchase tickets.

---

## Author

**Francisco Javier Gómez Pulido**

*Machine Learning Engineer @ IMSE-cnm (CSIC) | Double Major in Mathematics & Computer Science | Master's in Artificial Intelligence*

📫 **Let's connect:**
* **LinkedIn:** [linkedin.com/in/frangomezpulido](https://www.linkedin.com/in/frangomezpulido)
* **GitHub:** [github.com/fragompul](https://github.com/fragompul)

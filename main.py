import os
import csv
import json
import requests
import time
from datetime import datetime, timedelta

# Environment Variables
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PRICE_THRESHOLD_PER_PERSON = float(os.getenv("PRICE_THRESHOLD_PER_PERSON", 650))

# API Configuration
RAPIDAPI_HOST = "booking-com15.p.rapidapi.com"
API_URL = f"https://{RAPIDAPI_HOST}/api/v1/flights/searchFlights"

# Trip Configuration (Optimized for 50 requests/month limit)
ORIGIN = "MAD"
DESTINATIONS = ["PEK", "PVG"]
NIGHTS = [14]
ADULTS = 4
CSV_FILE = "flight_history.csv"

# Search Window: First weekend of November 2026 (Thursday to Sunday)
START_DATE = datetime.strptime("2026-11-05", "%Y-%m-%d")
END_DATE = datetime.strptime("2026-11-08", "%Y-%m-%d")

def init_csv():
    """Initializes the CSV file with headers if it does not exist."""
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Search_Timestamp', 'Origin', 'Destination', 'Departure_Date', 
                'Return_Date', 'Nights', 'Total_Price_EUR', 'Price_Per_Person_EUR', 
                'Airline', 'Max_Stops'
            ])

def send_telegram_alert(message: str):
    """Sends a formatted HTML message via Telegram Bot."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, json=payload)

def send_telegram_document():
    """Sends the operational CSV dataset to the Telegram chat."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    with open(CSV_FILE, 'rb') as f:
        files = {'document': f}
        data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': 'SYSTEM ALERT: Latest flight history dataset attached.'}
        requests.post(url, data=data, files=files)

def search_flights(origin: str, dest: str, dep_date: str, ret_date: str) -> list:
    """Fetches flight offers from the Booking.com RapidAPI endpoint."""
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    
    querystring = {
        "fromId": f"{origin}.AIRPORT",
        "toId": f"{dest}.AIRPORT",
        "departDate": dep_date,
        "returnDate": ret_date,
        "pageNo": "1",
        "adults": str(ADULTS),
        "currency_code": "EUR"
    }
    
    try:
        response = requests.get(API_URL, headers=headers, params=querystring)
        response.raise_for_status()
        
        data = response.json()
        
        # Security parsing for unexpected API plain text errors
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                print(f"API Returned a plain string message: {data[:200]}")
                return []
                
        if isinstance(data, dict):
            if data.get("status") is False:
                print(f"API Internal Error: {data.get('message', 'No message')}")
                return []
            return data.get("data", {}).get("flightOffers", [])
            
        return []
        
    except requests.exceptions.RequestException as e:
        print(f"API request failed for {origin}-{dest} on {dep_date}: {e}")
        return []

def main():
    print(f"[{datetime.now()}] Starting flight search pipeline for {ADULTS} passengers...")
    init_csv()
    
    current_date = START_DATE
    best_deals = []
    new_records = []

    while current_date <= END_DATE:
        str_dep = current_date.strftime("%Y-%m-%d")
        
        for nights in NIGHTS:
            str_ret = (current_date + timedelta(days=nights)).strftime("%Y-%m-%d")
            
            for dest in DESTINATIONS:
                flights = search_flights(ORIGIN, dest, str_dep, str_ret)
                time.sleep(2.0) # Delay to respect API rate limits
                
                for flight in flights:
                    try:
                        # 1. Routing and Stops Parsing
                        segments = flight.get("segments", [])
                        if len(segments) < 2:
                            continue # Ensure it is a round-trip
                            
                        outbound_legs = segments[0].get("legs", [])
                        inbound_legs = segments[1].get("legs", [])
                        
                        outbound_stops = len(outbound_legs) - 1
                        inbound_stops = len(inbound_legs) - 1
                        max_stops = max(outbound_stops, inbound_stops)
                        
                        if max_stops > 1:
                            continue
                            
                        # 2. Airline Parsing
                        try:
                            airline = outbound_legs[0]["carriersData"][0]["name"]
                        except (KeyError, IndexError):
                            airline = "Unknown Airline"
                        
                        # 3. Price Parsing
                        try:
                            units = flight["priceBreakdown"]["total"].get("units", 0)
                            nanos = flight["priceBreakdown"]["total"].get("nanos", 0)
                            total_price = float(units) + (float(nanos) / 1000000000.0)
                        except KeyError:
                            continue
                            
                        price_per_person = total_price / ADULTS
                        
                        # 4. Data Logging
                        new_records.append([
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            ORIGIN, dest, str_dep, str_ret, nights,
                            total_price, price_per_person, airline, max_stops
                        ])
                        
                        # 5. Threshold Validation
                        if price_per_person <= PRICE_THRESHOLD_PER_PERSON:
                            best_deals.append(
                                f"Route: <b>{ORIGIN} -> {dest}</b>\n"
                                f"Dates: {str_dep} to {str_ret} ({nights} nights)\n"
                                f"Price: <b>EUR {price_per_person:.2f}/pax</b> | Stops: {max_stops}\n"
                                f"Airline: {airline}"
                            )
                            
                    except Exception as e:
                        print(f"Data mapping error on flight token: {e}")
                        continue
        
        current_date += timedelta(days=1)

    if new_records:
        with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(new_records)

    if best_deals:
        msg = "<b>CRITICAL UPDATE: FLIGHT DEALS DETECTED</b>\n\n" + "\n\n".join(best_deals[:10])
        send_telegram_alert(msg)
        send_telegram_document()
        print("Alert notifications and dataset successfully transmitted via Telegram.")
    else:
        print("No flights meeting the specified threshold were identified. Dataset updated.")

if __name__ == "__main__":
    main()

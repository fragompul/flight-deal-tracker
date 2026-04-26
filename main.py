import os
import csv
import requests
import time
from datetime import datetime, timedelta

# Environment Variables
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PRICE_THRESHOLD_PER_PERSON = float(os.getenv("PRICE_THRESHOLD_PER_PERSON", 650))

# API Configuration
RAPIDAPI_HOST = "tripadvisor16.p.rapidapi.com"
API_URL = f"https://{RAPIDAPI_HOST}/api/v1/flights/searchFlights"

# Trip Configuration
ORIGIN = "MAD"
#DESTINATIONS = ["PEK", "PKX", "PVG", "CAN"]
#NIGHTS = [13, 14, 15]
DESTINATIONS = ["PEK"]
NIGHTS = [14]
ADULTS = 4
CSV_FILE = "flight_history.csv"

# Search Window: All of November 2026
START_DATE = datetime.strptime("2026-11-01", "%Y-%m-%d")
END_DATE = datetime.strptime("2026-11-30", "%Y-%m-%d")

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
    """Sends the actual CSV file to the Telegram chat."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    with open(CSV_FILE, 'rb') as f:
        files = {'document': f}
        data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': '📊 Latest flight history dataset attached.'}
        requests.post(url, data=data, files=files)

def search_flights(origin: str, dest: str, dep_date: str, ret_date: str) -> list:
    """Fetches flight offers from TripAdvisor via RapidAPI."""
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    
    querystring = {
        "sourceAirportCode": origin,
        "destinationAirportCode": dest,
        "date": dep_date,
        "returnDate": ret_date,
        "adults": str(ADULTS),
        "currencyCode": "EUR"
    }
    
    try:
        response = requests.get(API_URL, headers=headers, params=querystring)
        response.raise_for_status()
        
        data = response.json()
        return data.get("data", {}).get("flights", [])
    except requests.exceptions.RequestException as e:
        print(f"API request failed for {origin}-{dest} on {dep_date}: {e}")
        return []

def main():
    print(f"[{datetime.now()}] Starting flight search for {ADULTS} passengers...")
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
                time.sleep(1.5) 
                
                for flight in flights:
                    try:
                        total_price = float(flight["purchaseLinks"][0]["totalPrice"])
                        price_per_person = total_price / ADULTS
                        
                        outbound_stops = len(flight["segments"][0]["legs"]) - 1
                        inbound_stops = len(flight["segments"][1]["legs"]) - 1
                        max_stops = max(outbound_stops, inbound_stops)
                        
                        if max_stops > 1:
                            continue
                            
                        airline = flight["segments"][0]["legs"][0]["operatingCarrier"]["displayName"]
                        
                        new_records.append([
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            ORIGIN, dest, str_dep, str_ret, nights,
                            total_price, price_per_person, airline, max_stops
                        ])
                        
                        if price_per_person <= PRICE_THRESHOLD_PER_PERSON:
                            best_deals.append(
                                f"✈️ <b>{ORIGIN} ➔ {dest}</b>\n"
                                f"📅 {str_dep} to {str_ret} ({nights} nights)\n"
                                f"💶 <b>€{price_per_person:.2f}/pax</b> | Stops: {max_stops}\n"
                                f"🏢 Airline: {airline}"
                            )
                    except (KeyError, IndexError, TypeError):
                        continue
        
        current_date += timedelta(days=1)

    if new_records:
        with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(new_records)

    if best_deals:
        msg = "🚨 <b>AMAZING FLIGHT DEALS DETECTED!</b> 🚨\n\n" + "\n\n".join(best_deals[:10])
        send_telegram_alert(msg)
        send_telegram_document()
        print("Alerts and dataset sent via Telegram.")
    else:
        print("No flights below threshold today. History updated.")

if __name__ == "__main__":
    main()

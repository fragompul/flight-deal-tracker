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

# Trip Configuration
ORIGIN = "MAD"
DESTINATIONS = ["PEK", "PVG"]
NIGHTS = [14, 15, 16]
ADULTS = 4
CSV_FILE = "flight_history.csv"

# Search Window: November 1st to November 8th, 2026
START_DATE = datetime.strptime("2026-11-01", "%Y-%m-%d")
END_DATE = datetime.strptime("2026-11-08", "%Y-%m-%d")

def init_csv():
    """Initializes the CSV file with extended headers if it does not exist."""
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Search_Timestamp', 'Origin', 'Destination', 'Departure_Date', 
                'Return_Date', 'Nights', 'Total_Price_EUR', 'Price_Per_Person_EUR', 
                'Outbound_Airlines', 'Inbound_Airlines', 'Outbound_Duration_Hrs', 
                'Inbound_Duration_Hrs', 'Outbound_Stops', 'Inbound_Stops',
                'Outbound_Layovers', 'Inbound_Layovers'
            ])

def send_telegram_alert(message: str):
    """Sends a formatted HTML message via Telegram Bot."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print(f"Telegram Alert Delivery Failed: {response.text}")

def send_telegram_document():
    """Sends the operational CSV dataset to the Telegram chat."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    with open(CSV_FILE, 'rb') as f:
        files = {'document': f}
        data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': 'SYSTEM ALERT: Latest flight history dataset attached.'}
        response = requests.post(url, data=data, files=files)
        if response.status_code != 200:
            print(f"Telegram Document Delivery Failed: {response.text}")

def format_segment(segment: dict) -> str:
    """Formats a flight segment (outbound/inbound) into a highly detailed readable string."""
    legs = segment.get("legs", [])
    if not legs: return "N/A\n"
    
    route = legs[0].get("departureAirport", {}).get("code", "Unknown")
    for leg in legs:
        route += f" ➔ {leg.get('arrivalAirport', {}).get('code', 'Unknown')}"
        
    details = ""
    for i, leg in enumerate(legs):
        dep_time = leg.get("departureTime", "").replace("T", " ")[:-3]
        arr_time = leg.get("arrivalTime", "").replace("T", " ")[:-3]
        
        carriers = leg.get("carriersData", [])
        airline = carriers[0].get("name", "Unknown") if carriers else "Unknown"
        
        details += f"  • {leg.get('departureAirport', {}).get('code', '')} ({dep_time}) ➔ {leg.get('arrivalAirport', {}).get('code', '')} ({arr_time}) [{airline}]\n"
        
        if i < len(legs) - 1:
            try:
                next_dep = datetime.strptime(legs[i+1]["departureTime"], "%Y-%m-%dT%H:%M:%S")
                curr_arr = datetime.strptime(leg["arrivalTime"], "%Y-%m-%dT%H:%M:%S")
                layover_sec = (next_dep - curr_arr).total_seconds()
                layover_h = int(layover_sec // 3600)
                layover_m = int((layover_sec % 3600) // 60)
                details += f"    ⏳ <i>Layover: {layover_h}h {layover_m}m in {leg.get('arrivalAirport', {}).get('code', '')}</i>\n"
            except Exception:
                pass
                
    total_h = int(segment.get("totalTime", 0) // 3600)
    total_m = int((segment.get("totalTime", 0) % 3600) // 60)
    
    return f"🗺️ <b>{route}</b> (Total Time: {total_h}h {total_m}m)\n{details}"

def extract_segment_analytics(segment: dict) -> tuple:
    """Extracts analytical data including multiple airlines, flight duration, and layover times."""
    legs = segment.get("legs", [])
    airlines = []
    layovers = []
    
    for i, leg in enumerate(legs):
        carriers = leg.get("carriersData", [])
        if carriers:
            airlines.append(carriers[0].get("name", "Unknown"))
            
        if i < len(legs) - 1:
            try:
                next_dep = datetime.strptime(legs[i+1]["departureTime"], "%Y-%m-%dT%H:%M:%S")
                curr_arr = datetime.strptime(leg["arrivalTime"], "%Y-%m-%dT%H:%M:%S")
                layover_sec = (next_dep - curr_arr).total_seconds()
                layovers.append(f"{int(layover_sec // 3600)}h {int((layover_sec % 3600) // 60)}m")
            except Exception:
                layovers.append("Unknown")
                
    total_h = round(segment.get("totalTime", 0) / 3600.0, 2)
    
    unique_airlines = []
    for a in airlines:
        if a not in unique_airlines:
            unique_airlines.append(a)
            
    airline_str = " + ".join(unique_airlines) if unique_airlines else "Unknown"
    layover_str = " | ".join(layovers) if layovers else "Direct"
    
    return airline_str, total_h, layover_str

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
        
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return []
                
        if isinstance(data, dict):
            if data.get("status") is False:
                return []
            api_data = data.get("data", {})
            if isinstance(api_data, str):
                return []
            if isinstance(api_data, dict):
                return api_data.get("flightOffers", api_data.get("flights", []))
            if isinstance(api_data, list):
                return api_data
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
                time.sleep(2.0) 
                
                for flight in flights:
                    try:
                        segments = flight.get("segments", [])
                        if len(segments) < 2:
                            continue 
                            
                        outbound_legs = segments[0].get("legs", [])
                        inbound_legs = segments[1].get("legs", [])
                        
                        outbound_stops = len(outbound_legs) - 1
                        inbound_stops = len(inbound_legs) - 1
                        max_stops = max(outbound_stops, inbound_stops)
                        
                        # Extract detailed analytics for CSV dataset
                        out_airlines, outbound_h, out_lays = extract_segment_analytics(segments[0])
                        in_airlines, inbound_h, in_lays = extract_segment_analytics(segments[1])
                        
                        try:
                            units = flight["priceBreakdown"]["total"].get("units", 0)
                            nanos = flight["priceBreakdown"]["total"].get("nanos", 0)
                            total_price = float(units) + (float(nanos) / 1000000000.0)
                        except KeyError:
                            continue
                            
                        price_per_person = total_price / ADULTS
                        
                        new_records.append([
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            ORIGIN, dest, str_dep, str_ret, nights,
                            total_price, price_per_person, 
                            out_airlines, in_airlines, 
                            outbound_h, inbound_h, 
                            outbound_stops, inbound_stops, 
                            out_lays, in_lays
                        ])
                        
                        if price_per_person <= PRICE_THRESHOLD_PER_PERSON:
                            meets_ideal_criteria = (max_stops <= 1) and (outbound_h <= 18) and (inbound_h <= 18)
                            
                            warning_tag = ""
                            if not meets_ideal_criteria:
                                warning_tag = "⚠️ <i>NOTE: This itinerary exceeds 1 stop or 18h total flight time.</i>\n"
                                
                            deal_msg = (
                                f"💶 <b>EUR {price_per_person:.2f}/pax</b> (Total: EUR {total_price:.2f})\n"
                                f"{warning_tag}"
                                f"📅 <b>{nights} Nights</b> ({str_dep} to {str_ret})\n\n"
                                f"🛫 <b>OUTBOUND:</b>\n{format_segment(segments[0])}\n"
                                f"🛬 <b>INBOUND:</b>\n{format_segment(segments[1])}\n"
                                f"🏢 <b>Airline:</b> {out_airlines}"
                            )
                            best_deals.append(deal_msg)
                            
                    except Exception as e:
                        continue
        
        current_date += timedelta(days=1)

    if new_records:
        with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(new_records)

    if best_deals:
        msg = "<b>🚨 CRITICAL UPDATE: FLIGHT DEALS DETECTED 🚨</b>\n\n" + "\n--------------------\n\n".join(best_deals[:5])
        send_telegram_alert(msg)
        send_telegram_document()
        print("Alert notifications and dataset successfully transmitted via Telegram.")
    else:
        print("No flights meeting the specified threshold were identified. Dataset updated.")

if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
import plotly.express as px
import os

# -----------------------------------------------------------------------------
# Configuration & Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Flight Deal Tracker | Analytics Dashboard",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a cleaner, professional look
st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Data Loading & Preprocessing
# -----------------------------------------------------------------------------
DATA_PATH = "flight_history.csv"

@st.cache_data(ttl=3600)
def load_and_clean_data():
    if not os.path.exists(DATA_PATH):
        return pd.DataFrame()
    
    # Load dataset
    df = pd.read_csv(DATA_PATH)
    
    if df.empty:
        return df
        
    # Convert date columns to datetime objects
    df['Search_Timestamp'] = pd.to_datetime(df['Search_Timestamp'])
    df['Departure_Date'] = pd.to_datetime(df['Departure_Date'])
    df['Return_Date'] = pd.to_datetime(df['Return_Date'])
    
    # Deduplication Strategy: 
    # If the same flight (Origin, Dest, Dates, Airline, Stops) was searched multiple times,
    # keep only the most recent search timestamp to reflect the latest price.
    subset_cols = ['Origin', 'Destination', 'Departure_Date', 'Return_Date', 'Airline', 'Max_Stops']
    df = df.sort_values('Search_Timestamp', ascending=False).drop_duplicates(subset=subset_cols, keep='first')
    
    # Sort by price initially
    df = df.sort_values('Price_Per_Person_EUR', ascending=True)
    return df

df = load_and_clean_data()

# -----------------------------------------------------------------------------
# App Layout - Header
# -----------------------------------------------------------------------------
st.title("Aviation Data Pipeline: Price Analytics")
st.markdown("Interactive dashboard monitoring historical flight prices and optimal routing combinations.")

if df.empty:
    st.warning("No data found. The automated pipeline needs to execute and generate 'flight_history.csv' first.")
    st.stop()

# -----------------------------------------------------------------------------
# Sidebar - Filtering Engine
# -----------------------------------------------------------------------------
st.sidebar.header("Filter Engine")

# 1. Price Filter
min_price = float(df['Price_Per_Person_EUR'].min())
max_price = float(df['Price_Per_Person_EUR'].max())
selected_price_range = st.sidebar.slider(
    "Max Price Per Person (EUR)", 
    min_value=min_price, 
    max_value=max_price, 
    value=max_price,
    step=10.0
)

# 2. Destinations
destinations = sorted(df['Destination'].unique())
selected_dests = st.sidebar.multiselect("Destination Airports", destinations, default=destinations)

# 3. Layover Filter
stops = sorted(df['Max_Stops'].unique())
selected_stops = st.sidebar.multiselect("Maximum Layovers", stops, default=stops)

# 4. Nights Filter
nights = sorted(df['Nights'].unique())
selected_nights = st.sidebar.multiselect("Duration (Nights)", nights, default=nights)

# 5. Airline Filter
airlines = sorted(df['Airline'].unique())
selected_airlines = st.sidebar.multiselect("Airlines", airlines, default=airlines)

# 6. Date Filter
min_date = df['Departure_Date'].min().date()
max_date = df['Departure_Date'].max().date()
selected_dates = st.sidebar.date_input(
    "Departure Date Range", 
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Apply Filters
filtered_df = df.copy()
filtered_df = filtered_df[filtered_df['Price_Per_Person_EUR'] <= selected_price_range]

if selected_dests:
    filtered_df = filtered_df[filtered_df['Destination'].isin(selected_dests)]
if selected_stops:
    filtered_df = filtered_df[filtered_df['Max_Stops'].isin(selected_stops)]
if selected_nights:
    filtered_df = filtered_df[filtered_df['Nights'].isin(selected_nights)]
if selected_airlines:
    filtered_df = filtered_df[filtered_df['Airline'].isin(selected_airlines)]
    
if len(selected_dates) == 2:
    start_dt, end_dt = selected_dates
    filtered_df = filtered_df[
        (filtered_df['Departure_Date'].dt.date >= start_dt) & 
        (filtered_df['Departure_Date'].dt.date <= end_dt)
    ]

# -----------------------------------------------------------------------------
# Main Content - KPIs
# -----------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Optimal Flights Found", f"{len(filtered_df)}")
with col2:
    cheapest = filtered_df['Price_Per_Person_EUR'].min() if not filtered_df.empty else 0
    st.metric("Lowest Price (Pax)", f"€{cheapest:,.2f}")
with col3:
    avg_price = filtered_df['Price_Per_Person_EUR'].mean() if not filtered_df.empty else 0
    st.metric("Average Price", f"€{avg_price:,.2f}")
with col4:
    best_airline = filtered_df.iloc[0]['Airline'] if not filtered_df.empty else "N/A"
    st.metric("Top Recommended Airline", best_airline)

st.markdown("---")

# -----------------------------------------------------------------------------
# Main Content - Data Visualization
# -----------------------------------------------------------------------------
if not filtered_df.empty:
    tab1, tab2 = st.tabs(["📊 Market Overview", "📋 Detailed Reports"])
    
    with tab1:
        # Scatter Plot: Price Distribution over Dates
        fig = px.scatter(
            filtered_df, 
            x="Departure_Date", 
            y="Price_Per_Person_EUR", 
            color="Destination",
            size="Nights",
            hover_data=["Airline", "Max_Stops", "Return_Date"],
            title="Price Volatility Matrix by Departure Date",
            labels={"Price_Per_Person_EUR": "Price per Person (EUR)", "Departure_Date": "Departure Date"},
            template="plotly_white"
        )
        fig.update_layout(yaxis_tickformat="€")
        st.plotly_chart(fig, use_container_width=True)
        
    with tab2:
        # Format the dataframe for display
        display_df = filtered_df.copy()
        display_df['Departure_Date'] = display_df['Departure_Date'].dt.strftime('%Y-%m-%d')
        display_df['Return_Date'] = display_df['Return_Date'].dt.strftime('%Y-%m-%d')
        display_df['Search_Timestamp'] = display_df['Search_Timestamp'].dt.strftime('%Y-%m-%d %H:%M')
        
        # Select and rename columns for a professional report
        display_df = display_df[[
            'Origin', 'Destination', 'Departure_Date', 'Return_Date', 
            'Nights', 'Airline', 'Max_Stops', 'Price_Per_Person_EUR', 'Total_Price_EUR', 'Search_Timestamp'
        ]]
        
        st.subheader("Optimized Flight Itineraries")
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Price_Per_Person_EUR": st.column_config.NumberColumn("Price/Pax", format="€%.2f"),
                "Total_Price_EUR": st.column_config.NumberColumn("Total Price", format="€%.2f"),
                "Max_Stops": st.column_config.NumberColumn("Layovers", format="%d")
            }
        )
else:
    st.info("No flights match the current filter criteria. Please adjust your parameters.")


import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
from datetime import date
from zoneinfo import ZoneInfo
import requests
from datetime import datetime, timedelta

def fetch_electricity_prices(day):
    year = day.year
    date_string = day.strftime("%m-%d")

    url = (
        f"https://www.elprisetjustnu.se/api/v1/prices/"
        f"{year}/{date_string}_SE3.json"
    )

    response = requests.get(url, timeout=15)
    response.raise_for_status()

    return response.json()
    

# --------------------------------
# INSTÄLLNINGAR
# --------------------------------

START_DATE = date(2026, 9, 11)
START_ODOMETER = 0
YEARLY_LIMIT = 20000       # 2 000 mil
THREE_YEAR_LIMIT = 60000   # 6 000 mil

st.set_page_config(
    page_title="IONIQ 5 Dashboard",
    page_icon="🚗",
    layout="wide"
)


st.markdown("""
<style>

/* Huvudbakgrund */
.stApp {
    background: linear-gradient(135deg, #0b1420 0%, #172638 100%);
    color: #ffffff;
}

/* Huvudrubrik */
h1 {
    color: #ffffff !important;
    font-size: 2.5rem !important;
    font-weight: 800 !important;
}

/* Underrubriker */
h2, h3 {
    color: #ffffff !important;
    font-weight: 700 !important;
}

/* Mätarkort */
[data-testid="stMetric"] {
    background: #24364a;
    border: 1px solid #40566e;
    padding: 22px 20px;
    border-radius: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
}

/* Etiketter */
[data-testid="stMetricLabel"] {
    color: #c5d3e0 !important;
    font-size: 0.95rem !important;
}

/* Stora siffror */
[data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
}

/* Positiv utveckling – grönt */
[data-testid="stMetricDelta"] svg {
    color: #35d07f !important;
}

/* Negativ utveckling – rött */
[data-testid="stMetricDelta"][data-testid*="stMetricDelta"] {
    font-weight: 800 !important;
}

/* Tydligare färger på mätarkorten */
[data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-weight: 800 !important;
}

/* Vanlig text */
.stMarkdown, .stCaption {
    color: #d6e0ea;
}

/* Diagram och tabeller */
[data-testid="stDataFrame"] {
    border: 1px solid #40566e;
    border-radius: 12px;
}

/* Avstånd mellan sektioner */
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
}

</style>
""", unsafe_allow_html=True)

st.title("IONIQ 5 – Dashboard")
st.caption("Uppföljning av körsträcka | 2 000 mil per år | 6 000 mil på tre år")

tab_korbudget, tab_elpriser = st.tabs(["Körbudget", "Elpriser"])

with tab_korbudget:
    # --------------------------------
    # HÄMTA DATA FRÅN SUPABASE
    # --------------------------------
    
    try:
        supabase = create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_SECRET_KEY"]
        )
    
        result = (
            supabase.table("odometer_history")
            .select("id, created_at, odometer_km")
            .order("recorded_at", desc=False)
            .execute()
        )
    
        df = pd.DataFrame(result.data)
        
        if df.empty:
            st.warning("Ingen mätarhistorik finns ännu.")
            st.stop()
    
    except Exception as e:
        st.error("Kunde inte hämta data från databasen.")
        st.code(str(e))
        st.stop()
    
    # --------------------------------
    # BEARBETA DATA
    # --------------------------------
    
    df["recorded_at"] = pd.to_datetime(
        df["created_at"], utc=True
    ).dt.tz_convert("Europe/Stockholm")
    
    df["odometer_km"] = pd.to_numeric(
        df["odometer_km"]
    )
    
    df = df.sort_values("recorded_at")
    
    
    latest = df.iloc[-1]
    current_odometer = float(latest["odometer_km"])
    last_reading = latest["recorded_at"]
    
    today = date.today()
    elapsed_days = max((today - START_DATE).days, 0)
    
    allowed_distance_today = round(elapsed_days * YEARLY_LIMIT / 365.25)
    
    elapsed_years = elapsed_days / 365.25
    
    expected_km = YEARLY_LIMIT * elapsed_years
    difference = current_odometer - expected_km
    
    remaining_km = THREE_YEAR_LIMIT - current_odometer
    remaining_days = max(
        (date(2029, 9, 11) - today).days, 0
    )
    
    remaining_per_day = (
        remaining_km / remaining_days
        if remaining_days > 0 else 0
    )
    
    daily_average = (
        (current_odometer - START_ODOMETER) / elapsed_days
        if elapsed_days > 0 else 0
    )
    
    progress = current_odometer / THREE_YEAR_LIMIT
    
    # --------------------------------
    # ÖVERSIKT
    # --------------------------------
    
    st.subheader("Aktuell status")
    
    c1, c2, c3, c4 = st.columns(4)
    
    c1.metric(
        "Mätarställning",
        f"{current_odometer:,.0f} km".replace(",", " ")
    )
    
    c2.metric(
        "Tillåten körsträcka idag",
        f"{allowed_distance_today:,.0f} km".replace(",", " ")
    )
    
    
    
    if pd.notna(last_reading):
        st.caption(
            f"Senaste avläsning: {last_reading.strftime('%Y-%m-%d %H:%M')}"
        )
    else:
        st.caption("Senaste avläsning: Saknas")
    
    # --------------------------------
    # KÖRBUDGET
    # --------------------------------
    
    st.subheader("Körbudget")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Årlig budget – 2 000 mil**")
    
        st.metric(
            "Skillnad mot budget hittills",
            f"{difference:+,.0f} km".replace(",", " "),
            help="Positivt värde betyder att du ligger över budget."
        )
    
        if difference > 0:
            st.markdown(
                '<span style="color:#ff5c5c;font-weight:800;">🔴 Över budget</span>',
                unsafe_allow_html=True
            )
        elif difference < 0:
            st.markdown(
                '<span style="color:#35d07f;font-weight:800;">🟢 Under budget</span>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<span style="color:#35d07f;font-weight:800;">🟢 Exakt på budget</span>',
                unsafe_allow_html=True
            )
    
        st.progress(min(max(current_odometer / THREE_YEAR_LIMIT, 0), 1))
    with col2:
        st.markdown("**Treårig budget – 6 000 mil**")
        st.metric(
            "Tillåten körning per dag framåt",
            f"{remaining_per_day:.1f} km"
        )
    
    st.caption(
        f"Beräkningen utgår från startdatum {START_DATE} "
        "och en treårsperiod till 11 september 2029."
    )
    
    
    # --------------------------------
    # HISTORIKDIAGRAM
    # --------------------------------
    st.subheader("Faktisk körsträcka jämfört med budget")
    
    # Beräkna tillåten körsträcka för varje datum
    df["recorded_at"] = pd.to_datetime(
        df["recorded_at"], utc=True
    )
    
    df["datum"] = df["recorded_at"].dt.tz_convert(
        "Europe/Stockholm"
    )
    
    start_date = pd.Timestamp("2026-09-11", tz="Europe/Stockholm")
    
    elapsed_days = (df["datum"] - start_date).dt.days
    
    df["tillaten_korning"] = (
        elapsed_days.clip(lower=0) * YEARLY_LIMIT / 365.25
    )
    
    # Lägg till startpunkten
    start_row = pd.DataFrame([{
        "datum": start_date,
        "odometer_km": 0,
        "tillaten_korning": 0
    }])
    
    chart_df = pd.concat([
        start_row,
        df[["datum", "odometer_km", "tillaten_korning"]]
    ], ignore_index=True)
    
    chart_df = chart_df.sort_values("datum")
    
    # Dela upp faktisk körsträcka i under och över budget
    chart_df["Under budget"] = chart_df.apply(
        lambda row: row["odometer_km"]
        if row["odometer_km"] <= row["tillaten_korning"]
        else float("nan"),
        axis=1
    )
    
    chart_df["Över budget"] = chart_df.apply(
        lambda row: row["odometer_km"]
        if row["odometer_km"] > row["tillaten_korning"]
        else float("nan"),
        axis=1
    )
    
    # Skapa diagrammet
    chart = px.line(
        chart_df,
        x="datum",
        y=[
            "Under budget",
            "Över budget",
            "tillaten_korning"
        ],
        markers=True,
        labels={
            "datum": "Datum",
            "value": "Körsträcka (km)",
            "variable": "Typ"
        },
        template="plotly_dark",
        color_discrete_map={
            "Under budget": "#35d07f",
            "Över budget": "#ff5c5c",
            "tillaten_korning": "#f5a623"
        }
    )
    
    # Gör budgetlinjen streckad
    chart.update_traces(
        line=dict(dash="dash"),
        selector={"name": "tillaten_korning"}
    )
    
    # Byt namn på budgetlinjen
    chart.for_each_trace(
        lambda trace: trace.update(name="Tillåten körsträcka")
        if trace.name == "tillaten_korning"
        else None
    )
    
    chart.update_layout(
        paper_bgcolor="#101820",
        plot_bgcolor="#1d2935",
        font_color="#f2f4f7",
        legend_title_text="",
        yaxis_title="Körsträcka (km)",
        xaxis_title="Datum"
    )
    
    st.plotly_chart(chart, use_container_width=True)

with tab_elpriser:
    st.subheader("Elpriser – SE3")

    st.caption("Spotpriser för idag och imorgon")

    today = date.today()
    tomorrow = today + timedelta(days=1)

    try:
        today_prices = fetch_electricity_prices(today)
        tomorrow_prices = fetch_electricity_prices(tomorrow)

        prices = today_prices + tomorrow_prices
        price_df = pd.DataFrame(prices)

        price_df["Tid"] = pd.to_datetime(price_df["time_start"])
        price_df["Pris (öre/kWh)"] = price_df["SEK_per_kWh"] * 100

                # Beräkna de billigaste 25 % av priserna per dygn
        price_df["Billig period"] = (
            price_df.groupby(price_df["Tid"].dt.date)["Pris (öre/kWh)"]
            .rank(method="first", pct=True) <= 0.25
        )

        price_df["Prisnivå"] = price_df["Billig period"].map({
            True: "Billigaste 25 %",
            False: "Övriga tider"
        })

        # Skapa diagram
        chart = px.bar(
            price_df,
            x="Tid",
            y="Pris (öre/kWh)",
            color="Prisnivå",
            color_discrete_map={
                "Billigaste 25 %": "#35d07f",
                "Övriga tider": "#6c8fb3"
            },
            title="Elpriser idag och imorgon"
        )

        chart.update_layout(
            paper_bgcolor="#101820",
            plot_bgcolor="#1d2935",
            font_color="#f2f4f7",
            legend_title_text="",
            xaxis_title="Tid",
            yaxis_title="Pris (öre/kWh)"
        )

        st.plotly_chart(chart, use_container_width=True)

    except Exception as e:
        st.warning("Kunde inte hämta elpriser för idag och imorgon.")
        st.caption(str(e))


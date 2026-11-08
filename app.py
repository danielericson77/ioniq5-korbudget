
import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
from datetime import date
from zoneinfo import ZoneInfo

# --------------------------------
# INSTÄLLNINGAR
# --------------------------------

START_DATE = date(2026, 9, 11)
START_ODOMETER = 0
YEARLY_LIMIT = 20000       # 2 000 mil
THREE_YEAR_LIMIT = 60000   # 6 000 mil

st.set_page_config(
    page_title="IONIQ 5 Körbudget",
    page_icon="🚗",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background-color: #101820;
    color: #f2f4f7;
}
[data-testid="stMetric"] {
    background-color: #1d2935;
    border: 1px solid #344454;
    padding: 18px;
    border-radius: 12px;
}
[data-testid="stMetricLabel"] {
    color: #b8c5d1;
}
h1, h2, h3 {
    color: #f2f4f7;
}
</style>
""", unsafe_allow_html=True)

st.title("🚗 IONIQ 5 – Körbudget")
st.caption("Uppföljning av körsträcka | 2 000 mil per år | 6 000 mil på tre år")

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
    st.write("Rådata – endast datumfält:")
    st.write(result.data)

    st.write("Kontroll av data från Supabase:")
    st.write(df)

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

st.write("Kontroll efter databearbetning:")
st.write(df[["recorded_at", "odometer_km"]])
st.write("Antal rader:", len(df))

latest = df.iloc[-1]
current_odometer = float(latest["odometer_km"])
last_reading = latest["recorded_at"]

today = date.today()
elapsed_days = max((today - START_DATE).days, 0)

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
    f"{current_odometer:,.1f} km".replace(",", " ")
)

c2.metric(
    "Körda mil",
    f"{current_odometer / 10:,.1f}".replace(",", " ")
)

c3.metric(
    "Snitt per dag",
    f"{daily_average:.1f} km"
)

c4.metric(
    "Kvar till 6 000 mil",
    f"{remaining_km / 10:,.1f} mil".replace(",", " ")
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

df["datum"] = (
    df["recorded_at"]
    .dt.tz_convert("Europe/Stockholm")
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

chart = px.line(
    chart_df,
    x="datum",
    y=["odometer_km", "tillaten_korning"],
    markers=True,
    labels={
        "datum": "Datum",
        "value": "Körsträcka (km)",
        "variable": "Typ"
    },
    template="plotly_dark",
    color_discrete_map={
        "odometer_km": "#00c2a8",
        "tillaten_korning": "#f5a623"
    }
)

chart.for_each_trace(
    lambda trace: trace.update(
        name="Faktisk körsträcka" if trace.name == "odometer_km"
        else "Tillåten körsträcka"
    )
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

# --------------------------------
# HISTORIKTABELL
# --------------------------------

st.subheader("Avläsningshistorik")

history = df.copy()
history["Datum"] = history["recorded_at"].dt.strftime(
    "%Y-%m-%d %H:%M"
)
history["Mätarställning (km)"] = history["odometer_km"]

st.dataframe(
    history[["Datum", "Mätarställning (km)"]].sort_values(
        "Datum", ascending=False
    ),
    use_container_width=True,
    hide_index=True
)

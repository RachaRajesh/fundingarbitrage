import requests
import streamlit as st

# --- FETCH FUNCTIONS ---

def fetch_lighter_funding():
    url = "https://mainnet.zklighter.elliot.ai/api/v1/funding-rates"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": "d17a00d571396ab603c2b99731ec2b786377129b1834ef5f3ff5d3ebfa552810c1cd8bcf1c3484b5"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        lighter = {
            item["symbol"].upper(): float(item["rate"]) * 100
            for item in data.get("funding_rates", [])
            if item.get("exchange") == "lighter"
        }
        return lighter
    except Exception as e:
        st.error(f"Error fetching Lighter data: {e}")
        return {}

def fetch_extended_funding():
    url = "https://api.extended.exchange/api/v1/info/markets"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json().get("data", [])
        extended = {
            item["name"].split("-")[0].upper(): float(item.get("marketStats", {}).get("fundingRate", 0)) * 8 * 100
            for item in data
        }
        return extended
    except Exception as e:
        st.error(f"Error fetching Extended data: {e}")
        return {}

def fetch_pacifica_funding():
    url = "https://api.pacifica.fi/api/v1/info/prices"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        symbols = data if isinstance(data, list) else [m for k in data for m in data[k] if isinstance(data[k], list)]
        pacifica = {
            item["symbol"].upper(): float(item.get("funding", 0.0)) * 8 * 100
            for item in symbols
        }
        return pacifica
    except Exception as e:
        st.error(f"Error fetching Pacifica data: {e}")
        return {}

# --- ROI LOGIC ---
def calculate_roi(rate_a, rate_b, fee_a, fee_b):
    high = max(rate_a, rate_b)
    low = min(rate_a, rate_b)
    net_profit = high - low
    total_fee = fee_a + fee_b
    if net_profit > 0:
        roi_hours = (8 * total_fee) / net_profit
        return round(roi_hours, 2)
    return "-"

# --- STREAMLIT UI ---
st.set_page_config(page_title="Funding Arbitrage ROI", layout="wide")
st.title("🔁 Funding Rate Arbitrage Dashboard")

pair_choice = st.selectbox("Choose exchange pair for comparison:", [
    "Lighter vs Extended", "Pacifica vs Extended", "Pacifica vs Lighter"
])

sort_choice = st.radio("Sort by:", ["Difference ↓", "ROI ↑"])

# --- DATA SELECTION ---
if pair_choice == "Lighter vs Extended":
    data_a = fetch_lighter_funding()
    data_b = fetch_extended_funding()
    label_a = "Lighter"
    label_b = "Extended"
    fee_a, fee_b = 0.00, 0.05

elif pair_choice == "Pacifica vs Extended":
    data_a = fetch_pacifica_funding()
    data_b = fetch_extended_funding()
    label_a = "Pacifica"
    label_b = "Extended"
    fee_a, fee_b = 0.08, 0.05

else:  # Pacifica vs Lighter
    data_a = fetch_pacifica_funding()
    data_b = fetch_lighter_funding()
    label_a = "Pacifica"
    label_b = "Lighter"
    fee_a, fee_b = 0.08, 0.00

# --- PROCESS ---
tokens = set(data_a).intersection(set(data_b))
rows = []
for token in tokens:
    rate_a = data_a[token]
    rate_b = data_b[token]
    diff = round(abs(rate_a - rate_b), 4)
    roi = calculate_roi(rate_a, rate_b, fee_a, fee_b)
    rows.append({
        "Token": token,
        f"{label_a} %": f"{rate_a:.4f}%",
        f"{label_b} %": f"{rate_b:.4f}%",
        "Diff %": f"{diff:.4f}%",
        "ROI (w/ fee)": f"{roi}h" if roi != "-" else "-"
    })

if sort_choice == "Difference ↓":
    rows.sort(key=lambda x: float(x["Diff %"][:-1]) if x["Diff %"] != "-" else -999, reverse=True)
elif sort_choice == "ROI ↑":
    rows.sort(key=lambda x: float(x["ROI (w/ fee)"][:-1]) if x["ROI (w/ fee)"] != "-" else float('inf'))

# --- DISPLAY ---
st.markdown("### 📈 Comparison Table")
st.dataframe(rows, use_container_width=True)

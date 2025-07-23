
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Funding Arbitrage ROI", layout="wide")
st.title("🔁 Funding Rate Arbitrage ROI Calculator")

# --------- API Fetching Functions ---------
@st.cache_data(ttl=600)
def fetch_lighter_funding():
    url = "https://mainnet.zklighter.elliot.ai/api/v1/funding-rates"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": "d17a00d571396ab603c2b99731ec2b786377129b1834ef5f3ff5d3ebfa552810c1cd8bcf1c3484b5"
    }
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        funding_rates = data.get("funding_rates", [])
        return {item['symbol'].upper(): item['rate'] * 100 for item in funding_rates if item.get("exchange") == "lighter"}
    except:
        return {}

@st.cache_data(ttl=600)
def fetch_extended_funding():
    url = "https://api.extended.exchange/api/v1/info/markets"
    try:
        response = requests.get(url)
        markets = response.json().get("data", [])
        return {
            market['name'].split("-")[0].upper(): float(market.get("marketStats", {}).get("fundingRate", 0)) * 8 * 100
            for market in markets
        }
    except:
        return {}

@st.cache_data(ttl=600)
def fetch_pacifica_funding():
    url = "https://api.pacifica.fi/api/v1/info/prices"
    try:
        response = requests.get(url)
        data = response.json()
        symbols = {}
        if isinstance(data, list):
            for item in data:
                symbol = item.get("symbol", "").upper()
                rate = item.get("funding", 0.0)
                symbols[symbol] = float(rate) * 100
        elif isinstance(data, dict):
            for group in data.values():
                for item in group:
                    symbol = item.get("symbol", "").upper()
                    rate = item.get("funding", 0.0)
                    symbols[symbol] = float(rate) * 100
        return symbols
    except:
        return {}

# --------- Arbitrage ROI Logic ---------
def compare_and_calculate(src_data, dst_data, src_fee=0.08, dst_fee=0.05):
    matched = set(src_data.keys()).intersection(dst_data.keys())
    results = []
    for token in matched:
        src_rate = src_data[token]
        dst_rate = dst_data[token]

        short_rate, long_rate = (src_rate, dst_rate) if src_rate > dst_rate else (dst_rate, src_rate)
        roi_fee = src_fee if short_rate == src_rate else dst_fee
        diff = short_rate - long_rate
        roi = (8 * roi_fee) / diff if diff > 0 else None

        results.append({
            "Token": token,
            "Short @": "Source" if short_rate == src_rate else "Target",
            "Src Rate (%)": round(src_rate, 4),
            "Dst Rate (%)": round(dst_rate, 4),
            "Diff (%)": round(diff, 4),
            "ROI (h)": round(roi, 2) if roi else "-"
        })

    return pd.DataFrame(results)

# --------- UI Controls ---------
exchange_option = st.selectbox(
    "Choose exchange pair for comparison:",
    ("Lighter vs Extended", "Pacifica vs Extended", "Pacifica vs Lighter")
)

sort_option = st.radio("Sort by:", ["Difference ↓", "ROI ↑"])

# --------- Data Logic ---------
if "Lighter" in exchange_option:
    lighter_data = fetch_lighter_funding()

if "Extended" in exchange_option:
    extended_data = fetch_extended_funding()

if "Pacifica" in exchange_option:
    pacifica_data = fetch_pacifica_funding()

if exchange_option == "Lighter vs Extended":
    df = compare_and_calculate(lighter_data, extended_data, src_fee=0.0, dst_fee=0.05)
elif exchange_option == "Pacifica vs Extended":
    df = compare_and_calculate(pacifica_data, extended_data, src_fee=0.08, dst_fee=0.05)
else:
    df = compare_and_calculate(pacifica_data, lighter_data, src_fee=0.08, dst_fee=0.0)

# --------- Display Table ---------
if sort_option == "Difference ↓":
    df.sort_values("Diff (%)", ascending=False, inplace=True)
else:
    df["ROI (h) numeric"] = pd.to_numeric(df["ROI (h)"], errors="coerce")
    df.sort_values("ROI (h) numeric", inplace=True)
    df.drop(columns=["ROI (h) numeric"], inplace=True)

st.dataframe(df, use_container_width=True)

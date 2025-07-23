import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Funding Arbitrage Dashboard", layout="wide")

# ----------------- API Fetch Functions -----------------

def fetch_extended_funding():
    url = "https://api.extended.exchange/api/v1/info/markets"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return {}

    markets = data.get("data", [])
    funding = {}
    for market in markets:
        name = market["name"]
        token = name.split("-")[0].upper()
        try:
            rate = float(market.get("marketStats", {}).get("fundingRate", "0"))
        except ValueError:
            rate = 0.0
        funding[token] = round(rate * 8 * 100, 4)  # convert to 8hr %
    return funding

def fetch_lighter_funding():
    url = "https://mainnet.zklighter.elliot.ai/api/v1/funding-rates"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": "d17a00d571396ab603c2b99731ec2b786377129b1834ef5f3ff5d3ebfa552810c1cd8bcf1c3484b5"
    }
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        data = res.json()
    except Exception:
        return {}

    funding = {}
    for item in data.get("funding_rates", []):
        if item.get("exchange") == "lighter":
            symbol = item.get("symbol", "").upper()
            rate = item.get("rate", 0)
            funding[symbol] = round(rate * 100, 4)
    return funding

def fetch_pacifica_funding():
    url = "https://api.pacifica.fi/api/v1/info/prices"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
    except Exception:
        return {}

    funding = {}
    if isinstance(data, list):
        for symbol in data:
            name = symbol.get("symbol", "").upper()
            rate = symbol.get("funding", 0.0)
            funding[name] = round(rate * 8 * 100, 4)  # 8hr %
    elif isinstance(data, dict):
        for key in data:
            if isinstance(data[key], list):
                for symbol in data[key]:
                    name = symbol.get("symbol", "").upper()
                    rate = symbol.get("funding", 0.0)
                    funding[name] = round(rate * 8 * 100, 4)
    return funding

# ----------------- Streamlit UI -----------------

st.title("📈 Funding Rate Arbitrage ROI Calculator")

exchange_pair = st.selectbox(
    "Choose exchange pair for comparison:",
    ["Extended vs Lighter", "Pacifica vs Extended", "Pacifica vs Lighter"]
)

sort_option = st.radio("Sort by:", ["Difference ↓", "ROI ↑"])

if exchange_pair == "Extended vs Lighter":
    data_a = fetch_extended_funding()
    data_b = fetch_lighter_funding()
    fee_a = 0.05
    fee_b = 0.00
    label_a = "Extended"
    label_b = "Lighter"

elif exchange_pair == "Pacifica vs Extended":
    data_a = fetch_pacifica_funding()
    data_b = fetch_extended_funding()
    fee_a = 0.08
    fee_b = 0.05
    label_a = "Pacifica"
    label_b = "Extended"

elif exchange_pair == "Pacifica vs Lighter":
    data_a = fetch_pacifica_funding()
    data_b = fetch_lighter_funding()
    fee_a = 0.08
    fee_b = 0.00
    label_a = "Pacifica"
    label_b = "Lighter"

# ----------------- Core Logic -----------------

tokens = set(data_a.keys()).intersection(set(data_b.keys()))
rows = []

for token in sorted(tokens):
    rate_a = data_a[token]
    rate_b = data_b[token]

    diff = round(rate_a - rate_b, 4)

    short_rate = max(rate_a, rate_b)
    long_rate = min(rate_a, rate_b)
    total_fee = fee_a if rate_a > rate_b else fee_b
    profit = abs(short_rate - long_rate)

    if profit > 0:
        roi_hr = round((8 * total_fee) / profit, 2)
    else:
        roi_hr = float("inf")

    rows.append({
        "Token": token,
        f"{label_a} %": f"{rate_a:.4f}%",
        f"{label_b} %": f"{rate_b:.4f}%",
        "Diff %": f"{diff:+.4f}%",
        "ROI (h)": f"{roi_hr:.2f}h" if roi_hr != float("inf") else "-"
    })

df = pd.DataFrame(rows)

if sort_option == "Difference ↓":
    df.sort_values(by="Diff %", ascending=False, inplace=True)
else:
    df["ROI (h) numeric"] = pd.to_numeric(df["ROI (h)"].str.replace("h", "", regex=False), errors="coerce")
    df.sort_values(by="ROI (h) numeric", inplace=True)
    df.drop(columns=["ROI (h) numeric"], inplace=True)

st.dataframe(df, use_container_width=True)

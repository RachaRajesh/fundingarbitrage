
import streamlit as st
import pandas as pd
import requests

def fetch_extended_funding():
    url = "https://api.extended.exchange/api/v1/info/markets"
    try:
        response = requests.get(url)
        data = response.json()
        markets = data.get("data", [])
    except:
        return {}

    extended_symbols = {}
    for market in markets:
        symbol = market.get("name", "")
        short_name = symbol.split("-")[0].upper()
        rate_str = market.get("marketStats", {}).get("fundingRate", "0")
        try:
            rate = float(rate_str)
        except ValueError:
            rate = 0.0
        rate_percent = rate * 100
        extended_symbols[short_name] = round(rate_percent, 4)
    return extended_symbols

def fetch_lighter_funding():
    url = "https://mainnet.zklighter.elliot.ai/api/v1/funding-rates"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": "d17a00d571396ab603c2b99731ec2b786377129b1834ef5f3ff5d3ebfa552810c1cd8bcf1c3484b5"
    }
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        rates = data.get("funding_rates", [])
    except:
        return {}

    lighter_symbols = {}
    for item in rates:
        if item.get("exchange") == "lighter":
            symbol = item.get("symbol", "").upper()
            rate = item.get("rate", 0)
            lighter_symbols[symbol] = round(rate * 100, 4)
    return lighter_symbols

def fetch_pacifica_funding():
    url = "https://api.pacifica.fi/api/v1/info/prices"
    try:
        response = requests.get(url)
        data = response.json()
    except:
        return {}

    pacifica_symbols = {}
    if isinstance(data, list):
        for symbol in data:
            name = symbol.get("symbol", "").upper()
            rate = symbol.get("funding", 0.0)
            pacifica_symbols[name] = round(rate * 100, 4)
    elif isinstance(data, dict):
        for key in data:
            if isinstance(data[key], list):
                for symbol in data[key]:
                    name = symbol.get("symbol", "").upper()
                    rate = symbol.get("funding", 0.0)
                    pacifica_symbols[name] = round(rate * 100, 4)
    return pacifica_symbols

def calculate_arbitrage(data_a, data_b, label_a, label_b, fee_a, fee_b):
    matched = set(data_a.keys()).intersection(set(data_b.keys()))
    rows = []

    for token in matched:
        a_rate = data_a[token]
        b_rate = data_b[token]
        diff = round(b_rate - a_rate, 4)

        long_rate = min(a_rate, b_rate)
        short_rate = max(a_rate, b_rate)
        fee = fee_a if short_rate == a_rate else fee_b

        net_profit = abs(short_rate - long_rate)
        roi_hours = round((fee * 8) / net_profit, 2) if net_profit > 0 else float("inf")

        rows.append({
            "Token": token,
            f"{label_a} %": f"{a_rate:.4f}%",
            f"{label_b} %": f"{b_rate:.4f}%",
            "Diff %": f"{diff:+.4f}%",
            "ROI (h)": "∞" if roi_hours == float("inf") else f"{roi_hours:.2f}h",
            "ROI (h) numeric": roi_hours
        })

    return pd.DataFrame(rows)

st.title("🔁 Funding Rate Arbitrage ROI Tool")

exchange_pair = st.selectbox("Choose exchange pair for comparison:", [
    "Pacifica vs Extended",
    "Pacifica vs Lighter",
    "Extended vs Lighter"
])

sort_by = st.radio("Sort by:", ["Difference ↓", "ROI ↑"])

if exchange_pair == "Pacifica vs Extended":
    df = calculate_arbitrage(fetch_pacifica_funding(), fetch_extended_funding(), "Pacifica", "Extended", 0.08, 0.05)
elif exchange_pair == "Pacifica vs Lighter":
    df = calculate_arbitrage(fetch_pacifica_funding(), fetch_lighter_funding(), "Pacifica", "Lighter", 0.08, 0.00)
else:
    df = calculate_arbitrage(fetch_extended_funding(), fetch_lighter_funding(), "Extended", "Lighter", 0.05, 0.00)

if sort_by == "Difference ↓":
    df["Diff numeric"] = pd.to_numeric(df["Diff %"].str.replace('%', ''), errors='coerce')
    df = df.sort_values(by="Diff numeric", ascending=False).drop(columns=["Diff numeric"])
else:
    df["ROI (h) numeric"] = pd.to_numeric(df["ROI (h) numeric"], errors='coerce')
    df = df.sort_values(by="ROI (h) numeric", ascending=True).drop(columns=["ROI (h) numeric"])

st.dataframe(df.reset_index(drop=True), use_container_width=True)

df.reset_index(drop=True).to_csv("arbitrage_output.csv", index=False)

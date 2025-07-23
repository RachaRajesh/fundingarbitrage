
import requests

def fetch_pacifica_funding():
    url = "https://api.pacifica.fi/api/v1/info/prices"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"\n❌ Pacifica API error: {e}\n")
        return {}

    pacifica_symbols = {}
    if isinstance(data, list):
        for symbol in data:
            name = symbol.get("symbol", "").upper()
            rate = symbol.get("funding", 0.0)
            rate_percent = float(rate) * 8 * 100  # Convert to 8hr funding %
            pacifica_symbols[name] = rate_percent
    elif isinstance(data, dict):
        for key in data:
            if isinstance(data[key], list):
                for symbol in data[key]:
                    name = symbol.get("symbol", "").upper()
                    rate = symbol.get("funding", 0.0)
                    rate_percent = float(rate) * 8 * 100
                    pacifica_symbols[name] = rate_percent

    return pacifica_symbols

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
    except Exception as e:
        print(f"\n❌ Lighter API error: {e}\n")
        return {}

    funding_rates = data.get("funding_rates", [])
    lighter_symbols = {}
    for item in funding_rates:
        if item.get("exchange") != "lighter":
            continue
        symbol = item.get("symbol", "").upper()
        rate = item.get("rate", 0)
        rate_percent = float(rate) * 100  # already 8hr funding rate
        lighter_symbols[symbol] = rate_percent

    return lighter_symbols

def main():
    pacifica_data = fetch_pacifica_funding()
    lighter_data = fetch_lighter_funding()

    matched = set(pacifica_data.keys()).intersection(set(lighter_data.keys()))
    results = []

    for token in matched:
        pacifica_rate = pacifica_data.get(token)
        lighter_rate = lighter_data.get(token)

        pacifica_str = f"{pacifica_rate:.4f}%" if pacifica_rate is not None else "-"
        lighter_str = f"{lighter_rate:.4f}%" if lighter_rate is not None else "-"

        if pacifica_rate is not None and lighter_rate is not None:
            diff = lighter_rate - pacifica_rate
            diff_str = f"{diff:.4f}%"

            # Fees
            pacifica_fee = 0.08
            lighter_fee = 0.00

            # Short on higher funding, long on lower
            high = max(pacifica_rate, lighter_rate)
            low = min(pacifica_rate, lighter_rate)
            net_profit = high - low

            if net_profit > 0:
                roi_with_fee = (8 * (pacifica_fee + lighter_fee)) / net_profit
                roi_str = f"{roi_with_fee:.2f}h"
            else:
                roi_str = "-"
        else:
            diff_str = roi_str = "-"

        results.append((token, pacifica_str, lighter_str, diff_str, roi_str))

    results.sort(key=lambda x: float(x[4][:-1]) if x[4] != '-' else float('inf'))

    print("\n🔁 Funding Rate Differences + ROI (Short High, Long Low):")
    print(f"{'Token':<10} | {'Pacifica %':<12} | {'Lighter %':<12} | {'Diff %':<10} | {'ROI (w/ fee)':<13}")
    print("-" * 70)
    for token, pacifica_str, lighter_str, diff_str, roi_str in results:
        print(f"{token:<10} | {pacifica_str:<12} | {lighter_str:<12} | {diff_str:<10} | {roi_str:<13}")

if __name__ == "__main__":
    main()

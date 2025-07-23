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
            pacifica_symbols[name] = float(rate) * 100  # Convert to %
    elif isinstance(data, dict):
        for key in data:
            if isinstance(data[key], list):
                for symbol in data[key]:
                    name = symbol.get("symbol", "").upper()
                    rate = symbol.get("funding", 0.0)
                    pacifica_symbols[name] = float(rate) * 100

    return pacifica_symbols

def fetch_extended_funding():
    url = "https://api.extended.exchange/api/v1/info/markets"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"\n❌ Extended API error: {e}\n")
        return {}

    markets = data.get("data", [])
    extended_symbols = {}
    for market in markets:
        symbol = market.get("name", "")
        short_name = symbol.split("-")[0].upper()
        rate_str = market.get("marketStats", {}).get("fundingRate", "0")
        try:
            rate = float(rate_str)
        except ValueError:
            rate = 0.0
        extended_symbols[short_name] = rate * 100  # Funding already per hour in decimal
    return extended_symbols

def main():
    pacifica_data = fetch_pacifica_funding()
    extended_data = fetch_extended_funding()

    matched = set(pacifica_data.keys()).intersection(set(extended_data.keys()))
    results = []

    for token in matched:
        pacifica_rate = pacifica_data.get(token)
        extended_rate = extended_data.get(token)

        pacifica_str = f"{pacifica_rate:.4f}%" if pacifica_rate is not None else "-"
        extended_str = f"{extended_rate:.4f}%" if extended_rate is not None else "-"

        if pacifica_rate is not None and extended_rate is not None:
            diff = extended_rate - pacifica_rate
            diff_str = f"{diff:.4f}%"

            # Arbitrage logic: short high, long low
            if extended_rate > pacifica_rate:
                short_on = "extended"
                net_profit = extended_rate - pacifica_rate
                fee = 0.05  # Extended fee
            else:
                short_on = "pacifica"
                net_profit = pacifica_rate - extended_rate
                fee = 0.08  # Pacifica fee

            if net_profit > 0:
                roi_with_fee = fee / net_profit
                roi_str = f"{roi_with_fee:.2f}h"
            else:
                roi_str = "-"
        else:
            diff_str = roi_str = "-"

        results.append((token, pacifica_str, extended_str, diff_str, roi_str))

    results.sort(key=lambda x: float(x[4][:-1]) if x[4] != '-' else float('inf'))

    print("\n🔁 Funding Rate Differences + ROI (Short High, Long Low):")
    print(f"{'Token':<10} | {'Pacifica %':<12} | {'Extended %':<12} | {'Diff %':<10} | {'ROI (w/ fee)':<13}")
    print("-" * 70)
    for token, pacifica_str, extended_str, diff_str, roi_str in results:
        print(f"{token:<10} | {pacifica_str:<12} | {extended_str:<12} | {diff_str:<10} | {roi_str:<13}")

if __name__ == "__main__":
    main()

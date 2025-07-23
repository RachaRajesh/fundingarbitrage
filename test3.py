import requests

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
        rate_percent = rate * 100  # already 8hr funding rate
        lighter_symbols[symbol] = rate_percent

    return lighter_symbols

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
        rate_percent = rate * 8 * 100  # convert 1hr to 8hr funding
        extended_symbols[short_name] = rate_percent

    return extended_symbols

def main():
    lighter_data = fetch_lighter_funding()
    extended_data = fetch_extended_funding()

    matched = set(lighter_data.keys()).union(set(extended_data.keys()))
    results = []

    for token in matched:
        lighter_rate = lighter_data.get(token)
        extended_rate = extended_data.get(token)

        lighter_str = f"{lighter_rate:.4f}%" if lighter_rate is not None else "-"
        extended_str = f"{extended_rate:.4f}%" if extended_rate is not None else "-"

        if lighter_rate is not None and extended_rate is not None:
            diff = extended_rate - lighter_rate
            diff_str = f"{diff:.4f}%"

            trading_fee = 0.05  # round-trip fee assumed

            # Arbitrage logic: short the higher funding, long the lower
            higher = max(lighter_rate, extended_rate)
            lower = min(lighter_rate, extended_rate)
            net_profit = higher - lower

            if net_profit > 0:
                roi_with_fee = (8 * trading_fee) / net_profit
                roi_str = f"{roi_with_fee:.2f}h"
            else:
                roi_str = "-"
        else:
            diff_str = roi_str = "-"

        results.append((token, lighter_str, extended_str, diff_str, roi_str))

    sort_choice = input("\nSort by (1) difference descending or (2) ROI ascending? Enter 1 or 2: ").strip()
    if sort_choice == '1':
        results.sort(key=lambda x: float(x[3][:-1]) if x[3] != '-' else -999, reverse=True)
    elif sort_choice == '2':
        results.sort(key=lambda x: float(x[4][:-1]) if x[4] != '-' else float('inf'))
    else:
        results.sort(key=lambda x: x[0])

    print("\n\n🔁 Funding Rate Differences + ROI Estimates:")
    print(f"{'Token':<10} | {'Lighter %':<12} | {'Extended %':<12} | {'Diff %':<10} | {'ROI (w/ fee)':<13}")
    print("-" * 70)
    for token, lighter_str, extended_str, diff_str, roi_str in results:
        print(f"{token:<10} | {lighter_str:<12} | {extended_str:<12} | {diff_str:<10} | {roi_str:<13}")

if __name__ == "__main__":
    main()

import os
import requests
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

if not API_KEY:
    print("ERROR: No API key found. Please add your Alpha Vantage API key to a .env file.")
    print("Example: ALPHA_VANTAGE_API_KEY=your_api_key_here")
    exit(1)

def test_real_time_forex():
    """Test real-time forex exchange rate API"""
    print("\n--- Testing Real-Time Forex API ---")
    
    url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=EUR&to_currency=USD&apikey={API_KEY}"
    
    print(f"Making request to: {url.replace(API_KEY, 'YOUR_API_KEY')}")
    
    response = requests.get(url)
    data = response.json()
    
    if "Realtime Currency Exchange Rate" in data:
        print("✓ SUCCESS: Real-time forex API is working")
        exchange_rate = data["Realtime Currency Exchange Rate"]["5. Exchange Rate"]
        print(f"Current EUR/USD rate: {exchange_rate}")
        return True
    elif "Error Message" in data:
        print(f"× ERROR: {data['Error Message']}")
        return False
    elif "Information" in data:
        print(f"× RATE LIMIT: {data['Information']}")
        return False
    else:
        print("× ERROR: Unexpected response format")
        print(data)
        return False

def test_daily_forex():
    """Test daily forex data API"""
    print("\n--- Testing Daily Forex Data API ---")
    
    url = f"https://www.alphavantage.co/query?function=FX_DAILY&from_symbol=EUR&to_symbol=USD&outputsize=compact&apikey={API_KEY}"
    
    print(f"Making request to: {url.replace(API_KEY, 'YOUR_API_KEY')}")
    
    response = requests.get(url)
    data = response.json()
    
    if "Time Series FX (Daily)" in data:
        print("✓ SUCCESS: Daily forex API is working")
        # Get the latest date in the time series
        latest_date = list(data["Time Series FX (Daily)"].keys())[0]
        latest_data = data["Time Series FX (Daily)"][latest_date]
        print(f"Latest data ({latest_date}):")
        print(f"  Open:  {latest_data['1. open']}")
        print(f"  High:  {latest_data['2. high']}")
        print(f"  Low:   {latest_data['3. low']}")
        print(f"  Close: {latest_data['4. close']}")
        return True
    elif "Error Message" in data:
        print(f"× ERROR: {data['Error Message']}")
        return False
    elif "Information" in data:
        print(f"× RATE LIMIT: {data['Information']}")
        return False
    else:
        print("× ERROR: Unexpected response format")
        print(data)
        return False

def test_intraday_forex():
    """Test intraday forex data API"""
    print("\n--- Testing Intraday (30min) Forex Data API ---")
    
    url = f"https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol=EUR&to_symbol=USD&interval=30min&outputsize=compact&apikey={API_KEY}"
    
    print(f"Making request to: {url.replace(API_KEY, 'YOUR_API_KEY')}")
    
    response = requests.get(url)
    data = response.json()
    
    if "Time Series FX (30min)" in data:
        print("✓ SUCCESS: Intraday forex API is working")
        # Get the latest date in the time series
        latest_datetime = list(data["Time Series FX (30min)"].keys())[0]
        latest_data = data["Time Series FX (30min)"][latest_datetime]
        print(f"Latest data ({latest_datetime}):")
        print(f"  Open:  {latest_data['1. open']}")
        print(f"  High:  {latest_data['2. high']}")
        print(f"  Low:   {latest_data['3. low']}")
        print(f"  Close: {latest_data['4. close']}")
        return True
    elif "Error Message" in data:
        print(f"× ERROR: {data['Error Message']}")
        return False
    elif "Information" in data:
        print(f"× RATE LIMIT: {data['Information']}")
        return False
    else:
        print("× ERROR: Unexpected response format")
        print(data)
        return False

def test_usdx():
    """Test DXY data - trying multiple approaches"""
    print("\n--- Testing DXY (US Dollar Index) Data ---")
    
    # Try as a forex pair
    url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=USD&to_currency=DXY&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    if "Realtime Currency Exchange Rate" in data:
        print("✓ SUCCESS: DXY as forex pair is working")
        return True
    
    # Try as a symbol (like ticker DXY)
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=DXY&apikey={API_KEY}"
    print(f"Making request to: {url.replace(API_KEY, 'YOUR_API_KEY')}")
    
    response = requests.get(url)
    data = response.json()
    
    if "Global Quote" in data and data["Global Quote"]:
        print("✓ SUCCESS: DXY as symbol is working")
        print(f"Current DXY price: {data['Global Quote']['05. price']}")
        return True
    
    # If none of the above work, try searching for the symbol
    url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords=dollar%20index&apikey={API_KEY}"
    print(f"Making request to: {url.replace(API_KEY, 'YOUR_API_KEY')}")
    
    response = requests.get(url)
    data = response.json()
    
    if "bestMatches" in data and data["bestMatches"]:
        print("✓ PARTIAL SUCCESS: Found potential DXY symbols")
        for match in data["bestMatches"]:
            print(f"  Symbol: {match['1. symbol']}, Name: {match['2. name']}")
        return True
    
    print("× NOTE: Unable to find direct DXY data. You may need to use a proxy like UUP or USDX.")
    print("  Suggestion: For DXY, you may need to use another API or a workaround.")
    return False

def check_api_rate_limits():
    """Print API rate limit information"""
    print("\n--- Alpha Vantage API Rate Limits ---")
    print("Free tier limitations:")
    print("- 5 API calls per minute")
    print("- 500 API calls per day")
    print("\nTo avoid rate limit issues:")
    print("1. Add delays between API calls")
    print("2. Cache results when possible")
    print("3. Consider batching related API calls")
    print("4. Upgrade to a paid plan if necessary")

def print_api_key_status():
    """Print masked API key information"""
    print("\n--- API Key Status ---")
    if not API_KEY:
        print("× ERROR: No API key found")
    else:
        masked_key = API_KEY[:4] + "*" * (len(API_KEY) - 8) + API_KEY[-4:]
        print(f"✓ API key found: {masked_key}")
        print("Remember to keep your API key secret!")

def main():
    """Run all tests"""
    print("=" * 50)
    print("Alpha Vantage API Test")
    print("=" * 50)
    
    print_api_key_status()
    
    success_count = 0
    total_tests = 4
    
    if test_real_time_forex():
        success_count += 1
    
    if test_daily_forex():
        success_count += 1
    
    if test_intraday_forex():
        success_count += 1
    
    if test_usdx():
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {success_count}/{total_tests} tests passed")
    print("=" * 50)
    
    check_api_rate_limits()

if __name__ == "__main__":
    main()
import requests

# Fetch the JSON data from the URL
response = requests.get('https://tradeogre.com/api/v1/ticker/BTC-USDT')

# Check if the request was successful
if response.status_code == 200:
    data = response.json()  # Parse the JSON response
    btc_price = data['price']  # Extract the BTC price
    print(btc_price)  # Print the BTC price
else:
    print(f"Error: {response.status_code}")

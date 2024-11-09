import requests

# Fetch the JSON data from the URL
print("Request RYO-BTC")
response_ryo_btc = requests.get('https://tradeogre.com/api/v1/ticker/RYO-BTC')
print("Request BTC-USDT")
response_btc_usd = requests.get('https://tradeogre.com/api/v1/ticker/BTC-USDT')
print("Request USDT-RUB")
response_rub_usd = requests.get('https://www.cbr-xml-daily.ru/daily_json.js')

# Check if the request was successful
if response_ryo_btc.status_code == 200:
    data = response_ryo_btc.json()  # Parse the JSON response
    ryo_value = data['price']  # Extract the RYO price
    print(f"Ryo BTC price: {ryo_value} ")  # Print the RYO price
    data = response_btc_usd.json()  # Parse the JSON response
    btc_price = data['price']  # Extract the BTC price
    print(f"BTC price in USD: {btc_price} ")  # Print the BTC price
    data = response_rub_usd.json()  # Parse the JSON response
    usd_rub_price = data['Valute']['USD']['Value']  # Extract the USD value
    print(f"RUB price in USD: {usd_rub_price} ")  # Print the USD value
    ryo_usd_price = float(ryo_value) * float(btc_price)
    print(f"Price RYO in USD: {ryo_usd_price} ")  # Print the USD price
    ryo_rub_price = float(ryo_usd_price) * float(usd_rub_price)
    print(f"Price RYO in RUB: {ryo_rub_price}")  # Print the RUB price



else:
    print(f"Error: {response.status_code}")

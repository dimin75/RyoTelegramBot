import requests

# Fetch the JSON data from the URL
response = requests.get('https://tradeogre.com/api/v1/ticker/RYO-BTC')

# Check if the request was successful
if response.status_code == 200:
    data = response.json()  # Parse the JSON response
    ryo_value = data['price']  # Extract the RYO price
    print(ryo_value)  # Print the RYO price
else:
    print(f"Error: {response.status_code}")

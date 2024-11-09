import requests

# Fetch the JSON data from the URL
response = requests.get('https://www.cbr-xml-daily.ru/daily_json.js')

# Check if the request was successful
if response.status_code == 200:
    data = response.json()  # Parse the JSON response
    usd_value = data['Valute']['USD']['Value']  # Extract the USD value
    print(usd_value)  # Print the USD value
else:
    print(f"Error: {response.status_code}")

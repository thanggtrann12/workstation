import requests

response = requests.get('http://localhost:5000/GetCommandSet/')

if response.status_code == 200:
    data = response.json()
    # Do something with the data
    print(data)
else:
    print(f'Request failed with status code {response.status_code}')

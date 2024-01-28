import requests
from bs4 import BeautifulSoup
import csv

def extract(page):
    url = f'https://visitseattle.org/events/page/{page}'
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    return soup

def extract_event_urls(soup):
    selector = "div.search-result-preview > div > h3 > a"
    a_eles = soup.select(selector)
    return [x['href'] for x in a_eles]

def extract_event_details(event_url):
    response = requests.get(event_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extracting details
    name = soup.find('h1', class_='page-title').text.strip()
    date = soup.find("h4").find_all("span")[0].text.strip()
    location = soup.find("h4").find_all("span")[1].text.strip()
    event_type = soup.find_all("a", class_="button big medium black category")[0].text.strip()
    region = soup.find_all("a", class_="button big medium black category")[1].text.strip()
    
    return [name, date, location, event_type, region]

# Extract event URLs
event_data = []
for page in range(0, 2):
    print(f'Getting page {page}...')
    soup = extract(page)
    event_urls = extract_event_urls(soup)
    for event_url in event_urls:
        data = extract_event_details(event_url)
        event_data.append(data)

# Use OpenStreetMap API to get latitude and longitude for locations
for data in event_data:
    region_name = data[4].split('/')[0].strip()  # Extract the first name before the '/'
    region_name = f"{region_name}, Seattle"  # Append ", Seattle"
    #print (region_name)
    base_url = "https://nominatim.openstreetmap.org/search.php"
    query_params = {
        "q": region_name,
        "format": "jsonv2"
    }
    res = requests.get(base_url, params=query_params)
    location_data = res.json()
    #print(location_data)
    if location_data:
        latitude = location_data[0]['lat']
        longitude = location_data[0]['lon']
        data.extend([latitude, longitude])
    else:
        data.extend([None, None])

# Step 4: Look up the weather
weather_api_url = "https://api.weather.gov/points/{},{}"
for data in event_data:
    if data[-2] is not None and data[-1] is not None:
        weather_url = weather_api_url.format(data[-2], data[-1])
        response = requests.get(weather_url)
        if response.status_code == 200:
            point_dict = response.json()
            point_dict
            forcast_url = point_dict['properties']['forecast']
            res = requests.get(forcast_url)
            weather_data = res.json()
            #print(weather_data)
            if 'properties' in weather_data and 'periods' in weather_data['properties']:
                forecast = weather_data['properties']['periods'][0]['detailedForecast']
                data.append(forecast)
            else:
                data.append("Weather data not available")
        else:
            data.append("Weather data not available")
    else:
        data.append("Weather data not available")

# Store data as CSV
header = ['Name', 'Date', 'Location', 'Type', 'Region', 'Latitude', 'Longitude', 'Weather Forecast']
with open('events.csv', 'w', newline='', encoding='utf-8') as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(header)
    csv_writer.writerows(event_data)

print("Data has been successfully written to events.csv.")

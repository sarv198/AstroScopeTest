import requests
# import pandas as pd

start_date = '2015-06-30'
end_date = '2016-06-30'
api_key = 'V2PUUx21RDfaBSJn3VbX9AOsQHQ8b9b8qnT76OBY'

# print(f'https://api.nasa.gov/neo/rest/v1/feed?start_date={start_date}&end_date={end_date}&api_key={api_key}')
# result = requests.get(f'https://api.nasa.gov/neo/rest/v1/feed?start_date={start_date}&api_key={api_key}')

des = 433

for i in range(1, 11):
    #print(f'https://ssd-api.jpl.nasa.gov/cad.api?des={str(des)}&date-min=1900-01-01&date-max=2100-01-01&dist-max=0.2')
    result2 = requests.get(f'https://ssd-api.jpl.nasa.gov/cad.api?des={str(des)}&date-min=1900-01-01&date-max=2100-01-01&dist-max=0.2')
    # This API returns name, orbit ID, time of close-approach, approach distance, minimum distance, maximum distance, velocity relative to approach body, velocity relative to massless body, time of close approach, body, magnitude H, diameter, uncertainty in diameter, full name
    # We want TIME OF CLOSE-APPROACH, DISTANCE, VELOCITY RELATIVE TO APPROACH BODY, DIAMETER, FULLNAME
    des -= 1
    #print(result2.json())
    TimeOFCA = result2.json()['data'][0][4]
    print(TimeOFCA)

try:
    result2.raise_for_status()

except requests.HTTPError:
    # print(f'Error {result.status_code}')
    print(f'Error {result2.status_code}')

#print(result.json())
#print(result2.json())

# print(result.json()['near_earth_objects'][start_date])

#df = pd.DataFrame(result.json()['near_earth_objects'])
#print(df.head())

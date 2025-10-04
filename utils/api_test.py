import requests
import pandas as pd

start_date = '2015-06-30'
end_date = '2016-06-30'
api_key = 'V2PUUx21RDfaBSJn3VbX9AOsQHQ8b9b8qnT76OBY'

print(f'https://api.nasa.gov/neo/rest/v1/feed?start_date={start_date}&end_date={end_date}&api_key={api_key}')
result = requests.get(f'https://api.nasa.gov/neo/rest/v1/feed?start_date={start_date}&api_key={api_key}')

try:
    result.raise_for_status()

except requests.HTTPError:
    print(f'Error {result.status_code}')

#print(result.json())

print(result.json()['near_earth_objects'][start_date])

#df = pd.DataFrame(result.json()['near_earth_objects'])
#print(df.head())

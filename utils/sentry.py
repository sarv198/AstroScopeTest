import requests
def get_sentry_des(impact_probability = 1e-5):
    sentry_url = "https://ssd-api.jpl.nasa.gov/sentry.api"
    params = {
        'all':'1',
        'ip-min':str(impact_probability)
    }

    response = requests.get(sentry_url, params = params)

    try:
        response.raise_for_status()
    except requests.HTTPError:
        print(f"Error {response.status_code}")
    
    data_list = response.json()['data']

    list_of_des = [row["des"] for row in data_list]

    return list_of_des

# print(get_sentry_des())

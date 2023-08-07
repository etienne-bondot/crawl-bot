import requests


def calculatePageSpeed(url):
    try:
        response = requests.get(url)
        response_time = response.elapsed.total_seconds()
        return response_time
    except requests.exceptions.RequestException:
        return None

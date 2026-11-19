
def fetch_data(client, url):
    response = client.get(url)
    return response


def process_data(client, url):
    data = fetch_data(client, url)
    return data


def generate_report(client, url):
    result = process_data(client, url)
    print(result)
    return result


def calculate_total(a, b):
    return a + b


async def fetch_data(client, url):
    response = await client.get(url)
    return response


async def process_data(client, url):
    data = await fetch_data(client, url)
    return data


async def generate_report(client, url):
    result = await process_data(client, url)
    print(result)
    return result


def calculate_total(a, b):
    return a + b

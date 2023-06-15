import yaml
import requests
from requests.exceptions import ConnectionError

# Load the YAML file
with open("accounts.yaml") as file:
    data = yaml.safe_load(file)

# Loop through each item in the YAML data
for item in data:
    print("Checking", item["name"])
    name = item["name"]
    accounts = item["accounts"]

    # Check if the 'source' field is present
    if "source" in item:
        source = item["source"]

        # If source is a list, loop through each URL
        if isinstance(source, list):
            for url in source:
                if url.startswith("http"):
                    try:
                        response = requests.head(url, allow_redirects=False)
                        response_code = response.status_code

                        # Check if the response code is not 200 or 301
                        if (
                            response_code != 200
                            and response_code != 301
                            and response_code != 403
                        ):
                            print(f"URL: {url}")
                            print(f"Response Code: {response_code}")
                            print("----------------------")

                    except ConnectionError as e:
                        print(f"Error connecting to URL: {url}")
                        print(f"Error message: {str(e)}")
                        print("----------------------")
                else:
                    print(f"Invalid URL: {source}")
                    print("----------------------")

        # If source is a single URL, handle it directly
        else:
            if source.startswith("http"):
                try:
                    response = requests.head(source, allow_redirects=False)
                    response_code = response.status_code

                    # Check if the response code is not 200 or 301
                    if (
                        response_code != 200
                        and response_code != 301
                        and response_code != 403
                    ):
                        print(f"URL: {source}")
                        print(f"Response Code: {response_code}")
                        print("----------------------")

                except ConnectionError as e:
                    print(f"Error connecting to URL: {source}")
                    print(f"Error message: {str(e)}")
                    print("----------------------")
            else:
                print(f"Invalid URL: {source}")

    else:
        print(f"No source for {name}")
        print("----------------------")

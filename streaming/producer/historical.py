from dotenv import load_dotenv
import requests
import os
import json
import time
from confluent_kafka.cimpl import Producer
import producer.ccloud_lib as ccloud_lib
from producer.date_range import get_date_range


def stream_historical():

    load_dotenv()
    api_key = os.environ.get("crypto_api_key")

    # Read arguments and configurations and initialize
    # args = ccloud_lib.parse_args()
    config_file = "producer/ccloud.config"
    # topic = args.topic
    conf = ccloud_lib.read_ccloud_config(config_file)

    # Create Producer instance
    producer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
    producer = Producer(producer_conf)

    # Create topic
    kafka_topic = "coins_historical"
    ccloud_lib.create_topic(conf, kafka_topic)

    date_range_hist = get_date_range()

    # List of top 10 coin by volume
    # coin_list = ["USDT", "BTC", "ETH", "FDUSD", "XRP", "SOL", "USDC", "DOGE", "LINK", "AAVE"]
    # note :  "USDT", "BTC", "ETH", "FDUSD", "XRP", "SOL" loaded from 1 Jan to 19 Dec 2024..
    # ["USDC", "DOGE", "LINK", "AAVE"] loaded from 1 Jun to Dec 2024
    
    coin_list = ["USDT", "BTC", "ETH", "FDUSD", "XRP", "SOL", "USDC", "DOGE", "LINK", "AAVE"]

    # Pull daily 12:00 UTC price for each coin
    i = 0
    while i < len(coin_list):
        current_coin = coin_list[i]

        # API URL and Payload
        base_url = "https://api.livecoinwatch.com/coins/single/history"

        for date, timestamp in date_range_hist.items():

            start_unix_timestamp = timestamp
            end_unix_timestamp = timestamp

            payload = json.dumps(
                {
                    "currency": "USD",
                    "code": current_coin,
                    "start": start_unix_timestamp,
                    "end": end_unix_timestamp,
                    "meta": True,
                }
            )
            # Headers for the API request
            headers = {"content-type": "application/json", "x-api-key": api_key}

            # Fetch the data from the API
            response = requests.request("POST", base_url, headers=headers, data=payload)

            if response.status_code == 200:
                data = response.json()

                # Send data to Kafka
                producer.produce(kafka_topic, key=None, value=json.dumps(data))
                producer.flush()  # Ensure the message is delivered
                print(f"Message sent to Kafka: {data}")

            else:
                print(f"Failed to fetch data: {response.status_code} - {response.text}")

            time.sleep(
                1
            )  # adding a pause because after around 260+ consecutive API calls, i get error 429 Too Many Requests

        i += 1

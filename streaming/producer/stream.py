from dotenv import load_dotenv
import requests
import os
import json
import time
from confluent_kafka.cimpl import Producer
import producer.ccloud_lib as ccloud_lib


def stream_coins():

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
    kafka_topic = "coins_current_full"
    ccloud_lib.create_topic(conf, kafka_topic)

    # Poll the API every n seconds
    while True:
        # API URL and Payload
        base_url = "https://api.livecoinwatch.com/coins/map"
        payload = json.dumps(
            {
                "codes": [
                    "USDT",
                    "BTC",
                    "ETH",
                    "FDUSD",
                    "XRP",
                    "SOL",
                    "USDC",
                    "DOGE",
                    "LINK",
                    "AAVE"
                ],
                "currency": "USD",
                "sort": "code",
                "order": "ascending",
                "offset": 0,
                "limit": 0,
                "meta": True,
            }
        )

        # Headers for the API request
        headers = {"content-type": "application/json", "x-api-key": api_key}

        # Fetch the data from the API
        response = requests.request("POST", base_url, headers=headers, data=payload)

        if response.status_code == 200:
            data = response.json()

            # Send each row of the data to Kafka
            for coin in data:
                c_code = coin.get("code")
                producer.produce(kafka_topic, key=str(c_code), value=json.dumps(coin))
                producer.flush()  # Ensure the message is delivered
                print(f"Message sent to Kafka: {coin}")

        else:
            print(f"Failed to fetch data: {response.status_code} - {response.text}")

        time.sleep(3)

from dotenv import load_dotenv
import requests 
import os
import json
from confluent_kafka.cimpl import Producer
import ccloud_lib
import time


if __name__ == '__main__':

    load_dotenv()
    api_key = os.environ.get("crypto_api_key")

    # Read arguments and configurations and initialize
    #args = ccloud_lib.parse_args()
    config_file = 'ccloud.config'
    #topic = args.topic
    conf = ccloud_lib.read_ccloud_config(config_file)

    # Create Producer instance
    producer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
    producer = Producer(producer_conf)

    # Create topic 
    kafka_topic="coins_current_full"
    ccloud_lib.create_topic(conf, kafka_topic)

    delivered_records = 0
 
 # Poll the API every 3 seconds
    while True:
        # API URL and Payload
        base_url = "https://api.livecoinwatch.com/coins/list"
        payload = json.dumps({
            "currency": "USD",
            "sort": "rank",
            "order": "ascending",
            "offset": 0,
            "limit": 10,  # top 10
            "meta": True
        })

        # Headers for the API request
        headers = {
            'content-type': 'application/json',
            'x-api-key': api_key
        }

        # Fetch the data from the API
        response = requests.request("POST", base_url, headers=headers, data=payload)

        if response.status_code == 200:
            data = response.json()
            
            # Send each row of the data to Kafka
            for coin in data:
                crank = coin.get('rank')
                producer.produce(kafka_topic, key=str(crank), value=json.dumps(coin))
                producer.flush()  # Ensure the message is delivered
                print(f"Message sent to Kafka: {coin}")
    
        else:
            print(f"Failed to fetch data: {response.status_code} - {response.text}")

        time.sleep(3)

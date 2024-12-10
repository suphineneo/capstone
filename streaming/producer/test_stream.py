from dotenv import load_dotenv
import requests 
import os
import json
#import utilities.ccloud_lib as ccloud_lib
import logging
import sys
#from utilities.process_streams import process_streams
#from confluent_kafka.cimpl import Producer


if __name__ == '__main__':
   
    load_dotenv()
    api_key = os.environ.get("crypto_api_key")
    
    base_url = "https://api.livecoinwatch.com/coins/list"

    payload = json.dumps({
    "currency": "USD",
    "sort": "rank",
    "order": "ascending",
    "offset": 0,
    "limit": 10, #top10
    "meta": False
    })
    headers = {
    'content-type': 'application/json',
    'x-api-key': api_key
    }

    response = requests.request("POST", base_url, headers=headers, data=payload)

    print(response.text)
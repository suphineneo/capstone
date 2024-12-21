# Capstone Project (Dec 2024): Data Streaming Application

## Introduction:

I purchased a handful of Solana on 21 May 2023 because i wanted to get a NFT Sneaker (https://www.stepn.com/- a Web3 lifestyle application that rewards users for outdoor movement with NFT Sneakers and Tokens). Since then, i have seen the price of Solana soar to great heights.

![IMG_0715_my_stepn_sneaker](https://github.com/user-attachments/assets/bcaccfe9-e11d-4499-9bce-ac77108931f3)


## Objective: Capture and store real time Cryptocurrency coins price data in ClickHouse

Application for analysts and traders:
> - Real-time Analytics: Query real time data for identifying opportunities and making trading decisions.
> - Technical Indicators: Develop and chart technical indicators like 10 day, 30 day moving averages.
> - Risk Management: Analyze market volatility.
> - Performance Tracking: Monitor the performance of coins over time.

Metabase dashboards:
![image](https://github.com/user-attachments/assets/1787b69e-d1cb-4830-8a01-b2fd7c19b1f7)

<img width="913" alt="image" src="https://github.com/user-attachments/assets/fed59971-ecf6-4ee4-871c-3010939c4b0e" />


## Source: 
> - Subscribed to https://www.livecoinwatch.com/ API as there is documentation (https://livecoinwatch.github.io/lcw-api-docs/#coinssingle) and it seemed straightforward.
> - API Daily Limit: 10,000
> - Used 2 APIs:
> - For current values: url = "https://api.livecoinwatch.com/coins/map"
> - For historical values: url = "https://api.livecoinwatch.com/coins/single/history".

**Challenges with getting a daily close for historical data**:
-	Cryptocurrency market does not sleep. Trading happens 24/7, 365 days a year.
-	History API from Livecoinwatch does not return a daily close. So I had to define price at 12:00 UTC as the daily close.
-	After some testing, I realise I have to pass in the same datetime as start and end date params to get specifically daily 12:00 UTC price, i.e., 1 API call per date. Took a while to fetch historical data from 1 Jan 2024 to current date for 10 coins.
- For Future improvement: Refine the way daily close is retrieved. Without a daily limit, the price at 12:00 UTC can be retrieved from the current value API and a seperate historical api is not necessary.

## Architecture Diagram: 




## Process flow:
- stream.py: producer sends current data from  API into a Kafka topic '**coins_current_full**' hosted on confluent cloud.
- historical.py: producer sends historical data from API into a separate Kafka topic '**coins_historical**' hosted on confluent cloud.
- Using ksqldb, a stream and 2 tables ('**ohlc_by_minute**', '**60_sec_mov_avg**') were created. Window Tumbling and Hopping were applied to the real time streaming data to compute open, high, low, close prices by minute, and a moving average every 60 seconds.
```bash
(Tumbling)
CREATE TABLE ohlc_by_minute WITH (KAFKA_TOPIC='ohlc_by_minute', value_format='JSON') 
AS
SELECT
TIMESTAMPTOSTRING(WINDOWSTART, 'yyyy-MM-dd HH:mm') as window_start,
code,
EARLIEST_BY_OFFSET(rate) as open,
max(rate) as high,
min(rate) as low,
LATEST_BY_OFFSET(rate) as close
from COINS_CURRENT_STREAM 
WINDOW TUMBLING (SIZE 1 MINUTE)
GROUP BY code
EMIT CHANGES;
```
```bash
(Hopping)
CREATE TABLE 60_sec_mov_avg WITH (KAFKA_TOPIC='60_sec_mov_avg', value_format='JSON') 
AS
SELECT 
TIMESTAMPTOSTRING(WINDOWSTART, 'yyyy-MM-dd HH:mm:ss') as window_start,
code,
avg(rate) as 60_sec_mov_avg
from COINS_CURRENT_STREAM 
WINDOW HOPPING (SIZE 60 SECONDS, ADVANCE BY 30 SECONDS)
group by code
EMIT CHANGES;
```
<img width="556" alt="image" src="https://github.com/user-attachments/assets/0614b2e6-46a8-4d39-b2ae-7cd018cf7dc6" />
<img width="542" alt="image" src="https://github.com/user-attachments/assets/4e1e4d3b-f238-457e-89d7-daaeab7350ee" />


- The following Clickpipes were created for each of the 4 Kafka topic
  <img width="757" alt="image" src="https://github.com/user-attachments/assets/816fe078-f035-4c47-8e82-fc032089fc2e" />

- In Clickhouse, several views are created based on the data loaded from clickpipes.
  <img width="424" alt="image" src="https://github.com/user-attachments/assets/e7d46826-cb27-483e-9aad-4f15f5f682a2" />

- *For the full list of transformation scripts, refer to https://github.com/suphineneo/capstone/blob/update_readme/clickhouse_scripts.md

  Examples:
```bash
-- Returns open high low close price for the CURRENT day. 
-- Values will change while data is streaming.
-- Used in metabase dashboard
CREATE VIEW v_ohlc_by_day AS 
SELECT
  toStartOfDay(toDate(_timestamp)) as date,
  code,
  name,
  argMin(rate, _timestamp) as open,
  max(rate) as high,
  min(rate) as low,
  argMax(rate, _timestamp) as close,
  max(allTimeHighUSD) as allTimeHigh,
  max(volume) as volume
FROM "coins_current_full"
GROUP BY date, code, name
ORDER BY date, code;
```
```bash
-- Returns % change between latest record and previous record
-- Values will change while data is streaming.
-- Used in metabase dashboard
CREATE VIEW v_change_by_second AS
SELECT
    _timestamp,
    code,
    name,
    rate,
    allTimeHighUSD,
    volume,
    cap,
    totalSupply,
    anyOrNull(rate) OVER (
        PARTITION BY code 
        ORDER BY _timestamp
        ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING
    ) AS previous_rate,
    (rate - previous_rate)/previous_rate*100 as change
FROM coins_current_full
ORDER BY _timestamp
```

## Testing:
- Used a ClickHouse Connect client instance to connect to a ClickHouse Cloud service in python (https://clickhouse.com/docs/en/integrations/python)
- Used pytest to test my ClickHouse views
  
```bash
cd streaming
python -m pytest
```
<img width="178" alt="image" src="https://github.com/user-attachments/assets/3de98735-0b6f-49f3-8184-a3dbd650cf1e" />

## GitHub Actions



## Build Docker container image and Deploy to AWS:
```bash
docker build --platform=linux/amd64 -t main .

docker run --env-file .env main:latest
```
- Login to AWS CLI
- Authenticate your Docker client to your registry
- Tag and push

```bash
aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin 443370714728.dkr.ecr.ap-southeast-1.amazonaws.com/coins

docker tag main:latest ${CONTAINER_REGISTRY_URL}/coins:latest
docker push ${CONTAINER_REGISTRY_URL}/coins:latest

```
- After the push, the image is reflected in AWS.

- Elastic Container Registry (ECR) - screenshot of image in ECR
 ![image](https://github.com/user-attachments/assets/7a45a41d-b061-4737-87d3-1938de6e8564)

- Task Definition – Container is pointing to image in ECR
 ![image](https://github.com/user-attachments/assets/efb06a17-d9be-4218-b4f3-f2bf3b96a4f1)


- Elastic Container Service (ECS) - screenshot of task in ECS
![image](https://github.com/user-attachments/assets/53a7e526-26ee-4f29-885d-389dad973d34)

- Screenshot of messages produced to Kafka topic
![image](https://github.com/user-attachments/assets/4248c16f-d495-4ff1-9353-4bf0df0ac954)
![image](https://github.com/user-attachments/assets/e3f5414a-9f6c-4064-a316-f6d8682c53f0)


 
 









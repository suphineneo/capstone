## Transformations in Clickhouse:

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
 
-- Creates CTE for the latest record only from v_change_by_second
-- Joins with historical table to get the latest 1d change and 7d change
-- Values will change while data is streaming.
-- Used in metabase dashboard
CREATE VIEW  overview_for_dashboard
AS 
WITH v_change_by_second_latest AS
 ( SELECT
  code,
  name,
  argMax(rate, _timestamp) as latest_rate,
  argMax(change, _timestamp) as latest_change,
  argMax(allTimeHighUSD, _timestamp) as allTimeHigh,
  argMax(volume, _timestamp) as volume,
  argMax(cap, _timestamp) as cap,
  argMax(totalSupply, _timestamp) as totalSupply,
  max(_timestamp) as latest_ts
FROM v_change_by_second
GROUP BY code, name
 )
 select
 latest.code, 
 latest.name, 
 latest_rate, 
 latest_change, 
 latest.allTimeHigh, 
 latest.volume, 
 latest.cap, 
 latest.totalSupply,
 hist.last_hist_rate as previous_day_rate,
 (latest_rate - previous_day_rate)/previous_day_rate*100 as 1d_change,
 hist.last_previous_rate_7d as previous_rate_7d,
 (latest_rate - previous_rate_7d)/previous_rate_7d*100 as 7d_change
 from v_change_by_second_latest latest
 left join v_change_by_day_latest hist on hist.code = latest.code

-- STAGING table for historical data because data is in an array of JSON
CREATE TABLE coins_daily_historical_stage
(   code String,  
    name String,
    rank Integer,
    allTimeHighUSD Float32,
    circulatingSupply Float32,
    totalSupply Float32,
    json_daily_data String
) ENGINE = MergeTree ORDER BY (code)

-- Splits the data from JSON into columns
-- Returns a daily price (12:00 UTC) per day from 1 Jan 2024
-- Used in metabase dashboard
CREATE VIEW v_hist_daily AS
WITH json_format AS
(SELECT 
    code,
    name,
    rank,
    allTimeHighUSD,
    --circulatingSupply,
    --totalSupply,
    arrayJoin(JSONExtractArrayRaw(json_daily_data)) as hist_data
    FROM "coins_daily_historical_stage"
)
SELECT     
    code,
    name,
    rank,
    allTimeHighUSD,
    --circulatingSupply,
    --totalSupply,
    fromUnixTimestamp(toInt64(divide(JSONExtract(hist_data, 'date', 'Int64'),1000))) as date,
    --JSONExtract(hist_data, 'date', 'Int64') as date,
    JSONExtract(hist_data, 'rate', 'Float32') AS rate,
    JSONExtract(hist_data, 'volume', 'Float32') AS volume,
    JSONExtract(hist_data, 'cap', 'Float32') AS cap,
    JSONExtract(hist_data, 'liquidity', 'Float32') AS liquidity
FROM json_format
ORDER BY code, date;

-- Returns 10 day moving average
-- Used in metabase dashboard
CREATE VIEW v_10_day_mov_avg
AS
SELECT
    code,
    name,
    toDate(date) as date,
    rate,
    avg(rate) OVER (PARTITION BY code ORDER BY date 
       ROWS BETWEEN 10 PRECEDING AND CURRENT ROW) AS 10_day_mov_avg
FROM v_hist_daily
ORDER BY
    code ASC, name ASC,
    date ASC;


--Returns 1 day and 7 day % change based on last record for each record in historical table.
CREATE VIEW v_change_by_day
AS SELECT
    code,
    name,
    toDate(date) as date,
    volume,
    cap,
    liquidity,
    allTimeHighUSD,
    rate,
    anyOrNull(rate) OVER (
        PARTITION BY code 
        ORDER BY date
        ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING
    ) AS previous_rate_1d,
    ROUND((rate - previous_rate_1d)/previous_rate_1d*100,4) as 1d_change,
    anyOrNull(rate) OVER (
        PARTITION BY code 
        ORDER BY date
        ROWS BETWEEN 7 PRECEDING AND 7 PRECEDING
    ) AS previous_rate_7d,
    ROUND((rate - previous_rate_7d)/previous_rate_7d*100,4) as 7d_change
FROM v_hist_daily
ORDER BY date desc

-- Returns only the latest record from v_change_by_day
-- Used in metabase dashboard
CREATE VIEW v_change_by_day_latest
AS
SELECT 
code,
name,
max(date) as last_hist_date,
argMax(rate, date) as last_hist_rate,
argMax(previous_rate_1d, date) as last_previous_rate_1d,
argMax(previous_rate_7d, date) as last_previous_rate_7d
FROM
v_change_by_day
group by code, name

```

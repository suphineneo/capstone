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

## Source: 
> - Subscribed to https://www.livecoinwatch.com/ API as there is documentation (https://livecoinwatch.github.io/lcw-api-docs/#coinssingle) and it seemed straightforward.
> - API Daily Limit: 10,000
> - Used 2 APIs:
> - For current values: url = "https://api.livecoinwatch.com/coins/map"
> - For historical values: url = "https://api.livecoinwatch.com/coins/single/history".

**Challenges with getting a daily close for historical data**:
-	Cryptocurrency market does not sleep. Trading happens 24/7, 365 days a year.
-	History API from Livecoinwatch does not return a daily close. So I had to define price at 12:00 UTC as the daily close.
-	After some testing, I realise I have to pass in the same datetime as start and end date params to get exactly daily 12:00 UTC, i.e., 1 API call per date. Took a while to fetch historical data from 1 Jan 2024 to current date for 10 coins.
- For Future improvement: Refine the way daily close is retrieved. Without a daily limit, the price at 12:00 UTC can be retrieved from the current value API and a seperate historical api is not necessary.




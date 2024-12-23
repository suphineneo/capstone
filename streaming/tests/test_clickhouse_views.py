import clickhouse_connect
import pytest
import pandas as pd


@pytest.fixture
def connect_to_clickhouse():
    CLICKHOUSE_CLOUD_HOSTNAME = "mbhgy1qvki.ap-southeast-1.aws.clickhouse.cloud"
    CLICKHOUSE_CLOUD_USER = "default"
    CLICKHOUSE_CLOUD_PASSWORD = "zwJ_1o_e5HEi4"

    client = clickhouse_connect.get_client(
        host=CLICKHOUSE_CLOUD_HOSTNAME,
        port=8443,
        username=CLICKHOUSE_CLOUD_USER,
        password=CLICKHOUSE_CLOUD_PASSWORD,
    )

    print("connected to " + CLICKHOUSE_CLOUD_HOSTNAME + "\n")

    # result = client.query('SELECT * FROM v_hist_daily LIMIT 2')
    # print(result.result_rows)

    return client


@pytest.fixture
def coin_code_name_df():
    code_name_mapping = [
        {"code": "AAVE", "name": "Aave"},
        {"code": "BTC", "name": "Bitcoin"},
        {"code": "DOGE", "name": "Dogecoin"},
        {"code": "ETH", "name": "Ethereum"},
        {"code": "FDUSD", "name": "First Digital USD"},
        {"code": "LINK", "name": "Chainlink"},
        {"code": "SOL", "name": "Solana"},
        {"code": "USDC", "name": "USDC"},
        {"code": "USDT", "name": "Tether"},
        {"code": "XRP", "name": "XRP"},
    ]
    df = pd.DataFrame(code_name_mapping, dtype="str")

    return df


def test_valid_code_name(connect_to_clickhouse, coin_code_name_df):
    client = connect_to_clickhouse
    clickhouse_data = client.query_df(
        "SELECT distinct code, name FROM coins_current_full order by code"
    )
    clickhouse_data = pd.DataFrame(clickhouse_data, dtype="str")

    pd.testing.assert_frame_equal(
        left=clickhouse_data, right=coin_code_name_df, check_exact=True
    )


# create a test that verifies high is > low in ohlc
def test_ohlc_logic(connect_to_clickhouse):
    client = connect_to_clickhouse
    clickhouse_data = client.query_df(
        "SELECT distinct(less(high - low, 0)) as high_low FROM v_ohlc_by_day"
    )
    clickhouse_data["high_low"] = clickhouse_data["high_low"].astype("int64")

    expected_value = [
        {"high_low": 0}
    ]  # high must be >= low in ohlc so the expected value of less(high-low) is 0
    expected_value = pd.DataFrame(expected_value, dtype="int64")

    pd.testing.assert_frame_equal(
        left=clickhouse_data, right=expected_value, check_exact=True
    )

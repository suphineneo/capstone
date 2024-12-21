from datetime import datetime, timezone, timedelta
import csv

# NOTES: The crypto market is 24/7 so there is no end of day close price. I set 12:00 UTC as the eod close to get a daily price for historical data.
# After some testing, due to behaviour of the hist API, I realise I have to pass in the same datetime as start and end date to get exactly daily 12:00 UTC
# For example, if i pass in 1/1/2024 to 12/12/2024 in one API call, alot of data points are skipped, probably due to limits. Because there would be too much data points.
# Hence i need to make 1 API call per date. Not ideal. Prob will find a better way to do it if i have more time.
# if got time, place csv file in s3


def get_date_range() -> dict[str, float]:
    # Note: If file is empty, this is the first load. Get 2024 Jan to current date.
    # Subsequent load will be incremental
    last_date_filename = "data/hist_last_date_loaded.csv"
    last_date_loaded = get_last_loaded_date(last_date_filename)

    if last_date_loaded is None:

        # If file is empty, this is the first load. Get 2024/1/1 to current date.
        start_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        end_dt = datetime(2024, 7, 31, 12, 0, 0, tzinfo=timezone.utc)
        # end_dt = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
        print(f"First load - Data will be loaded from {start_dt} to {end_dt}")
    else:

        # incremental load. start date is last loaded date + 1 while end date is current date.
        start_dt = last_date_loaded + timedelta(days=1)
        start_dt = start_dt.replace(hour=12, minute=0, second=0, microsecond=0)
        start_dt = start_dt.replace(tzinfo=timezone.utc)
        end_dt = datetime.now(timezone.utc).replace(
            hour=12, minute=0, second=0, microsecond=0
        )

        print(f"Incremental load - Data will be loaded from {start_dt} to {end_dt}")

    date_dict = {}

    current_date = start_dt
    while current_date <= end_dt:
        # Get the UNIX timestamp for the current date (in milliseconds)
        unix_timestamp = current_date.timestamp() * 1000

        # Add to the dictionary with the regular date as key and UNIX timestamp as value
        date_dict[current_date.strftime("%Y-%m-%d")] = unix_timestamp

        # Move to the next day
        current_date += timedelta(days=1)

    # write the end date into csv for subsequent incremental load
    store_end_date(end_dt, last_date_filename)

    return date_dict


def store_end_date(end_date, last_date_filename):

    last_date_loaded = end_date.strftime("%Y-%m-%d")  # Format as 'YYYY-MM-DD'
    try:
        with open(last_date_filename, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([last_date_loaded])

        print(f"{last_date_loaded} recorded into file")

    except Exception as e:
        print(f"Error writing to {last_date_filename}: {e}")


def get_last_loaded_date(last_date_filename):

    try:
        # Open the file to get the last loaded date
        with open(last_date_filename, mode="r", newline="") as file:
            reader = csv.reader(file)
            row = next(reader, None)
            if row is None or len(row) == 0 or row[0] == "":
                return None
            last_date_loaded = row[0]
            last_date_loaded = datetime.strptime(last_date_loaded, "%Y-%m-%d")
            print(f"last_date_loaded= {last_date_loaded}")
            return last_date_loaded

    except FileNotFoundError:
        print(f"File {last_date_filename} not found.")
        return None
    except Exception as e:
        print(f"Error reading the file: {e}")
        return None

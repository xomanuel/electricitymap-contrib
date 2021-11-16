import datetime
import json
import time
from io import StringIO
from time import sleep

import arrow
import pandas as pd
import requests
from dateutil import tz
from tqdm import tqdm

APG_API_BASE = "https://transparency.apg.at/transparency-api/api/v1"
EXCHANGE_API = "{}/Download/CBPF/German/M15".format(APG_API_BASE)

# column names
COL_FROM = "Zeit von [CET/CEST]"
COL_TO = "Zeit bis [CET/CEST]"
COL_CZ_AT = "CZ>AT Leistung [MW]"
COL_HU_AT = "HU>AT Leistung [MW]"
COL_SI_AT = "SI>AT Leistung [MW]"
COL_IT_AT = "IT>AT Leistung [MW]"
COL_CH_AT = "CH>AT Leistung [MW]"
COL_DE_AT = "DE>AT Leistung [MW]"
EXCHANGE_COLS = [COL_CZ_AT, COL_HU_AT, COL_SI_AT, COL_IT_AT, COL_CH_AT, COL_DE_AT]

# for each interconnector a function which retrieves the desired value from a dict or Series
# when the direction changes, we need to multiply by -1
EXCHANGES = {
    "AT->CH": lambda d: -1 * d[COL_CH_AT],
    "AT->CZ": lambda d: -1 * d[COL_CZ_AT],
    "AT->DE": lambda d: -1 * d[COL_DE_AT],
    "AT->IT": lambda d: -1 * d[COL_IT_AT],
    "AT->HU": lambda d: -1 * d[COL_HU_AT],
    "AT->SI": lambda d: -1 * d[COL_SI_AT],
}


def format_date(date: datetime.date) -> str:
    """
    Format a date as expected by the APG api
    Return: the date object as formatted string
    """
    return "{}T000000".format(date.isoformat())


def fetch_exchange(
    zone_key1, zone_key2, session=None, target_datetime=None, logger=None
):
    exchange = "->".join(sorted([zone_key1, zone_key2]))
    if exchange not in EXCHANGES:
        raise ValueError(
            "The requested exchange {} is not supported by the AT parser".format(
                exchange
            )
        )

    if target_datetime is None:
        date = arrow.utcnow().floor("day")
    else:
        date = arrow.get(target_datetime).to("utc")

    # TODO do we really need to fetch the document for each and every interconnector separately?
    exchange_data_of_day = fetch_exchanges_for_date(date, session=session).dropna()

    data = []
    for _, row in exchange_data_of_day.iterrows():
        flow = EXCHANGES[exchange](row)
        row_data = {
            "sortedZoneKeys": exchange,
            "datetime": row.datetime.to_pydatetime(),
            "netFlow": flow,
            "source": "transparency.apg.at",
        }
        data.append(row_data)

    return data


def fetch_exchanges_for_date(date: arrow.Arrow, session=None) -> pd.DataFrame:
    """
    Fetches all Austrian exchanges for a given date.
    Return: the exchange values of the requested day as a pandas DataFrame
    """
    # build the request url
    from_date = format_date(date.date())
    to_date = format_date(date.shift(days=+1).date())
    export_request_url = "{}/{}/{}".format(EXCHANGE_API, from_date, to_date)

    s = session or requests.Session()

    # perform the request which creates the export file
    resp = s.get(export_request_url)
    resp.raise_for_status()

    try:
        export_url_response = resp.json()["ResponseData"]
        cache_id = export_url_response["Cache_ID"]
        filename = export_url_response["FileName"]
    except:
        raise ValueError(
            "The response to the request for generating the csv file has an unexpected format."
        )

    # fetch the csv file which was created by the previous request
    csv_url = "{}/{}/{}".format(export_request_url, cache_id, filename)
    csv_response = s.get(csv_url)
    csv_response.raise_for_status()

    # override encoding by real educated guess as provided by chardet
    csv_response.encoding = csv_response.apparent_encoding
    csv_str = csv_response.text

    # create a dt index that is not sensitive to daylight saving time
    dt_index = pd.date_range(
        date.replace(tzinfo=None).format("YYYY-MM-DD HH:mm:ss"),
        date.shift(days=+1).replace(tzinfo=None).format("YYYY-MM-DD HH:mm:ss"),
        freq="15min",
        tz="Europe/Vienna",
    )
    dt_index = dt_index[:-1]

    try:
        csv_data = pd.read_csv(
            StringIO(csv_str),
            delimiter=";",
            dayfirst=True,
        )
        csv_data.loc[:, "datetime"] = dt_index
        csv_data = csv_data.drop(columns=[COL_FROM, COL_TO])
    except:
        raise ValueError("The downloaded csv file has an unexpected format")

    # parse float values (AT locale uses ',' instead of '.')
    csv_data[EXCHANGE_COLS] = (
        csv_data[EXCHANGE_COLS]
        .replace(to_replace=",", value=".", regex=True)
        .apply(pd.to_numeric)
    )

    return csv_data


# TODO: have script running to fetch data back in time.
def fetch_historical_exchanges():
    # Daily data
    countries = [ex.split("AT->")[1] for ex in EXCHANGES.keys()]
    to_fetch_datetimes = pd.date_range("2018-12-31", "2021-01-01", freq="D")
    _dfs = []
    inner_break = False
    for country in tqdm(countries):
        if inner_break:
            break
        with tqdm(total=len(to_fetch_datetimes)) as pbar:
            sleep(1)
            for i, dt in enumerate(to_fetch_datetimes):
                if i % 7 == 0:
                    pbar.set_description("Fetching {}".format(country))
                    pbar.update(7)
                try:
                    exchanges = fetch_exchange(
                        "AT",
                        country,
                        target_datetime=datetime.datetime(
                            year=dt.year, month=dt.month, day=dt.day
                        ),
                    )
                except BaseException as e:
                    print(f"Something went wrong, stopping fetching. {e}")
                    inner_break = True
                    break
                _dfs.append(pd.DataFrame.from_records(exchanges))

    all_exchanges_df = pd.concat(_dfs)
    all_exchanges_df = all_exchanges_df[
        all_exchanges_df.datetime >= "2019-01-01 00:00:00+01:00"
    ]
    all_exchanges_df = all_exchanges_df[
        all_exchanges_df.datetime <= "2020-12-31 23:00:00+01:00"
    ]
    all_exchanges_df.to_csv("at_exchanges.csv", index=False)


# TODO what dooes this do ?
def check_delay():
    while True:
        # run at every full minute
        now = arrow.utcnow()
        sleep_time = (now.ceil("minute") - now).seconds + 1
        if sleep_time > 0:
            time.sleep(sleep_time)

        try:
            exchange_data = fetch_exchanges_for_date(datetime.date.today())

            last_row = exchange_data.dropna().iloc[-1]
            end_date = last_row[COL_TO]

            if end_date.isoformat() not in STORAGE:
                delta = datetime.datetime.now() - end_date
                last_row["Delay [Minutes]"] = delta.seconds / 60
                STORAGE[end_date.isoformat()] = last_row.astype(str).to_dict()
                print("Encountered new exchange data with delay {}".format(delta))
            else:
                print("No new data is available")

            with open(STORAGE_FILE, "w") as f:
                json.dump(STORAGE, f)
        except Exception as e:
            print("An error occurred while checking the delay: {}".format(e))


STORAGE = {}
STORAGE_FILE = "delay_storage.json"


if __name__ == "__main__":
    # print("Fetching exchange AT->DE")
    # print(fetch_exchange("AT", "DE"))
    # print("Fetching exchange AT->DE for 2013-01-01")
    # print(
    #     fetch_exchange(
    #         "AT", "DE", target_datetime=datetime.datetime(year=2013, month=1, day=1)
    #     )
    # )
    fetch_historical_exchanges()

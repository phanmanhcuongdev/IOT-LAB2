
import pandas as pd
import numpy as np
from influxdb_client import Point
from influxdb_client.client.write_api import SYNCHRONOUS

from influxdb_client import InfluxDBClient

from mqtt_client import (
    INFLUX_URL, INFLUX_TOKEN,
    INFLUX_ORG, INFLUX_BUCKET
)


def read_data():
    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -2h)
      |> filter(fn: (r) => r._measurement == "sensor_data")
      |> filter(fn: (r) => r.device == "esp32")
      |> pivot(
          rowKey: ["_time"],
          columnKey: ["_field"],
          valueColumn: "_value"
      )
      |> sort(columns: ["_time"])
    '''

    with InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG
    ) as client:
        df = client.query_api().query_data_frame(query)

    return df

def handle_missing(df):
    columns = ["temperature", "humidity", "distance_cm"]

    print("Missing truoc xu ly:")
    print(df[columns].isna().sum())

    df = df.copy()

    df[columns] = df[columns].interpolate(
        method="linear",
        limit_direction="both"
    )

    print("Missing sau xu ly:")
    print(df[columns].isna().sum())

    return df

def handle_outliers(df):
    df = df.copy()
    columns = ["temperature", "humidity", "distance_cm"]

    for col in columns:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1

        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        mask = (df[col] < lower) | (df[col] > upper)

        print(f"{col}: {mask.sum()} outliers")

        # Thay outlier bang trung vi
        df.loc[mask, col] = df[col].median()

    return df


def process_data(df):
    df = df.copy()

    # Su dung timestamp lam index
    df["_time"] = pd.to_datetime(df["_time"], utc=True)
    df = df.set_index("_time").sort_index()

    columns = ["temperature", "humidity", "distance_cm"]

    # Resampling moi 10 giay
    df = df[columns].resample("10s").mean()

    # Xu ly missing sau resampling
    df = df.interpolate(method="time", limit_direction="both")

    # Tao dac trung
    df["temp_rolling_mean"] = df["temperature"].rolling(
        window=3, min_periods=1
    ).mean()

    df["temp_delta"] = df["temperature"].diff().fillna(0)

    # Chuan hoa Min-Max
    for col in columns:
        min_val = df[col].min()
        max_val = df[col].max()

        if max_val > min_val:
            df[col + "_normalized"] = (
                (df[col] - min_val) / (max_val - min_val)
            )
        else:
            df[col + "_normalized"] = 0.0

    return df


def save_processed(df):
    points = []

    for timestamp, row in df.iterrows():
        point = Point("sensor_processed").tag("device", "esp32")

        for col in df.columns:
            point.field(col, float(row[col]))

        point.time(timestamp.to_pydatetime())
        points.append(point)

    with InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG
    ) as client:
        client.write_api(write_options=SYNCHRONOUS).write(
            bucket=INFLUX_BUCKET,
            org=INFLUX_ORG,
            record=points
        )

    print(f"Da luu {len(points)} ban ghi da xu ly")


if __name__ == "__main__":
    df = read_data()

    print("So dong ban dau:", len(df))

    df = handle_missing(df)
    df = handle_outliers(df)
    df = process_data(df)

    print("So dong sau resampling:", len(df))
    print(df.tail())

    save_processed(df)
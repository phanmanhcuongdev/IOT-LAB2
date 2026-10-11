import time
import os
import json
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# MQTT Configuration
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "ptit/iot/cuongdso/lab2/telemetry"

# InfluxDB Configuration
INFLUX_URL = "http://localhost:8086"
INFLUX_ORG = "admin"
INFLUX_BUCKET = "iot-th-2"
INFLUX_TOKEN = "ijdkD2IWI7NoNJjlM-3XBF9QZu5XL19F5rfzf8ORS-kEEf3Eqd4olXKWF_LHMFmD_tt1XnyliOxNEzYEVtWKAg=="


def validate(data):
    required = ["temperature", "humidity", "distance_cm"]

    if not isinstance(data, dict):
        return False

    for field in required:
        if field not in data:
            return False

        if isinstance(data[field], bool):
            return False

        if not isinstance(data[field], (int, float)):
            return False

    return True


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("MQTT connected", flush=True)
        client.subscribe(TOPIC)
        print("Subscribed:", TOPIC, flush=True)
    else:
        print("MQTT connection failed:", reason_code, flush=True)


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode("utf-8"))

        if not validate(data):
            print("Du lieu khong hop le:", data, flush=True)
            return

        print("Du lieu hop le:", data, flush=True)

        point = (
            Point("sensor_data")
            .tag("device", "esp32")
            .field("temperature", float(data["temperature"]))
            .field("humidity", float(data["humidity"]))
            .field("distance_cm", float(data["distance_cm"]))
        )

        start = time.perf_counter()

        userdata.write(
            bucket=INFLUX_BUCKET,
            org=INFLUX_ORG,
            record=point
        )

        latency_ms = (time.perf_counter() - start) * 1000
        print(f"InfluxDB write latency: {latency_ms:.2f} ms")

        print("Da ghi InfluxDB", flush=True)

    except (ValueError, UnicodeDecodeError) as e:
        print("Loi du lieu:", e, flush=True)

    except Exception as e:
        print("Loi ghi database:", e, flush=True)


def main():
    with InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG
    ) as influx_client:

        write_api = influx_client.write_api(
            write_options=SYNCHRONOUS
        )

        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

        client.user_data_set(write_api)
        client.on_connect = on_connect
        client.on_message = on_message

        try:
            print("Connecting to MQTT Broker...", flush=True)
            client.connect(BROKER, PORT)
            client.loop_forever()

        except KeyboardInterrupt:
            print("Stopped")

        finally:
            client.disconnect()
            write_api.close()


if __name__ == "__main__":
    main()

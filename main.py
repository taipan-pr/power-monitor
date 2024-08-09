import os
import time
from dotenv import find_dotenv, load_dotenv
from influxclient import InfluxClient
from powerclamp import SolarPowerClamp, MainPowerClamp


def create_device():
    name = os.getenv("METER_NAME")
    if name == "MAIN":
        return MainPowerClamp(name=name,
                              device_id=os.getenv("METER_DEVICE_ID"),
                              key=os.getenv("METER_LOCAL_KEY"),
                              ip=os.getenv("METER_DEVICE_IP"),
                              delay_seconds=int(os.getenv("DELAY_SECS")))
    elif name == "SOLAR":
        return SolarPowerClamp(name=name,
                               device_id=os.getenv("METER_DEVICE_ID"),
                               key=os.getenv("METER_LOCAL_KEY"),
                               ip=os.getenv("METER_DEVICE_IP"),
                               delay_seconds=int(os.getenv("DELAY_SECS")))


def process(influxdb):
    power_clamp = create_device()

    if power_clamp is None:
        print("Device not found")
        return False

    while True:
        status = power_clamp.status()
        print(status)
        power_clamp.publish_data(influxdb, status['dps'])
        time.sleep(power_clamp.delay_seconds)


def main():
    print(f"Process start")

    # load environment variables
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    influxdb = InfluxClient(url=os.getenv("INFLUXDB_URL"),
                            token=os.getenv("INFLUXDB_TOKEN"),
                            org=os.getenv("INFLUXDB_ORG"),
                            bucket=os.getenv("INFLUXDB_BUCKET"))
    process(influxdb)


if __name__ == "__main__":
    main()

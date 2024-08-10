import os
import time
from dotenv import find_dotenv, load_dotenv
from influxclient import InfluxClient
from powerclamp import SolarPowerClamp, MainPowerClamp


def create_device():
    name = os.getenv("METER_NAME")

    if name == "MAIN":
        return MainPowerClamp(name=name,
                              meter_id=os.getenv("METER_DEVICE_ID"),
                              key=os.getenv("METER_LOCAL_KEY"),
                              ip=os.getenv("METER_DEVICE_IP"),
                              delay_seconds=int(os.getenv("DELAY_SECS")),
                              switch_ip=os.getenv("SWITCH_IP"),
                              switch_id=os.getenv("SWITCH_DEVICE_ID"),
                              switch_key=os.getenv("SWITCH_LOCAL_KEY"),
                              error_threshold=int(os.getenv("ERROR_THRESHOLD")),
                              switch_delay=int(os.getenv("SWITCH_DELAY")))
    elif name == "SOLAR":
        return SolarPowerClamp(name=name,
                               meter_id=os.getenv("METER_DEVICE_ID"),
                               key=os.getenv("METER_LOCAL_KEY"),
                               ip=os.getenv("METER_DEVICE_IP"),
                               delay_seconds=int(os.getenv("DELAY_SECS")),
                               switch_ip=os.getenv("SWITCH_IP"),
                               switch_id=os.getenv("SWITCH_DEVICE_ID"),
                               switch_key=os.getenv("SWITCH_LOCAL_KEY"),
                               error_threshold=int(os.getenv("ERROR_THRESHOLD")),
                               switch_delay=int(os.getenv("SWITCH_DELAY")))


def process(influxdb):
    power_clamp = create_device()

    if power_clamp is None:
        print("Device not found")
        return False

    while True:
        status = power_clamp.status()
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

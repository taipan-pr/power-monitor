import logging
import os
from dotenv import find_dotenv, load_dotenv
from influxclient import InfluxClient
from powerclamp import SolarPowerClamp, MainPowerClamp


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_device(influxdb):
    name = os.getenv("METER_NAME")
    switch_enabled = os.getenv("SWITCH_ENABLED").lower() in ('True', 'true', 't', 'y', 'yes')

    if name == "MAIN":
        return MainPowerClamp(name=name,
                              influxdb=influxdb,
                              switch_enabled=switch_enabled)
    elif name == "SOLAR":
        return SolarPowerClamp(name=name,
                               influxdb=influxdb,
                               switch_enabled=switch_enabled)


def process(influxdb):
    power_clamp = create_device(influxdb)

    if power_clamp is None:
        logger.info("Device not found")
        return False

    power_clamp.status()


def main():
    logger.info(f"Process start")

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

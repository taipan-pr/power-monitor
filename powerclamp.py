import time
from abc import ABC, abstractmethod
import tinytuya


class PowerClamp(ABC):
    def __init__(self, name, device_id, key, ip, delay_seconds):
        self.name = name
        self.device_id = device_id
        self.key = key
        self.ip = ip
        self.delay_seconds = delay_seconds

        self.__device = tinytuya.Device(
            dev_id=self.device_id,
            address=self.ip,
            local_key=self.key,
            version=3.4)

    def status(self):
        try:
            while True:
                data = self.__device.status()
                if data and 'dps' in data:
                    return data

                self.__device.heartbeat()
                time.sleep(self.delay_seconds)

        except:
            raise Exception(f"Failed to get status from {self.name}")

    def update_dps(self):
        payload = self.__device.generate_payload(tinytuya.UPDATEDPS)
        self.__device.send(payload)

    @abstractmethod
    def publish_data(self, influxdb, status):
        pass


class MainPowerClamp(PowerClamp):
    def publish_data(self, influxdb, status):
        if status['102'] == 'FORWARD':
            influxdb.write({
                'name': 'PowerClamp',
                'type': 'ActivePowerA',
                'value': status['101']
            })
            influxdb.write({
                'name': 'PowerClamp',
                'type': 'ActivePowerC',
                'value': 0
            })
        elif status['102'] == 'REVERSE':
            influxdb.write({
                'name': 'PowerClamp',
                'type': 'ActivePowerA',
                'value': 0
            })
            influxdb.write({
                'name': 'PowerClamp',
                'type': 'ActivePowerC',
                'value': status['101']
            })


class SolarPowerClamp(PowerClamp):
    def publish_data(self, influxdb, status):
        if status['102'] == 'FORWARD':
            influxdb.write({
                'name': 'PowerClamp',
                'type': 'ActivePowerB',
                'value': 0
            })
        elif status['102'] == 'REVERSE':
            influxdb.write({
                'name': 'PowerClamp',
                'type': 'ActivePowerB',
                'value': status['101']
            })

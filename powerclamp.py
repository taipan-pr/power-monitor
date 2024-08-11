import time
from abc import ABC, abstractmethod
import tinytuya


class PowerClamp(ABC):
    def __init__(self,
                 name,
                 meter_id,
                 key,
                 ip,
                 delay_seconds,
                 switch_id,
                 switch_key,
                 switch_ip,
                 error_threshold,
                 switch_delay):

        self.name = name
        self.meter_id = meter_id
        self.key = key
        self.ip = ip
        self.delay_seconds = delay_seconds
        self.error_threshold = error_threshold
        self.switch_delay = switch_delay

        self.__device = tinytuya.OutletDevice(
            dev_id=self.meter_id,
            address=self.ip,
            local_key=self.key,
            version=3.4
        )

        self.__switch = tinytuya.OutletDevice(
            dev_id=switch_id,
            address=switch_ip,
            local_key=switch_key,
            version=3.3
        )

    def status(self):
        try:
            error_count = 0
            while True:
                data = self.__device.status()
                if data and 'dps' in data:
                    return data

                error_count += 1

                if error_count < self.error_threshold:
                    self.__device.heartbeat()
                else:
                    self.__switch.turn_off()
                    time.sleep(self.switch_delay)
                    self.__switch.turn_on()
                    time.sleep(self.switch_delay)
                    print('Power cycle')

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
        if '101' not in status and '102' not in status:
            return

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
        if '101' not in status and '102' not in status:
            return

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

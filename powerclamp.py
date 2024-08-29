import os
import time
from abc import ABC, abstractmethod
import tinytuya

import line


class PowerClamp(ABC):
    def __init__(self, name, influxdb, switch_enabled):

        self.name = name
        self.meter_id = os.getenv("METER_DEVICE_ID")
        self.key = os.getenv("METER_LOCAL_KEY")
        self.ip = os.getenv("METER_DEVICE_IP")
        self.delay_seconds = int(os.getenv("DELAY_SECS"))
        self.error_threshold = int(os.getenv("ERROR_THRESHOLD"))
        self.switch_delay = int(os.getenv("SWITCH_DELAY"))
        self.influxdb = influxdb
        self.switch_enabled = switch_enabled

        self.__device = tinytuya.OutletDevice(
            dev_id=self.meter_id,
            address=self.ip,
            local_key=self.key,
            version=3.4
        )

        self.__switch = tinytuya.OutletDevice(
            dev_id=os.getenv("SWITCH_DEVICE_ID"),
            address=os.getenv("SWITCH_IP"),
            local_key=os.getenv("SWITCH_LOCAL_KEY"),
            version=3.3
        )

    def status(self):
        try:
            current_data = None
            error_count = 0
            while True:
                data = self.__device.status()

                if data and 'dps' in data:
                    current_data = data

                    self.publish_data(data['dps'])

                    time.sleep(self.delay_seconds)
                    continue

                if current_data and 'dps' in current_data:
                    print('Could not get the status using previous data - ', current_data)
                    self.publish_data(current_data['dps'])

                self.__device.heartbeat()

                if not self.switch_enabled:
                    time.sleep(self.delay_seconds)
                    continue

                error_count += 1

                if error_count > self.error_threshold:
                    self.__switch.turn_off()
                    time.sleep(self.switch_delay)
                    self.__switch.turn_on()
                    time.sleep(self.switch_delay)
                    print('Power cycle')
                    error_count = 0

                time.sleep(self.delay_seconds)

        except:
            raise Exception(f"Failed to get status from {self.name}")

    def update_dps(self):
        payload = self.__device.generate_payload(tinytuya.UPDATEDPS)
        self.__device.send(payload)

    @abstractmethod
    def publish_data(self, status):
        pass


class MainPowerClamp(PowerClamp):
    def publish_data(self, status):
        if '101' not in status and '102' not in status:
            return

        if status['102'] == 'FORWARD':
            self.influxdb.write({
                'name': 'PowerClamp',
                'type': 'ActivePowerA',
                'value': status['101']
            })
            self.influxdb.write({
                'name': 'PowerClamp',
                'type': 'ActivePowerC',
                'value': 0
            })
        elif status['102'] == 'REVERSE':
            self.influxdb.write({
                'name': 'PowerClamp',
                'type': 'ActivePowerA',
                'value': 0
            })
            self.influxdb.write({
                'name': 'PowerClamp',
                'type': 'ActivePowerC',
                'value': status['101']
            })


class SolarPowerClamp(PowerClamp):
    def __init__(self, name, influxdb, switch_enabled):
        super().__init__(name, influxdb, switch_enabled)

        self.__inverter_status = InverterStatus.NONE

    def publish_data(self, status):
        if '101' not in status and '102' not in status:
            return

        if self.__inverter_status != InverterStatus.MALFUNCTION and status['101'] == 0:
            line.send_line_message("Inverter malfunction")
            self.__inverter_status = InverterStatus.MALFUNCTION

        if self.__inverter_status == InverterStatus.MALFUNCTION and status['101'] == 0:
            self.influxdb.write({
                'name': 'PowerClamp',
                'type': 'ActivePowerB',
                'value': 0
            })
            return

        if status['102'] == 'FORWARD':
            self.influxdb.write({
                'name': 'PowerClamp',
                'type': 'ActivePowerB',
                'value': 0
            })

            if self.__inverter_status != InverterStatus.STOPPED:
                line.send_line_message('Inverter stopped')
                self.__inverter_status = InverterStatus.STOPPED

        elif status['102'] == 'REVERSE':
            self.influxdb.write({
                'name': 'PowerClamp',
                'type': 'ActivePowerB',
                'value': status['101']
            })

            if self.__inverter_status != InverterStatus.WORKING:
                line.send_line_message('Inverter working')
                self.__inverter_status = InverterStatus.WORKING

from enum import Enum

class InverterStatus(Enum):
    NONE = 0
    STOPPED = 1
    WORKING = 2
    MALFUNCTION = 3

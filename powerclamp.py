import os
import threading
import time
import tinytuya
import line
from abc import ABC, abstractmethod
from enum import Enum
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PowerClampError(Exception):
    pass

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
        self.report_interval = int(os.getenv("REPORT_INTERVAL"))
        self.running = threading.Event()
        self.running.set()
        self.data = PowerData()

        self.__device = tinytuya.OutletDevice(
            dev_id=self.meter_id,
            address=self.ip,
            local_key=self.key,
            version=3.4
        )

        self.switch_enabled = switch_enabled
        self.__switch = None
        if self.switch_enabled:
            self.__switch = tinytuya.OutletDevice(
                dev_id=os.getenv("SWITCH_DEVICE_ID"),
                address=os.getenv("SWITCH_IP"),
                local_key=os.getenv("SWITCH_LOCAL_KEY"),
                version=3.3
            )

    def report(self, data):
        while self.running.is_set():
            try:
                d = data.get_value()
                if d is not None and 'dps' in d:
                    self.publish_data(d['dps'])
                time.sleep(self.report_interval)
            except Exception as e:
                logger.error(f"Error in report method: {e}")
                self.stop()
                raise PowerClampError("Error occurred, restarting")

    def update(self, data):
        error_count = 0
        while self.running.is_set():
            try:
                d = self.__device.status()
                self.__device.heartbeat()

                if d and 'dps' in d:
                    logger.info(f"Updating: {d}")
                    data.update(d)
                    error_count = 0
                else:
                    if self.switch_enabled:
                        error_count += 1
                        if error_count > self.error_threshold:
                            self.power_cycle()
                            error_count = 0

            except Exception as e:
                logger.error(f"Error in update method: {e}")
                self.stop()
                raise PowerClampError("Error occurred, restarting")
            finally:
                time.sleep(self.delay_seconds)

    def power_cycle(self):
        try:
            logger.info('Initiating power cycle')
            self.__switch.turn_off()
            time.sleep(self.switch_delay)
            self.__switch.turn_on()
            time.sleep(self.switch_delay)
            logger.info('Power cycle completed')
        except Exception as e:
            logger.error(f"Error during power cycle: {e}")
            self.stop()
            raise PowerClampError("Error occurred, restarting")

    def status(self):
        try:
            thread1 = threading.Thread(target=self.update, args=(self.data,), name="UpdateThread")
            thread2 = threading.Thread(target=self.report, args=(self.data,), name="ReportThread")

            thread1.start()
            thread2.start()

            while thread1.is_alive() and thread2.is_alive():
                thread1.join(1)
                thread2.join(1)

        except KeyboardInterrupt:
            logger.info("Stopping threads...")
            self.stop()
        except PowerClampError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in status method: {e}")
            self.stop()
            raise PowerClampError("Error occurred, restarting")

    def stop(self):
        self.running.clear()

    @abstractmethod
    def publish_data(self, status):
        pass

class MainPowerClamp(PowerClamp):
    def publish_data(self, status):
        if '101' not in status or '102' not in status:
            return

        if status['102'] == 'FORWARD':
            self.influxdb.write({'name': 'PowerClamp', 'type': 'ActivePowerA', 'value': status['101']})
            self.influxdb.write({'name': 'PowerClamp', 'type': 'ActivePowerC', 'value': 0})
        elif status['102'] == 'REVERSE':
            self.influxdb.write({'name': 'PowerClamp', 'type': 'ActivePowerA', 'value': 0})
            self.influxdb.write({'name': 'PowerClamp', 'type': 'ActivePowerC', 'value': status['101']})

class SolarPowerClamp(PowerClamp):
    def __init__(self, name, influxdb, switch_enabled):
        super().__init__(name, influxdb, switch_enabled)

    def publish_data(self, status):
        if '101' not in status or '102' not in status:
            return

        if status['102'] == 'FORWARD':
            self.influxdb.write({'name': 'PowerClamp', 'type': 'ActivePowerB', 'value': 0})
            self.data.send_line_message()

        elif status['102'] == 'REVERSE':
            self.influxdb.write({'name': 'PowerClamp', 'type': 'ActivePowerB', 'value': status['101']})
            self.data.send_line_message()

class PowerData:
    def __init__(self):
        self.__data = None
        self.lock = threading.Lock()
        self.__inverter_status = InverterStatus.NONE

    def update(self, data):
        with self.lock:
            self.__data = data

    def get_value(self):
        with self.lock:
            return self.__data

    def send_line_message(self):
        status = self.get_inverter_status()
        if self.__inverter_status == status:
            return

        if status == InverterStatus.MALFUNCTION:
            line.send_line_message("Power outage")
        elif status == InverterStatus.STOPPED:
            line.send_line_message("Inverter has stopped")
        elif status == InverterStatus.WORKING:
            line.send_line_message("Inverter is working")

        self.__inverter_status = status

    def get_inverter_status(self):
        data = self.__data
        status = InverterStatus.NONE

        if data['dps']['101'] == 0:
            status = InverterStatus.MALFUNCTION
        elif data['dps']['102'] == 'FORWARD':
            status = InverterStatus.STOPPED
        elif data['dps']['102'] == 'REVERSE':
            status = InverterStatus.WORKING

        return status


class InverterStatus(Enum):
    NONE = 0
    STOPPED = 1
    WORKING = 2
    MALFUNCTION = 3

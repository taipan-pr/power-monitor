from datetime import datetime, timezone
from influxdb_client import Point
from influxdb_client.client import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS


class InfluxClient:
    def __init__(self, url, token, org, bucket):
        self.client = influxdb_client.InfluxDBClient(url=url, token=token, org=org, bucket=bucket)
        self.bucket = bucket
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.org = org

    def write(self, data):
        p = (Point(data['name'])
             .field(data['type'], data['value'])
             .time(datetime.now(timezone.utc)))

        self.write_api.write(bucket=self.bucket, org=self.org, record=p)

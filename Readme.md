# Power Monitor

## Setup .env file
- METER_NAME= `MAIN` or `SOLAR`
- METER_DEVICE_ID= Device ID from Tuya, for example: `eb7754...61x07h`
- METER_LOCAL_KEY= Local key from Tuya, see [here](https://github.com/jasonacox/tinytuya). For example, `.CFc...iIBJ`
- METER_DEVICE_IP= Local IP address: `10.87.200.3`
- INFLUXDB_URL= InfluxDB URL with port: http://electricity-influxdb:8086
- INFLUXDB_TOKEN= InfluxDB Token: `KO39KY9gRY__83V...i4PUrhPno5Kp4Fw==`
- INFLUXDB_ORG= InfluxDB Organization: `TP`
- INFLUXDB_BUCKET= InfluxDB Bucket
- DELAY_SECS= Delay for each of the polling to the device
- SWITCH_DEVICE_ID= Device ID from Tuya, for example: `eb7754...61x07h` 
- SWITCH_LOCAL_KEY= Local key from Tuya, see [here](https://github.com/jasonacox/tinytuya). For example, `.CFc...iIBJ`
- SWITCH_IP= Local IP address: `10.87.200.3`
- SWITCH_DELAY= The interval of how switch is turn off
- ERROR_THRESHOLD= The threshold of h~~~~ow many times it fails to retrieve data until power cycle

## Build command
docker buildx build --platform linux/amd64 --tag dewnoibkk/tuya-monitor:latest --push .

## Docker Compose
docker-compose pull && docker-compose down && docker-compose up -d && docker container prune -f && docker image prune -f && docker container prune -f

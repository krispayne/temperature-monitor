#!/usr/bin/env python

# Raspberry Pi temperature logging script.
# @author Jeff Geerling, 2015.

import os
import glob
import time
import configparser
import influxdb_client
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS


config = configparser.ConfigParser()
config_dir = os.path.dirname(os.path.abspath(__file__))
config.read(config_dir + '/temps.conf')

token = config['influxdb']['influxdb_token']
org = config['influxdb']['influxdb_org']
url = config['influxdb']['influxdb_url']
bucket = config['influxdb']['influxdb_bucket']
client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)

write_api = client.write_api(write_options=SYNCHRONOUS)

# Read the temperature from a connected DS18B20 temperature sensor.
def readTempFromGPIO():
    base_dir = '/sys/bus/w1/devices/'
    device_folder = glob.glob(base_dir + '28*')[0]
    device_file_path = device_folder + '/w1_slave'
    device_file = open(device_file_path, "r")
    text = device_file.read()
    device_file.close()

    # Grab the second line, parse it, and find the temperature value.
    temp_line = text.split("\n")[1]
    temp_data = temp_line.split(" ")[9]
    temp_c = float(temp_data[2:]) / 1000
    temp_f = temp_c * 9.0 / 5.0 + 32.0
    # Adjust the temperature according to the configured offset.
    temp_f_adjusted = temp_f + float(config['dashboard']['local_temp_offset'])
    temp = "{0:.2f}".format(temp_f_adjusted)
    return temp

while True:
    # Get current temperature and timestamp.
    temp = readTempFromGPIO()
    point = (
        Point("Temperature Sensor")
        .tag("stationid", config['sensor']['station_id'])
        .tag("stationname", config['sensor']['station_name'])
				.tag("sensor", config['sensor']['sensor'])
        .field("temperature", temp)
    )
    # Send data to temperature logger.
    write_api.write(bucket=bucket, org=org, record=point)

    # Wait [local_temp_read_delay] seconds.
    time.sleep(int(config['dashboard']['local_temp_read_delay']))

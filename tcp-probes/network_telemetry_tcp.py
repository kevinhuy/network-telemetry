#!/usr/bin/env python3
''' Code for tcp probe. The command is executed every
    5 seconds and the RTT is extraxcted via regex.
    The value is stored in one or more InfluxDb instance'''

import re
import time
import threading
import yaml
from urllib3.exceptions import NewConnectionError
from urllib3.exceptions import MaxRetryError
from requests.exceptions import ConnectionError as ApiCallError
from classes.tcp_alpine import Tcp
from classes.influx_body import JsonBuilder
from credPass import credPass
from influxdb import InfluxDBClient

def thread_tcp():
    ''' multithreading tcp probes '''
    tcp_threads = []
    for region, values in dic_targets.items():
        for target, port in values.items():
            thread_targets = threading.Thread(target=influxdb_call, args=(target, port, region))
            thread_targets.start()
            tcp_threads.append(thread_targets)

def influxdb_call(target, port, region):
    ''' tcp probe execution and regex rtt '''
    json_body = JsonBuilder(Tcp(port, target).run_tcp(), target, region).json_body()
    for client in db_list:
        try:
            connect = InfluxDBClient(
                host=client,
                port=8086,
                username=influx.load(client, 'username'),
                password=influx.load(client, 'password'),
                database='network_telemetry')
            for json in json_body:
                connect.write_points(json)
        except (NewConnectionError, MaxRetryError, ApiCallError) as error:
            print(error)

if __name__ == '__main__':
    dic_targets = yaml.load(open('/var/targets.yaml', 'rb'))
    re_time = re.compile(r'(\d+\.\d+)')
    influx = credPass()
    # Add DB hostname/IP to db_list in case you want send result to more than one DB.
    # Remember to update .credential.json with DBs login.
    db_list = [
        'db'
        ]
    while True:
        thread_tcp()
        time.sleep(5)

#!/bin/python

from prometheus_client import Gauge
from prometheus_client import start_http_server

import threading 
import json
import requests
import time
import sys
import os

from alaudacli import service
from alaudacli import commands

def alauda_login(username, password, cloud='cn', endpoint='https://api.alauda.cn/v1/'):

    commands.login(username, password, cloud, endpoint)

def alauda_service_list(namespace):

    service_list = service.Service.list(namespace, 1)

    return service_list

def alauda_instance_list(namespace, name):

    service_inst = service.Service.fetch(name, namespace)
    instances = service_inst.list_instances()

    instance_list = []
    for data in instances:
        instance = json.loads(data.details)
        instance_list.append(instance)

    return instance_list

def alauda_get_instance_metrics(namespace, name, instance_uuid, start_time, end_time, interval):

    service_inst = service.Service.fetch(name, namespace)
    url = service_inst.api_endpoint + 'services/{0}/{1}/instances/{2}/metrics?start_time={3}&end_time={4}&point_per_period={5}'.format(service_inst.namespace, service_inst.name, instance_uuid, start_time, end_time, interval)
    r = requests.get(url, headers=service_inst.headers)

    data = json.loads(r.text)
    return data

def gather_data(namespace, run_event):

    g_cpu_usage = Gauge("cpu_cumulative_usage", "CPU Cumulative Usage", ["service", "instance"])
    g_cpu_utilization = Gauge('cpu_utilization', "CPU utilization", ["service", "instance"])
    g_memory_usage = Gauge('memory_usage', "Memory Usage", ["servie", "instance"])
    g_memory_utilization = Gauge('memory_utilization', "Memory Utilization", ["service", "instance"])

    while run_event.is_set():
        time.sleep(20)
	
	service_list = alauda_service_list(namespace)
        for service_inst in service_list:
            service_name = service_inst.name
            instance_list = alauda_instance_list(namespace, service_name)
            for instance in instance_list:
                end_time = int(time.time())
                start_time = str(end_time - 60) #gather data every 1 minute
		end_time = str(end_time)
                data = alauda_get_instance_metrics(namespace, service_name, instance['uuid'], start_time, end_time, "1m")
		g_cpu_usage.labels(service_name, instance['instance_name']).set(data['points'][0][1])
                g_cpu_utilization.labels(service_name, instance['instance_name']).set(data['points'][0][2])
                g_memory_usage.labels(service_name, instance['instance_name']).set(data['points'][0][3])
                g_memory_utilization.labels(service_name, instance['instance_name']).set(data['points'][0][4])

if __name__ == "__main__":

    username = os.environ.get('ALAUDA_USERNAME')
    password = os.environ.get('ALAUDA_PASSWORD')
    alauda_login(username, password)

    run_event = threading.Event()
    run_event.set()

    thread = threading.Thread(target=gather_data, args=('darkheaven', run_event))
    thread.start()

    try:
        start_http_server(9104)
        while True:
            time.sleep(10)

    except KeyboardInterrupt:
        run_event.clear()
        thread.join()
        sys.exit(0)


import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import concurrent.futures
import configparser
import json
import random
import sqlite3
import time
import docker
import socket
import requests
import traceback
import queue
import threading
from flask import Flask, request
from joblib import Parallel, delayed
import connector_db as dbConnector
import logging
from sqlite3 import Connection
from src import query_client

monitoring_demon = Flask(__name__)
parser = configparser.ConfigParser()
parser.read('../config.ini')
try:
    docker_client = docker.client.from_env()
except Exception as e:
    print("Error docker: {}".format(e))
    print("trace: {}".format(traceback.format_exc()))
    exit(1)
experiment = None

class Run:
    def __init__(self, node_count, gossip_rate, target_count, run, node_list=None, db_collection=None):
        self.db_id = -1
        self.data_entries_per_ip = {}
        self.node_list = node_list or []
        self.node_count = node_count
        self.convergence_round = -1
        self.convergence_message_count = -1
        self.message_count = 0
        self.start_time = None
        self.convergence_time = None
        self.is_converged = False
        self.gossip_rate = gossip_rate
        self.target_count = target_count
        self.run = run
        self.db_collection = db_collection
        self.max_round_is_reached = False
        self.ip_per_ic = {}
        self.stopped_nodes = {}

    def set_db_id(self, param):
        self.db_id = param

class Experiment:
    def __init__(self, node_count_range, gossip_rate_range, target_count_range, run_count, monitoring_address_ip,
                 is_send_data_back, push_mode):
        self.db_id = -1
        self.node_count_range = node_count_range
        self.gossip_rate_range = gossip_rate_range
        self.target_count_range = target_count_range
        self.run_count = run_count
        self.runs = []
        self.monitoring_address_ip = monitoring_address_ip
        self.db = dbConnector.DemonDB()
        self.query_queue = queue.Queue()
        self.query_thread = None
        self.is_send_data_back = is_send_data_back
        self.push_mode = push_mode
        self.NodeDB = dbConnector.NodeDB()

    def set_db_id(self, param):
        self.db_id = param

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def spawn_node(index, node_list, client, custom_network_name):
    try:
        new_node = docker_client.containers.run("demonv1", auto_remove=True, detach=True,
                                                network_mode=custom_network_name,
                                                ports={'5000': node_list[index]["port"]})
    except Exception as e:
        print("Node not spawned: {}".format(e))
        print("trace: {}".format(traceback.format_exc()))
        node_list[index]["port"] = get_free_port()
        spawn_node(index, node_list, client, custom_network_name)
    else:
        node_details = client.containers.get(new_node.id)
        node_list[index] = {"id": node_details.id,
                            "ip": node_details.attrs['NetworkSettings']['Networks']['test']['IPAddress'],
                            "port": node_details.attrs['NetworkSettings']['Ports']['5000/tcp'][0]['HostPort']}

def spawn_multiple_nodes(run):
    network_name = "test"
    from_index = 0
    if run.node_list is None:
        run.node_list = [None] * run.node_count
    elif len(run.node_list) == run.node_count:
        return  # Nodes are already spawned
    else:
        from_index = len(run.node_list)
        run.node_list = run.node_list + [None] * (run.node_count - len(run.node_list))
    client = docker.DockerClient()
    for i in range(from_index, run.node_count):
        run.node_list[i] = {}
        run.node_list[i]["port"] = get_free_port()
    Parallel(n_jobs=-1, prefer="threads")(
        delayed(spawn_node)(i, run.node_list, client, network_name) for i in range(from_index, run.node_count))

def nodes_are_ready(run):
    for i in range(0, run.node_count):
        if docker_client.containers.get(run.node_list[i]['id']).status != "running":
            return False
        run.node_list[i]["is_alive"] = True
    return True

def start_node(index, run, database_address, monitoring_address, ip):
    to_send = {"node_list": run.node_list, "target_count": run.target_count, "gossip_rate": run.gossip_rate,
               "database_address": database_address, "monitoring_address": monitoring_address,
               "node_ip": run.node_list[index]["ip"], "is_send_data_back": experiment.is_send_data_back,
               "push_mode": experiment.push_mode, "client_port": "4000"}
    try:
        time.sleep(0.01)
        requests.post("http://{}:{}/start_node".format(ip, run.node_list[index]["port"]), json=to_send)
    except Exception as e:
        print("Node not started: {}".format(e))
        start_node(index, run, database_address, monitoring_address, ip)

def start_run(run, monitoring_address):
    database_address = parser.get('database', 'db_file')
    ip = parser.get('system_setting', 'docker_ip')
    with concurrent.futures.ThreadPoolExecutor(max_workers=run.node_count) as executor:
        for i in range(0, run.node_count):
            executor.submit(start_node, i, run, database_address, monitoring_address, ip)
    run.start_time = time.time()

def prepare_run(run):
    spawn_multiple_nodes(run)
    while not nodes_are_ready(run):
        time.sleep(1)
    save_run_to_database(run)
    print("Run {} started".format(run.db_id), flush=True)
    time.sleep(10)

def generate_run(node_count, gossip_rate, target_count, run_count):
    if experiment.runs:
        return Run(node_count, gossip_rate, target_count, run_count, node_list=experiment.runs[-1].node_list)
    return Run(node_count, gossip_rate, target_count, run_count)

def save_run_to_database(run):
    run.db_id = experiment.db.insert_into_run(experiment.db_id, run.run, run.node_count, run.gossip_rate,
                                              run.target_count)

@monitoring_demon.route('/start', methods=['GET'])
def start_demon():
    server_ip = socket.gethostbyname(socket.gethostname())
    print("Server IP: {}".format(server_ip))
    return "OK - Run management ready"

if __name__ == "__main__":
    monitoring_demon.run(host='0.0.0.0', port=4000, debug=False, threaded=True)
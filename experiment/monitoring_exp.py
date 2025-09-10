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

def execute_queries_from_queue():
    while True:
        try:
            conn = sqlite3.connect('demonDB.db', check_same_thread=False)
            cursor = conn.cursor()
            query_data = experiment.query_queue.get()
            if query_data is None:
                break  # Signal to exit the thread
            query, parameters = query_data
            cursor.execute(query, parameters)
            conn.commit()
            experiment.query_queue.task_done()
        except Exception as e:
            print("Error db: {}".format(e))
            print("trace: {}".format(traceback.format_exc()))
            continue

def save_run_to_database(run):
    run.db_id = experiment.db.insert_into_run(experiment.db_id, run.run, run.node_count, run.gossip_rate,
                                              run.target_count)
    # NEW: capture metric profile
    profile_label = parser.get('MetricProfile', 'profile_label', fallback='unspecified')
    cpu_p = int(parser.get('MetricPriorities', 'cpu_priority', fallback=1))
    mem_p = int(parser.get('MetricPriorities', 'memory_priority', fallback=5))
    net_p = int(parser.get('MetricPriorities', 'network_priority', fallback=5))
    stor_p = int(parser.get('MetricPriorities', 'storage_priority', fallback=10))
    cpu_d = float(parser.get('MetricDeltas', 'cpu_delta', fallback=5.0))
    mem_d = float(parser.get('MetricDeltas', 'memory_delta', fallback=7.0))
    net_d = float(parser.get('MetricDeltas', 'network_delta', fallback=15.0))
    stor_d = float(parser.get('MetricDeltas', 'storage_delta', fallback=10.0))
    experiment.db.insert_run_metric_config(run.db_id, profile_label,
                                           cpu_p, mem_p, net_p, stor_p,
                                           cpu_d, mem_d, net_d, stor_d)

def create_and_start_demon_node(node_number, node_list, target_count, gossip_rate):
    # Add metric priority configuration
    node_data = {
        "metric_priorities": {
            "cpu": int(parser.get('MetricPriorities', 'cpu_priority', fallback=1)),
            "memory": int(parser.get('MetricPriorities', 'memory_priority', fallback=5)),
            "network": int(parser.get('MetricPriorities', 'network_priority', fallback=5)),
            "storage": int(parser.get('MetricPriorities', 'storage_priority', fallback=10))
        },
        "metric_deltas": {
            "cpu": float(parser.get('MetricDeltas', 'cpu_delta', fallback=5.0)),
            "memory": float(parser.get('MetricDeltas', 'memory_delta', fallback=7.0)),
            "network": float(parser.get('MetricDeltas', 'network_delta', fallback=15.0)),
            "storage": float(parser.get('MetricDeltas', 'storage_delta', fallback=10.0))
        }
    }

@monitoring_demon.route('/start', methods=['GET'])
def start_demon():
    server_ip = socket.gethostbyname(socket.gethostname())
    print("Server IP: {}".format(server_ip))
    return "OK - Metrics configuration ready"

if __name__ == "__main__":
    monitoring_demon.run(host='0.0.0.0', port=4000, debug=False, threaded=True)
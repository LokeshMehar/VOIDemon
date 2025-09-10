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

def get_target_count(node_count, target_count_range):
    new_range = []
    for i in target_count_range:
        if i <= node_count:
            new_range.append(i)
    return new_range

def generate_run(node_count, gossip_rate, target_count, run_count):
    if experiment.runs:
        return Run(node_count, gossip_rate, target_count, run_count, node_list=experiment.runs[-1].node_list)
    return Run(node_count, gossip_rate, target_count, run_count)

def prepare_experiment(server_ip):
    global experiment
    experiment = Experiment(json.loads(parser.get('DemonParam', 'node_range')),
                            json.loads(parser.get('DemonParam', 'gossip_rate_range')),
                            json.loads(parser.get('DemonParam', 'target_count_range')),
                            json.loads(parser.get('DemonParam', 'runs')),
                            server_ip,
                            parser.get('system_setting', 'is_send_data_back'),
                            parser.get('DemonParam', 'push_mode'))
    experiment.set_db_id(experiment.db.insert_into_experiment(time.time()))
    experiment.query_thread = threading.Thread(target=execute_queries_from_queue)
    experiment.query_thread.start()

def print_experiment():
    experiment.query_queue.put(None)
    experiment.query_thread.join()
    for run in experiment.runs:
        print("Run {}, converged after {} messages and {} seconds".format(run.node_count, run.convergence_message_count,
                                                                          run.convergence_time))

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

def save_converged_run_to_database(run):
    experiment.db.insert_into_converged_run(run.db_id, run.convergence_round, run.convergence_message_count,
                                            run.convergence_time)

def delete_all_nodes():
    to_remove = docker_client.containers.list(filters={"ancestor": "demonv1"})
    for node in to_remove:
        node.remove(force=True)
    return "OK"

@monitoring_demon.route('/start', methods=['GET'])
def start_demon():
    server_ip = socket.gethostbyname(socket.gethostname())
    print("Server IP: {}".format(server_ip))
    global experiment
    prepare_experiment(server_ip)
    for node_count in experiment.node_count_range:
        new_target_count_range = get_target_count(node_count, experiment.target_count_range)
        for target_count in new_target_count_range:
            for gossip_rate in experiment.gossip_rate_range:
                for run_count in range(0, experiment.run_count):
                    print("Preparing run with {} nodes, {} gossip rate, {} target count and {} run count".format(
                        node_count, gossip_rate, target_count, run_count))
                    run = generate_run(node_count, gossip_rate, target_count, run_count)
                    experiment.runs.append(run)
                    save_converged_run_to_database(run)
    print_experiment()
    delete_all_nodes()
    return "OK - Experiment finished - bussi k."

if __name__ == "__main__":
    monitoring_demon.run(host='0.0.0.0', port=4000, debug=False, threaded=True)
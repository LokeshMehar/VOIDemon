import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import concurrent.futures
import configparser
import json
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
    def __init__(self, node_count, gossip_rate, target_count, run, node_list=None):
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
        self.max_round_is_reached = False
        self.ip_per_ic = {}

    def set_db_id(self, param):
        self.db_id = param

class Experiment:
    def __init__(self, node_count_range, gossip_rate_range, target_count_range, run_count, monitoring_address_ip):
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

def run_converged(run):
    run.convergence_message_count = run.message_count
    run.convergence_time = (time.time() - run.start_time)
    if not run.is_converged:
        print("Convergence time: {}".format(run.convergence_time))
        print("Convergence message count: {}".format(run.convergence_message_count))
    run.is_converged = True

def check_convergence(run):
    if run.is_converged:
        return True
    if len(run.data_entries_per_ip) < run.node_count:
        return False
    for ip in run.data_entries_per_ip:
        if len(run.data_entries_per_ip[ip]) < run.node_count:
            return False
        if len(run.data_entries_per_ip[ip]) > run.node_count:
            return False
        for node_data in run.data_entries_per_ip[ip]:
            if "counter" not in run.data_entries_per_ip[ip][node_data]:
                return False
    run_converged(run)

def save_run_to_database(run):
    run.db_id = experiment.db.insert_into_run(experiment.db_id, run.run, run.node_count, run.gossip_rate,
                                              run.target_count)

def save_converged_run_to_database(run):
    experiment.db.insert_into_converged_run(run.db_id, run.convergence_round, run.convergence_message_count,
                                            run.convergence_time)

@monitoring_demon.route('/receive_ic', methods=['GET'])
def update_ic():
    client_ip = request.args['ip']
    client_port = request.args['port']
    experiment.runs[-1].ip_per_ic[client_ip + ":" + client_port] = True
    if len(experiment.runs[-1].ip_per_ic) == experiment.runs[-1].node_count:
        run_converged(experiment.runs[-1])
    return "OK"

@monitoring_demon.route('/receive_node_data', methods=['POST'])
def update_data_entries_per_ip():
    global experiment
    if not experiment:
        print("No experiment running, but a gossip node is trying to send data")
        return "NOK"
    
    client_ip = request.args['ip']
    client_port = request.args['port']
    round = request.args['round']
    inc = request.get_json()
    data_stored_in_node = inc["data"]
    data_flow_per_round = inc["data_flow_per_round"]

    nd = data_flow_per_round.setdefault('nd', 0)
    fd = data_flow_per_round.setdefault('fd', 0)
    rm = data_flow_per_round.setdefault('rm', 0)

    ic = len(data_stored_in_node)
    bytes_of_data = len(json.dumps(data_stored_in_node).encode('utf-8'))

    experiment.runs[-1].convergence_round = max(experiment.runs[-1].convergence_round, int(round))
    experiment.runs[-1].message_count += 1
    experiment.runs[-1].data_entries_per_ip[client_ip + ":" + client_port] = data_stored_in_node
    
    if not experiment.runs[-1].is_converged:
        if int(nd) > experiment.runs[-1].node_count:
            nd = experiment.runs[-1].node_count
        if int(fd) > experiment.runs[-1].node_count:
            fd = experiment.runs[-1].node_count
        
        delete_parameters = (experiment.runs[-1].db_id, client_ip, client_port, round)
        insert_parameters = (experiment.runs[-1].db_id, client_ip, client_port, round, nd, fd, rm, ic, bytes_of_data)
        
        experiment.query_queue.put(
            ("DELETE FROM round_of_node WHERE run_id = ? AND ip = ? AND port = ? AND round = ?", delete_parameters))
        experiment.query_queue.put((
            "INSERT INTO round_of_node (run_id, ip, port, round, nd, fd, rm, ic, bytes_of_data) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            insert_parameters))
    
    check_convergence(experiment.runs[-1])
    if int(round) >= 80:
        run_converged(experiment.runs[-1])
        experiment.runs[-1].max_round_is_reached = True
    return "OK"

@monitoring_demon.route('/start', methods=['GET'])
def start_demon():
    server_ip = socket.gethostbyname(socket.gethostname())
    print("Server IP: {}".format(server_ip))
    return "OK - Convergence logic ready"

if __name__ == "__main__":
    monitoring_demon.run(host='0.0.0.0', port=4000, debug=False, threaded=True)
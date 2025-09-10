import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import configparser
import json
import sqlite3
import time
import docker
import socket
import requests
import traceback
from flask import Flask, request
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
    def __init__(self, node_count, gossip_rate, target_count, run):
        self.db_id = -1
        self.node_count = node_count
        self.gossip_rate = gossip_rate
        self.target_count = target_count
        self.run = run
        self.node_list = []
        self.start_time = None
        self.is_converged = False

class Experiment:
    def __init__(self, node_count_range, gossip_rate_range, target_count_range, run_count):
        self.db_id = -1
        self.node_count_range = node_count_range
        self.gossip_rate_range = gossip_rate_range
        self.target_count_range = target_count_range
        self.run_count = run_count
        self.runs = []

@monitoring_demon.route('/start', methods=['GET'])
def start_demon():
    return "OK - Basic structure ready"

if __name__ == "__main__":
    monitoring_demon.run(host='0.0.0.0', port=4000, debug=False, threaded=True)
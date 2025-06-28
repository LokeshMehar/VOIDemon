
from flask import Flask
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
gossip = Flask(__name__)




if __name__ == "__main__":
    # get port from container
    gossip.run(host='0.0.0.0', debug=True, threaded=True)

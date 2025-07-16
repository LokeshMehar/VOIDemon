
from flask import Flask
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
gossip = Flask(__name__)



@gossip.route('/metadata', methods=['GET'])
def get_metadata():
    if not Node.instance().is_alive:
        # reset_node()
        return "Dead Node", 500
    node = Node.instance()
    latest_entry = max(node.data.keys(), key=int)
    metadata = {}
    for key in node.data[latest_entry]:
        if 'counter' in node.data[latest_entry][key]:
            metadata[key] = {'counter': node.data[latest_entry][key]['counter'],
                             'digest': node.data[latest_entry][key]['digest']}
    return json.dumps(metadata)

@gossip.route('/VOIDemon', methods=['GET'])
def get_hello_from_node():
    return "Hello from VOIDemon😈"

if __name__ == "__main__":
    # get port from container
    gossip.run(host='0.0.0.0', debug=True, threaded=True)

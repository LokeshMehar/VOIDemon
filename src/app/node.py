import time
import psutil
import requests
from singleton import Singleton
import logging
import secrets
from digest import mk_digest

logger = logging.getLogger("voidemon.node")

# Priority levels
PRIORITY_HIGH = 1     # Update every round
PRIORITY_MEDIUM = 5   # Update every 5 rounds
PRIORITY_LOW = 10     # Update every 10 rounds

# Configure priorities for different metrics

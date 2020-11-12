#!/usr/bin/python
# coding:utf8

__author__ = "Huseyin Cotel"
__copyright__ = "Copyright Vircon 2019"
__credits__ = ["onur", "huseyin"]
__license__ = "GPL"
__version__ = "1.0.1"
__maintainer__ = ""
__email__ = "info@vircongroup.com"
__status__ = "Development"

from config.envparams import Params
import redis
import time
from redis.sentinel import Sentinel

PARAM_FILE_PATH = "./params.json"
prms = Params(param_file_path=PARAM_FILE_PATH)

def connect2redis(host, port=6379, db=0, connectionPool=True, logging=None, sentinel_service=prms.REDIS_SENTINEL_SERVICE_NAME, master=True):
    if sentinel_service:
        retry_count = 0
        while retry_count < 10:
            sentinel = Sentinel([(host, 26379)])
            if master:
                client = sentinel.master_for(sentinel_service)
            else:
                client = sentinel.slave_for(sentinel_service)
            if is_available(client, logging=logging):
                logging.info("Connected to Redis succesfully.")
                return client
            else:
                print(f"Waiting for {pow(2, retry_count)} secs.")
                time.sleep(pow(2, retry_count))
                retry_count += 1
    else:
        retry_count = 0
        while retry_count < 10:
            if connectionPool:
                pool = redis.ConnectionPool(host=host, port=port, db=db)
                client = redis.StrictRedis(connection_pool=pool)
            else:
                client = redis.StrictRedis(host=host, port=port, db=db)
            if is_available(client, logging=logging):
                logging.info("Connected to Redis succesfully.")
                return client
            else:
                print(f"Waiting for {pow(2, retry_count)} secs.")
                time.sleep(pow(2, retry_count))
                retry_count += 1
    logging.error("Exiting...")
    exit(3)

def is_available(client, logging=None):
        try:
            client.client_list()  # getting None returns None or throws an exception
        except (redis.exceptions.ConnectionError,
                redis.exceptions.BusyLoadingError) as err:
            logging.error(f"Redis connection cannot be established due to '{err}'.")
            return False
        return True

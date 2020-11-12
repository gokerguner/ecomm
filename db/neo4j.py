__author__ = "Huseyin Cotel"
__copyright__ = "Copyright 2019"
__credits__ = [""]
__license__ = "GPL"
__version__ = "1.2.0"
__email__ = "info@vircongroup.com"
__status__ = "Development"

from py2neo import Graph
from py2neo import Node, Relationship
from config.envparams import Params
import time

PARAM_FILE_PATH = "params.json"
prms = Params(param_file_path=PARAM_FILE_PATH)

def get_secret(secret_name):
    try:
        with open('/run/secrets/{0}'.format(secret_name), 'r') as secret_file:
            return secret_file.read().strip()
    except IOError:
        return None

def connect2neo4j(hostname, logging):

    retry_count = 0
    neopass = get_secret("NEO4J_PASSWD")
    while retry_count < 10:
        graph = Graph(f"bolt://{hostname}:7687", user="neo4j", password=neopass)
        try:
            graph.run("Match () Return 1 Limit 1")
            logging.info("Connected to Neo4j succesfully.")
            return graph
        except Exception as e:
            logging.warning(e)
            print(f"Waiting for {pow(2, retry_count)} secs.")
            time.sleep(pow(2, retry_count))
            retry_count += 1

    logging.error("Exiting...")
    exit(3)

def createGraphIndexes(client, logging):

    try:
        client.schema.create_uniqueness_constraint("Person", "name")
    except Exception as e:
        logging.error(e)


#!/usr/bin/env python3

import argparse
import json
import logging
import colorsys
import signal
from time import sleep

import copy
import random
import requests


def hsv2rgb(h, s, v):
    if h >= 1:
        h = h / 360
    return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(h, s, v))


logging.basicConfig(format="%(asctime)s[%(levelname)8s][%(threadName)s][%(module)s] %(message)s",
                    datefmt="[%m/%d/%Y %H:%M:%S]")
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description="SwimSuite Result Simulator")

parser.add_argument("-a", "--api", dest="host", help="Host to send API requests to", default="127.0.0.1:8000")
parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run only. No post network requests.",
                    default=False)
parser.add_argument("-t", dest="time_factor", type=float, help="Sleep time between colour change",
                    default=1.0)
parser.add_argument("-b", dest="brightness", type=float, help="Brightness", default=1)
parser.add_argument("-s", dest="saturation", type=float, help="Saturation", default=1)
parser.add_argument("--step", dest="step", type=int, help="Hue step (in degrees)", default=2)
# Other
parser.add_argument("-v", "--verbose", dest="verbosity", action="count", help="Increase verbosity.")
args = parser.parse_args()

# Set root logging level
if args.verbosity is not None:
    logger = logging.getLogger()
    if args.verbosity == 1:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.DEBUG)

api_base = args.host
if api_base[0:4] != "http":
    api_base = "http://" + args.host
if api_base[:-1] != "/":
    api_base = api_base + "/"

if args.dry_run:
    logging.info("API Base: {}".format("DRY RUN"))
else:
    logging.info("API Base: {}".format(api_base))

nodes = requests.get("{}discover".format(api_base))
nodes = json.loads(nodes.text)

rgb_nodes = []

logging.info("Found {} nodes".format(len(nodes)))
for node_id, identifier in nodes.items():
    logging.info("{}: {}".format(node_id, identifier))
    node_io = requests.get("{}node/{}/io".format(api_base, node_id))
    node_io = json.loads(node_io.text)
    for type in node_io["types"]:
        if type["type"] == 4 and len(type["params"]) == 3:
            rgb_nodes.append(node_io)

def sig_handler(signal, etc):
    for type in node["types"]:
        if type["type"] == 4 and len(type["params"]) == 3:
            if not args.dry_run:
                r = requests.post("{}node/{}".format(api_base, node["id"]),
                                  headers={"Content-Type": "application/json"},
                                  data=json.dumps({
                                      "payload": type["type"],
                                      "data": [
                                          {
                                              "index": 0,
                                              "data": 0
                                          },
                                          {
                                              "index": 1,
                                              "data": 0
                                          },
                                          {
                                              "index": 2,
                                              "data": 0
                                          }
                                      ]
                                  }))
                if r.status_code != 200:
                    logging.error(r.text)
                    quit(1)
    quit(0)


signal.signal(signal.SIGINT, sig_handler)
signal.signal(signal.SIGTERM, sig_handler)

saturation = args.saturation
brightness = args.brightness
while True:
    for i in range(0, 359, args.step):
        color = hsv2rgb(i, saturation, brightness)
        logging.info("Colour (R: {}, G: {}, B: {})".format(color[0], color[1], color[2]))
        for node in rgb_nodes:
            for type in node["types"]:
                if type["type"] == 4 and len(type["params"]) == 3:
                    if not args.dry_run:
                        r = requests.post("{}node/{}".format(api_base, node["id"]),
                                          headers={"Content-Type": "application/json"},
                                          data=json.dumps({
                                              "payload": type["type"],
                                              "data": [
                                                  {
                                                      "index": 0,
                                                      "data": color[0]
                                                  },
                                                  {
                                                      "index": 1,
                                                      "data": color[1]
                                                  },
                                                  {
                                                      "index": 2,
                                                      "data": color[2]
                                                  }
                                              ]
                                          }))
                        if r.status_code != 200:
                            logging.error(r.text)
                            quit(1)
        if args.time_factor != 0:
            logging.debug("Sleeping for {}".format(args.time_factor))
            sleep(args.time_factor)
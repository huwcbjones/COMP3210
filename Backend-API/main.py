import argparse
import logging
from api import API

logging.basicConfig(format="%(asctime)s[%(levelname)8s][%(threadName)s][%(module)s] %(message)s",
                    datefmt="[%m/%d/%Y %H:%M:%S]")

parser = argparse.ArgumentParser(description="COMP3210 Backend API", prefix_chars="-+")

# Binary Protocol
group = parser.add_argument_group(title="Binary Protocol")
group.add_argument("--bin-addr", dest="bin_addr", help="Address to listen on (default: all)", default="",
                   metavar="ADDRESS")
group.add_argument("--bin-port", dest="bin_port", type=int, help="Port number to listen on", default=5190,
                   metavar="PORT")
bool_group = group.add_mutually_exclusive_group(required=True)
bool_group.add_argument("-b", dest="enable_binary", help="Disable Binary Protocol", action="store_false")
bool_group.add_argument("+b", dest="enable_binary", help="Enable Binary Protocol", action="store_true")

# REST API
group = parser.add_argument_group(title="REST API")
group.add_argument("--rest-addr", dest="rest_addr", help="Address to listen on (default: all)", default="",
                   metavar="ADDRESS")
group.add_argument("--rest-port", dest="rest_port", type=int, help="Port number to listen on", default=8080,
                   metavar="PORT")
bool_group = group.add_mutually_exclusive_group(required=True)
bool_group.add_argument("-r", dest="enable_rest", help="Disable REST API", action="store_false")
bool_group.add_argument("+r", dest="enable_rest", help="Enable REST API", action="store_true")

# Other
parser.add_argument("-v", "--verbose", dest="verbosity", action="count", help="Increase verbosity.")
parser.add_argument("-x", dest="xbee", help="X-Bee Serial Device", required=True)
args = parser.parse_args()

# Set root logging level
logger = logging.getLogger()
logger.setLevel(logging.WARNING)
if args.verbosity is not None:
    if args.verbosity == 1:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.DEBUG)

api = API(
    enable_binary=args.enable_binary, binary_address=args.bin_addr, binary_port=args.bin_port,
    enable_rest=args.enable_rest, rest_address=args.rest_addr, rest_port=args.rest_port,
    serial=args.xbee
)
api.run()

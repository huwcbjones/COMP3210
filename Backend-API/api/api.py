import json
import logging
import socket
import asyncio
import inspect
import os.path
import os
import pwd
import grp
from enum import Enum
from json import JSONDecodeError
from threading import Thread

import struct

import sdnotify
import tornado.web
from sensor_net import SensorNetwork, Node

from api import controllers


class API:
    app = None

    def __init__(self, enable_binary, binary_port, binary_address, enable_rest, rest_port, rest_address, serial, user, group):
        self.systemd = sdnotify.SystemdNotifier()

        try:
            self.user = pwd.getpwnam(user).pw_uid
        except KeyError:
            logging.fatal("User {} not found!".format(user))
            quit(1)

        try:
            self.group = grp.getgrnam(group).gr_gid
        except KeyError:
            logging.fatal("Group {} not found!".format(group))
            quit(1)

        if API.app is None:
            API.app = self
        else:
            raise RuntimeError()
        if __debug__:
            logging.warning("DEBUG MODE IS ENABLED!")
            logging.warning("Safeguards may be disabled.")
            logging.warning("To disable this warning, run python with the -O flag")

        self.enable_binary = enable_binary
        self.enable_rest = enable_rest

        if enable_binary:
            try:
                self._check_ports(binary_address, binary_port)
                self._init_binary(binary_address, binary_port)
            except OSError as e:
                logging.fatal("Error binding to {}:{}".format(binary_address, binary_port))
                logging.fatal(e.strerror)
                quit(1)
        if enable_rest:
            try:
                self._check_ports(rest_address, rest_port)
                self._init_rest(rest_address, rest_port)
            except OSError as e:
                logging.fatal("Error binding to {}:{}".format(rest_address, rest_port))
                logging.fatal(e.strerror)
                quit(1)

        self._init_rf_network(serial)

    def _init_rf_network(self, serial):
        logging.info("Initialising RF network...")
        if serial is None or not os.path.exists(serial):
            logging.fatal("Cannot open serial device {}".format(serial))
            quit(1)

        logging.info("Starting sensor network...")
        self.sensor_net = SensorNetwork(serial)
        self.sensor_net.discover(2)

        logging.info("Started RF Network!")

    def _init_binary(self, address, port):
        self._binary_api_thread = Thread(
            name="binary_api_thread",
            target=self._create_binary_thread,
            args=(address, port),
            daemon=True
        )

    def _init_rest(self, address, port):
        logging.info("Loading controllers...")

        routes = self._load_routes(controllers, set())

        logging.info("Loaded {} routes!".format(len(routes)))

        class DefaultController(controllers.Controller):

            def prepare(self):
                raise tornado.web.HTTPError(status_code=404)

        routes.append((r"[\w\W]*", DefaultController))
        app = tornado.web.Application(routes)
        app.listen(port=port, address=address)

    def _create_binary_thread(self, address, port):
        self.binary_api_loop = asyncio.new_event_loop()
        loop = self.binary_api_loop
        logging.debug("Creating Binary API")
        self._binary_api = loop.create_server(
            BinaryProtocol,
            address, port
        )
        logging.info("Starting Binary API...")
        loop.run_until_complete(self._binary_api)
        loop.run_forever()
        loop.close()

    def _load_routes(self, obj, checked):
        routes = []
        # Loop through members of obj
        for name, obj in inspect.getmembers(obj):
            if name in checked:
                continue
            checked.add(name)
            if name[0:2] == '__':
                continue

            if inspect.ismodule(obj):
                routes.extend(self._load_routes(obj, checked))
                continue

            if not inspect.isclass(obj):
                continue

            if not issubclass(obj, (controllers.Controller, controllers.WebSocketController)):
                continue

            logging.debug("Checking {}".format(name))
            if obj.route is not None:
                [routes.append((regex, obj)) for regex in obj.route]
                logging.debug("Loaded {} routes for {}!".format(len(obj.route), name))

        return routes

    def run(self):
        """
        Run the server
        """
        logging.info("Starting listen loop...")
        if self.enable_binary:
            self._binary_api_thread.start()

        loop = asyncio.get_event_loop()

        logging.info("Startup complete...")
        self._drop_privs()
        try:
            self.systemd.notify("READY=1")
            self.systemd.notify("STATUS=Running")
            loop.run_forever()
        except:
            # Find all running tasks:
            pending = asyncio.Task.all_tasks()

            # Run loop until tasks done:
            loop.run_until_complete(asyncio.gather(*pending))
        finally:
            self.sensor_net.stop()
            loop.stop()
            loop.close()

    def _drop_privs(self):
        if os.getuid() != 0:
            return
        logging.info("Dropping privileges...")

        os.setgroups([])
        os.setgid(self.group)
        os.setuid(self.user)

    @staticmethod
    def _check_ports(address, port):
        if not __debug__:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((address, port))
            s.close()


class BinaryProtocol(asyncio.Protocol):

    def __init__(self):
        self.transport = None
        self.remote = None
        self.remote_address = None
        self.remote_port = None
        pass

    def data_received(self, data):
        logging.debug("RECV {} <- {}".format(data, self.remote))
        try:
            destination, data = decode_payload(data)
            logging.debug("Destination: {}".format(destination))
            logging.debug("Payload: {}".format(data))
        except DecodeError as e:
            logging.error(e)
            return

        # Do stuff

        super().data_received(data)

    def eof_received(self):
        logging.info("Received disconnect from {}".format(self.remote))
        super().eof_received()

    def connection_made(self, transport):
        self.transport = transport
        if self.remote_address is None:
            sockname = transport.get_extra_info('socket').getpeername()
            self.remote_address = sockname[0]
            self.remote_port = sockname[1]
            self.remote = self.remote_address + ":" + str(self.remote_port)
        logging.info("Connected to {}".format(self.remote))

    def connection_lost(self, exc):
        logging.info("Lost connection to {}")
        super().connection_lost(exc)

    def write_data(self, data):
        logging.debug("SENT {} -> {}".format(data, self.remote))
        self.transport.write(data)


def get_payload(destination, data=None):
    payload = "".encode()
    if data is not None:
        payload = json.dumps(data).encode()
    return struct.pack("I{}s".format(len(payload)), destination, payload)


def decode_payload(data):
    (destination,), payload = struct.unpack("I", data[:4]), data[4:]

    # If we want to support JSON payloads *AND* we want to decode them in python, uncomment below
    # try:
    #     payload = payload.decode()
    #     payload = json.loads(payload)
    # except JSONDecodeError:
    #     raise DecodeError("Failed to decode payload {}".format(payload))

    return destination, payload


class DecodeError(Exception):
    def __init(self, message=""):
        super().__init__(message)

from . import Controller
from tornado.web import HTTPError


class DiscoverController(Controller):

    route = [r"/discover"]

    async def get(self):
        self.write([{"id": n.addr, "name": n.identifier} for _, n in self.app.sensor_net._slave_nodes.items()])


class RediscoverController(Controller):

    route = [r"/rediscover(/[0-9]*|)"]

    async def get(self, time):
        if time is None:
            time = 5
        elif isinstance(time, str):
            if time == '':
                time = 5
            else:
                try:
                    time = int(time)
                except ValueError:
                    raise HTTPError(status_code=400, reason='Invalid argument for time "{}"'.format(time))
        self.app.sensor_net.discover(time)
        self.write([{"id": n.addr, "name": n.identifier} for _, n in self.app.sensor_net._slave_nodes.items()])

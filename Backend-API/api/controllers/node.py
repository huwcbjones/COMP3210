from . import Controller
from sensor_net import Node, ProtocolError
from tornado.web import HTTPError


class NodeIOController(Controller):
    route = [r"/node/([0-9]+)/io"]

    async def get(self, node_id):
        try:
            node_id = int(node_id)
        except ValueError:
            raise HTTPError(status_code=404, reason="Node not found.")

        if node_id not in self.app.sensor_net._slave_nodes:
            raise HTTPError(status_code=404, reason="Node not found.")

        node = self.app.sensor_net._slave_nodes[node_id]
        node_info = {"id": node.addr, "identifier": node.identifier, "types": []}

        payloads = self.app.sensor_net.get_node_io(node)
        for payload in payloads.keys():
            type = {}
            node_info["types"].append(type)
            type["type"] = payload.value
            params = []
            type["params"] = params
            for i in range(0, payloads[payload]):
                payload_info = self.app.sensor_net.get_payload_info(node, payload, index=i)
                params.append({
                    "id": i,
                    "type": payload_info.decode()
                })
        self.write(node_info)


class NodeSendDataController(Controller):
    route = [r"/node/([0-9]+)"]

    async def post(self, node_id):
        try:
            node_id = int(node_id)
        except ValueError:
            raise HTTPError(status_code=404, reason="Node not found.")

        if node_id not in self.app.sensor_net._slave_nodes:
            raise HTTPError(status_code=404, reason="Node not found.")

        node = self.app.sensor_net._slave_nodes[node_id]

        if "payload" not in self.json_args:
            raise HTTPError(status_code=400, reason="payload not provided")
        if "data" not in self.json_args:
            raise HTTPError(status_code=400, reason="data not provided")

        if not isinstance(self.json_args["data"], list):
            raise HTTPError(status_code=400, reason="Invalid argument for data")

        try:
            payload = Node.Payload(int(self.json_args["payload"]))
        except ValueError:
            raise HTTPError(status_code=400, reason="Invalid payload type")

        data = []
        for d in self.json_args["data"]:
            if "index" not in d:
                raise HTTPError(status_code=400, reason="index not provided in data")
            if "data" not in d:
                raise HTTPError(status_code=400, reason="data not provided in data")

            data.append(d)

        for d in data:
            try:
                if payload == Node.Payload.BYTE_INPUT:
                    d["data"] = d["data"].encode()
                self.app.sensor_net.send_data(node, payload, d["data"], d["index"])
            except ValueError or TypeError as e:
                raise HTTPError(status_code=400, reason=e.args[0])
            except ProtocolError as e:
                raise HTTPError(400, reason=e.args[0])

        self.set_status(200)


class NodeGetDataController(Controller):
    route = [r"/node/([0-9]+)/([0-9]+|)(/[0-9]+|)"]

    async def get(self, node_id, payload, index):
        try:
            node_id = int(node_id)
        except ValueError:
            raise HTTPError(status_code=404, reason="Node not found.")

        if node_id not in self.app.sensor_net._slave_nodes:
            raise HTTPError(status_code=404, reason="Node not found.")

        node = self.app.sensor_net._slave_nodes[node_id]

        payload = Node.Payload(int(payload))
        if index != "":
            try:
                index = int(index[1:])
                data = {"value": self.app.sensor_net.get_data(node, payload, index)}
            except ValueError or TypeError as e:
                raise HTTPError(status_code=400, reason=e.args[0])
            except ProtocolError as e:
                raise HTTPError(400, reason=e.args[0])
        else:
            data = []
            for i in range(0, 16):
                try:
                    result = self.app.sensor_net.get_data(node, payload, i)
                    data.append({"index": i, "value": result})
                except ProtocolError:
                    break
        self.write(data)

# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Vultr
"""
import urllib

from libcloud.utils.py3 import httplib

from libcloud.common.base import ConnectionKey, JsonResponse
from libcloud.compute.base import NodeImage, NodeSize, Node
from libcloud.compute.base import NodeDriver, NodeLocation
from libcloud.compute.types import Provider, NodeState


class VultrResponse(JsonResponse):
    """
    Vultr response handler.  HTTP status codes are used to indicate errors,
    so this only needs to grab the actual message from the error page
    """
    def parse_error(self):
        return self.body


class VultrConnection(ConnectionKey):
    """
    Connection class for Vultr
    """

    host = 'api.vultr.com'
    responseCls = VultrResponse

    def add_default_params(self, params):
        params['api_key'] = self.key
        return params

    def post(self, **kwargs):
        kwargs['method'] = 'POST'
        kwargs['headers'] = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        return self.request(**kwargs)

    def encode_data(self, data):
        return urllib.urlencode(data)


class VultrNodeDriver(NodeDriver):
    """
    Vultr Node Driver
    """

    connectionCls = VultrConnection

    name = "Vultr"
    website = 'https://www.vultr.com'
    type = Provider.VULTR

    def list_nodes(self):
        data = self.connection.request('/v1/server/list').object
        return [self._to_node(data[cur]) for cur in data]

    def reboot_node(self, node):
        result = self.connection.post(
            action='/v1/server/reboot',
            data={'SUBID': node.id}
        )
        return result.status == httplib.OK

    def destroy_node(self, node):
        result = self.connection.post(
            action='/v1/server/destroy',
            data={'SUBID': node.id}
        )
        return result.status == httplib.OK

    def list_images(self, location=None):
        data = self.connection.request('/v1/os/list').object
        return [self._to_image(data[cur]) for cur in data]

    def list_sizes(self, location=None):
        data = self.connection.request('/v1/plans/list').object
        return [self._to_size(data[cur]) for cur in data]

    def list_locations(self):
        data = self.connection.request('/v1/regions/list').object
        return [self._to_location(data[cur]) for cur in data]

    def create_node(self, name, size, image, location, **kwargs):
        data = {
            'DCID': location.id,
            'OSID': image.id,
            'VPSPLANID': size.id,
            'label': name
        }

        result = self.connection.post(action='/v1/server/create', data=data)
        if result.status != httplib.OK:
            return False

        # The create API call only returns a SUBID.  To actually create
        # a node, we need to list all the nodes again
        nodes = self.list_nodes()
        for cur in nodes:
            if result.object['SUBID'] == cur.id:
                return cur

        return False

    def _to_node(self, data):
        if data['status'] == 'pending':
            state = NodeState.PENDING
        elif data['status'] == 'active' and data['power_status'] == 'running':
            state = NodeState.RUNNING
        elif data['status'] == 'active':
            state = NodeState.STOPPED
        else:
            state = NodeState.UNKNOWN

        extra = {
            'v6_network': data['v6_network'],
            'v6_network_size': data['v6_network_size'],
            'v6_main_ip': data['v6_main_ip'],
        }

        node = Node(
            id=data['SUBID'],
            name=data['label'],
            state=state,
            public_ips=[data['main_ip']],
            private_ips=None,
            extra=extra,
            driver=self
        )
        return node

    def _to_image(self, data):
        return NodeImage(
            id=data['OSID'],
            name=data['name'],
            driver=self
        )

    def _to_size(self, data):
        extra = {'windows': data['windows'], 'vcpu_count': data['vcpu_count']}
        return NodeSize(
            id=data['VPSPLANID'],
            name=data['name'],
            ram=int(data['ram']),
            disk=int(data['disk']),
            bandwidth=float(data['bandwidth']),
            price=float(data['price_per_month']),
            extra=extra,
            driver=self
        )

    def _to_location(self, data):
        return NodeLocation(
            id=data['DCID'],
            name=data['name'],
            country=data['country'],
            driver=self
        )


if __name__ == "__main__":
    import doctest

    doctest.testmod()

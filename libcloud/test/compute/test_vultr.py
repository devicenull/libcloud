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
import sys
import unittest

from libcloud.utils.py3 import httplib

from libcloud.compute.drivers.vultr import VultrNodeDriver
from libcloud.test import LibcloudTestCase, MockHttpTestCase
from libcloud.test.file_fixtures import ComputeFileFixtures
from libcloud.test.secrets import VULTR_PARAMS

class VultrTests(LibcloudTestCase):
    def setUp(self):
        VultrNodeDriver.connectionCls.conn_classes = (VultrMockHttp, VultrMockHttp)
        VultrMockHttp.type = None
        self.driver = VultrNodeDriver(*VULTR_PARAMS)

    def test_list_images_success(self):
        images = self.driver.list_images()
        self.assertTrue(len(images) == 2)

        image = images[0]
        self.assertTrue(image.id is not None)
        self.assertEqual(image.name, 'Ubuntu 12.04 i386')

        image = images[1]
        self.assertTrue(image.id is not None)
        self.assertEqual(image.name, 'CentOS 6 x64')

    def test_list_sizes_success(self):
        sizes = self.driver.list_sizes()
        self.assertTrue(len(sizes) == 2)

        size = sizes[0]
        self.assertTrue(size.id is not None)
        self.assertEqual(size.name, 'Starter')
        self.assertEqual(size.ram, 512)
        self.assertEqual(size.disk, 20)
        self.assertEqual(size.price, 5.00)

        size = sizes[1]
        self.assertTrue(size.id is not None)
        self.assertEqual(size.name, 'Basic')
        self.assertEqual(size.ram, 1024)
        self.assertEqual(size.disk, 30)
        self.assertEqual(size.price, 8.00)

    def test_list_locations_success(self):
        locations = self.driver.list_locations()
        self.assertTrue(len(locations) == 2)

        location = locations[0]
        self.assertTrue(location.id is not None)
        self.assertEqual(location.name, 'New Jersey')
        self.assertEqual(location.country, 'US')

        location = locations[1]
        self.assertTrue(location.id is not None)
        self.assertEqual(location.name, 'Chicago')
        self.assertEqual(location.country, 'US')

    def test_list_nodes_success(self):
        nodes = self.driver.list_nodes()
        self.assertTrue(len(nodes) == 1)

        node = nodes[0]
        self.assertTrue(node.id is not None)
        self.assertEqual(node.name, 'my new server')
        self.assertEqual(node.public_ips[0], '123.123.123.123')

    def test_reboot_node_success(self):
        node = self.driver.list_nodes()[0]
        result = self.driver.reboot_node(node)
        self.assertTrue(result)

    def test_destroy_node_success(self):
        node = self.driver.list_nodes()[0]
        result = self.driver.destroy_node(node)
        self.assertTrue(result)

    def test_server_error(self):
        VultrMockHttp.type = 'INTERNAL_SERVER_ERROR'
        self.assertRaises(Exception, self.driver.list_images)

class VultrMockHttp(MockHttpTestCase):
    fixtures = ComputeFileFixtures('vultr')

    def _v1_os_list(self, method, url, body, headers):
        body = self.fixtures.load('list_os.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _v1_os_list_INTERNAL_SERVER_ERROR(self, method, url, body, headers):
        return (httplib.INTERNAL_SERVER_ERROR, 'Internal server error has occured', {}, httplib.responses[httplib.INTERNAL_SERVER_ERROR])

    def _v1_plans_list(self, method, url, body, headers):
        body = self.fixtures.load('list_plans.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _v1_regions_list(self, method, url, body, headers):
        body = self.fixtures.load('list_regions.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _v1_server_list(self, method, url, body, headers):
        body = self.fixtures.load('list_servers.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _v1_server_reboot(self, method, url, body, headers):
        return (httplib.OK, {}, {}, httplib.responses[httplib.OK])

    def _v1_server_destroy(self, method, url, body, headers):
        return (httplib.OK, {}, {}, httplib.responses[httplib.OK])

if __name__ == '__main__':
    sys.exit(unittest.main())

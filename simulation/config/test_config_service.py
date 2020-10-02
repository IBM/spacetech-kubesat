# Copyright 2020 IBM Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import unittest
from unittest import TestCase, IsolatedAsyncioTestCase
from kubesat.message import Message
from kubesat.nats_handler import NatsHandler
from kubesat.validation import MessageSchemas, check_pointing_and_mode, check_internal, check_internal_data, check_pointing
from kubesat.testing import FakeNatsHandler, FakeLogger
from config_service import initialize_service, check_status
import time

class Tests(IsolatedAsyncioTestCase):

    async def test_initialize_service(self):
        """
        Test initialization of services based on config files
        """
        loop = asyncio.get_running_loop()
        shared_storage = {
                            "simulation": {
                              "clock": False,
                              "logging": False,
                              "czml": False,
                              "config": False
                            },
                            "cubesats": {
                              "cubesat_1": {
                                "orbits": False,
                                "rl": False,
                                "rl_training": False,
                                "data": False,
                                "agriculture": False
                              }
                            },
                            "groundstations": {
                              "groundstation_1": {
                                "groundstation": False
                              }
                            },
                            "iots": {
                              "iot_1": {
                                "iot": False
                              }
                            },
                            "config_path":"./simulation_config"
                          }
        nats = FakeNatsHandler("data1", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()
        logger = FakeLogger()

        message = nats.create_message("data", MessageSchemas.SERVICE_TYPE_MESSAGE)
        await initialize_service(message, nats, shared_storage, logger)
        self.assertTrue(shared_storage["cubesats"]["cubesat_1"]["data"])

    async def test_check_status(self):
        loop = asyncio.get_running_loop()
        shared_storage = {
                            "simulation": {
                              "clock": True,
                              "logging": False,
                              "czml": False,
                              "config": False
                            },
                            "cubesats": {
                              "cubesat_1": {
                                "orbits": False,
                                "rl": False,
                                "rl_training": False,
                                "data": False,
                                "agriculture": False
                              }
                            },
                            "groundstations": {
                              "groundstation_1": {
                                "groundstation": False
                              }
                            },
                            "iots": {
                              "iot_1": {
                                "iot": False
                              }
                            },
                            "config_path":"./simulation_config"
                          }
        nats = NatsHandler("data1", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()
        logger = FakeLogger()
        await check_status(nats, shared_storage, logger)
        self.assertTrue(shared_storage["simulation"]["clock"]==False)

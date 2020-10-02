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
from kubesat.testing import FakeNatsHandler, FakeLogger
from clock_service import send_timestep
import time

class Tests(IsolatedAsyncioTestCase):

    async def test_send_timestep(self):
        """
        Test timesteps
        """
        loop = asyncio.get_running_loop()
        shared_storage = {
        "start_time": "2020-07-15T00:00:00.000000",
        "time_step": 50.0
        }
        nats = FakeNatsHandler("clock", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()
        logger = FakeLogger()
        
        await send_timestep(nats, shared_storage, logger)

        self.assertEqual(len(nats._dict["simulation.timestep"]), 1)
        self.assertEqual(nats._dict["simulation.timestep"][0].data["time"], "2020-07-15T00:00:00.000000")
        self.assertEqual(shared_storage["start_time"], "2020-07-15T00:00:50.000000")
        

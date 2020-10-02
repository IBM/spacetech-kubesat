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


from kubesat.testing import FakeNatsHandler
from kubesat.message import Message
from agriculture_service import process_data
from kubesat.validation import check_internal_data, MessageSchemas


class Tests(IsolatedAsyncioTestCase):

    async def test_process_data(self):
        """
        Testing application service callback
        """

        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("app1", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()
        shared_storage = {
        }

        # testing correct case
        message = nats.create_message(23.45, MessageSchemas.IOT_DATA_MESSAGE)
        self.assertTrue(check_internal_data(message, nats, shared_storage, None))
        await process_data(message, nats, shared_storage, None)
        self.assertEqual(len(nats._dict["internal.data.out"]), 1)

        # testing incorrect case (not internal)
        message = nats.create_message(23.45, MessageSchemas.IOT_DATA_MESSAGE)
        message.sender_id = "sat1"
        self.assertFalse(check_internal_data(message, nats, shared_storage, None))

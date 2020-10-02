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
import pathlib
from kubesat.testing import FakeNatsHandler
from kubesat.validation import MessageSchemas, check_internal
from kubesat.message import Message
from rl_service import update_iot_phonebook, update_grstn_phonebook, \
    update_phonebook, update_buffered_packets, update_packets_received, update_rl, give_reward, take_action
from rl_service import agents, initialize_rl, rl_step

class Tests(IsolatedAsyncioTestCase):
    async def test_initialize_rl(self):
        """
        Test Initializing RL 
        """
        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("rl1", "0.0.0.0", "4222", loop=loop, user="a", password = "b")
        await nats.connect()
        model_path = "./saved_model_simple_scenario"
        weights_path = "./saved_weights_simple_scenario/dqn_dataEnv-v0_weights.h5f"
        shared_storage = {
          "phonebook": {"cubesat_1": True
            },
          "iot_phonebook": {"iot_1": False
          },
          "ground_phonebook":{
                            "groundstation_1": False
          },
          "packets_received": {
            "groundstation_1": 0
          },
          "buffered_packets": 0,
          "last_buffered_packets": 0,
          "predict_mode": True,
          "weights_location": weights_path,
          "model_location": model_path,
          "new_phonebook": True,
          "new_iot_phonebook": True,
          "new_ground_phonebook": True
        }
        await initialize_rl(nats, shared_storage, None)
        self.assertTrue(len(agents)>0)

    async def test_rl_step(self):
        """
        Test RL step
        """
        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("rl1", "0.0.0.0", "4222", loop=loop, user="a", password = "b")
        await nats.connect()
        model_path = "./saved_model_simple_scenario"
        weights_path = "./saved_weights_simple_scenario/dqn_dataEnv-v0_weights.h5f"
        shared_storage = {
          "phonebook": {"cubesat_1": True
            },
          "iot_phonebook": {"iot_1": False
          },
          "ground_phonebook":{
                            "groundstation_1": False
          },
          "packets_received": {
            "groundstation_1": 0
          },
          "buffered_packets": 0,
          "last_buffered_packets": 0,
          "predict_mode": True,
          "weights_location": weights_path,
          "model_location": model_path,
          "new_phonebook": True,
          "new_iot_phonebook": True,
          "new_ground_phonebook": True,
          "automatic": False
        }
        await initialize_rl(nats, shared_storage, None)
        self.assertTrue(await rl_step(None, nats, shared_storage, None))
        shared_storage = {
          "phonebook": {"cubesat_1": True
            },
          "iot_phonebook": {"iot_1": False
          },
          "ground_phonebook":{
                            "groundstation_1": False
          },
          "packets_received": {
            "groundstation_1": 0
          },
          "buffered_packets": 0,
          "last_buffered_packets": 0,
          "predict_mode": False,
          "weights_location": weights_path,
          "model_location": model_path,
          "new_phonebook": True,
          "new_iot_phonebook": True,
          "new_ground_phonebook": True,
          "automatic": False
        }
        self.assertFalse(await rl_step(None, nats, shared_storage, None))
        shared_storage = {
          "phonebook": {"cubesat_1": True
            },
          "iot_phonebook": {"iot_1": False
          },
          "ground_phonebook":{
                            "groundstation_1": False
          },
          "packets_received": {
            "groundstation_1": 0
          },
          "buffered_packets": 0,
          "last_buffered_packets": 0,
          "predict_mode": False,
          "weights_location": weights_path,
          "model_location": model_path,
          "new_phonebook": True,
          "new_iot_phonebook": True,
          "new_ground_phonebook": True,
          "automatic": True
        }
        self.assertTrue(await rl_step(None, nats, shared_storage, None))


    async def test_update_iot_phonebook(self):
        """
        Testing whether iot phonebook updates work properly
        """

        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("rl1", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()

        # testing whether receiving works
        shared_storage = {
            "phonebook": {
                "sat1": False,
                "sat2": False
            },
            "iot_phonebook": {
                "iot1": True,
                "iot2": False
            },
            "ground_phonebook": {
                "grstn1": False,
                "grstn2": False
            },
            "buffered_packets": 2365,
            "packets_received": {
                "grstn1": 212,
                "grstn2": 573
            }
        }

        # testing correct case
        message = nats.create_message({
            "iot1": False,
            "iot2": True
        }, MessageSchemas.PHONEBOOK_MESSAGE)

        await update_iot_phonebook(message, nats, shared_storage, None)
        self.assertTrue(shared_storage["iot_phonebook"]["iot2"])
        self.assertFalse(shared_storage["iot_phonebook"]["iot1"])

        # testing wrong case
        message = nats.create_message({
            "iot1": True,
            "iot2": False
        }, MessageSchemas.PHONEBOOK_MESSAGE)
        message.origin_id = "sat2"
        await update_iot_phonebook(message, nats, shared_storage, None)
        self.assertTrue(shared_storage["iot_phonebook"]["iot2"])
        self.assertFalse(shared_storage["iot_phonebook"]["iot1"])

    async def test_update_ground_phonebook(self):
        """
        Testing whether groundd phonebook updates work properly
        """

        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("rl1", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()

        # testing whether receiving works
        shared_storage = {
            "phonebook": {
                "sat1": False,
                "sat2": False
            },
            "iot_phonebook": {
                "iot1": True,
                "iot2": False
            },
            "ground_phonebook": {
                "grstn1": False,
                "grstn2": False
            },
            "buffered_packets": 2365,
            "packets_received": {
                "grstn1": 212,
                "grstn2": 573
            }
        }

        # testing correct internal case
        message = nats.create_message({
            "grstn1": False,
            "grstn2": True
        }, MessageSchemas.PHONEBOOK_MESSAGE)

        await update_grstn_phonebook(message, nats, shared_storage, None)
        self.assertTrue(shared_storage["ground_phonebook"]["grstn2"])
        self.assertFalse(shared_storage["ground_phonebook"]["grstn1"])

        # testing wrong not internal case
        message = nats.create_message({
            "grstn1": True,
            "grstn2": False
        }, MessageSchemas.PHONEBOOK_MESSAGE)
        message.origin_id = "sat2"
        await update_grstn_phonebook(message, nats, shared_storage, None)
        self.assertTrue(shared_storage["ground_phonebook"]["grstn2"])
        self.assertFalse(shared_storage["ground_phonebook"]["grstn1"])

    async def test_update_phonebook(self):
        """
        Testing whether phonebook updates work properly
        """

        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("rl1", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()

        # testing whether receiving works
        shared_storage = {
            "phonebook": {
                "sat1": False,
                "sat2": False
            },
            "iot_phonebook": {
                "iot1": True,
                "iot2": False
            },
            "ground_phonebook": {
                "grstn1": False,
                "grstn2": False
            },
            "buffered_packets": 2365,
            "packets_received": {
                "grstn1": 212,
                "grstn2": 573
            }
        }

        # testing correct internal case
        message = nats.create_message({
            "sat1": False,
            "sat2": True
        }, MessageSchemas.PHONEBOOK_MESSAGE)

        await update_phonebook(message, nats, shared_storage, None)
        self.assertTrue(shared_storage["phonebook"]["sat2"])
        self.assertFalse(shared_storage["phonebook"]["sat1"])

        # testing wrong not internal case
        message = nats.create_message({
            "sat1": True,
            "sat2": False
        }, MessageSchemas.PHONEBOOK_MESSAGE)
        message.origin_id = "sat2"
        await update_phonebook(message, nats, shared_storage, None)
        self.assertTrue(shared_storage["phonebook"]["sat2"])
        self.assertFalse(shared_storage["phonebook"]["sat1"])

    async def test_update_buffer_size(self):
        """
        Testing whether buffer size updates work properly
        """

        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("rl1", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()

        # testing whether receiving works
        shared_storage = {
            "phonebook": {
                "sat1": False,
                "sat2": False
            },
            "iot_phonebook": {
                "iot1": True,
                "iot2": False
            },
            "ground_phonebook": {
                "grstn1": False,
                "grstn2": False
            },
            "buffered_packets": 2365,
            "packets_received": {
                "grstn1": 212,
                "grstn2": 573
            }
        }

        # testing correct internal case
        message = nats.create_message(1234, MessageSchemas.BUFFER_MESSAGE)

        await update_buffered_packets(message, nats, shared_storage, None)
        self.assertEqual(shared_storage["buffered_packets"], 1234)

        # testing wrong not internal case
        message = nats.create_message(2234, MessageSchemas.BUFFER_MESSAGE)
        message.origin_id = "sat2"
        await update_buffered_packets(message, nats, shared_storage, None)
        self.assertEqual(shared_storage["buffered_packets"], 1234)

    async def test_update_packets_received(self):
        """
        Testing whether packets received updates work properly
        """

        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("rl1", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()

        # testing whether receiving works
        shared_storage = {
            "phonebook": {
                "sat1": False,
                "sat2": False
            },
            "iot_phonebook": {
                "iot1": True,
                "iot2": False
            },
            "ground_phonebook": {
                "grstn1": False,
                "grstn2": False
            },
            "buffered_packets": 2365,
            "packets_received": {
                "grstn1": 212,
                "grstn2": 573
            }
        }

        # testing correct internal case
        message = nats.create_message(1234, MessageSchemas.BUFFER_MESSAGE)
        message.origin_id = "grstn1"
        await update_packets_received(message, nats, shared_storage, None)
        self.assertEqual(shared_storage["packets_received"]["grstn1"], 1446)

    async def test_update_rl(self):
        """
        Testing whether rl service provides proper new inputs for RL environment
        """

        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("rl1", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()

        # testing whether receiving works
        shared_storage = {
            "predict_mode": False,
            "phonebook": {
                "sat1": False,
                "sat2": False
            },
            "iot_phonebook": {
                "iot1": True,
                "iot2": False
            },
            "ground_phonebook": {
                "grstn1": False,
                "grstn2": False
            },
            "buffered_packets": 2365,
            "packets_received": {
                "grstn1": 212,
                "grstn2": 573
            }
        }

        message = nats.create_message(None, MessageSchemas.RL_MESSAGE)
        response = await update_rl(message, nats, shared_storage, None)
        self.assertIsInstance(response, Message)
        self.assertEqual(response.data.keys(), {
            "phonebook": None,
            "iot_phonebook": None,
            "ground_phonebook": None,
            "buffered_packets": None
        }.keys())
        self.assertEquals(response.data["phonebook"], {
                "sat1": False,
                "sat2": False
            })
        self.assertEquals(response.data["iot_phonebook"], {
                "iot1": True,
                "iot2": False
            })
        self.assertEquals(response.data["ground_phonebook"], {
                "grstn1": False,
                "grstn2": False
            })
        self.assertEquals(response.data["buffered_packets"], 2365)

    async def test_give_reward(self):
        """
        Testing whether rl service provides new rewards to the RL environment
        """

        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("rl1", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()

        # testing whether receiving works
        shared_storage = {
            "phonebook": {
                "sat1": False,
                "sat2": False
            },
            "iot_phonebook": {
                "iot1": True,
                "iot2": False
            },
            "ground_phonebook": {
                "grstn1": False,
                "grstn2": False
            },
            "buffered_packets": 2365,
            "last_buffered_packets": 2325,
            "predict_mode": False,
            "packets_received": {
                "grstn1": 212,
                "grstn2": 573
            }
        }

        message = nats.create_message(None, MessageSchemas.RL_MESSAGE)
        response = await give_reward(message, nats, shared_storage, None)
        self.assertIsInstance(response, Message)
        self.assertEqual(response.data, 7860)

    async def test_take_action(self):
        """
        Testing whether the RL service emits the proper messages upon receiving a new action
        """

        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("rl1", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()

        # testing whether receiving works
        shared_storage = {
            "phonebook": {
                "sat1": False,
                "sat2": False
            },
            "iot_phonebook": {
                "iot1": True,
                "iot2": False
            },
            "ground_phonebook": {
                "grstn1": False,
                "grstn2": False
            },
            "buffered_packets": 2365,
            "packets_received": {
                "grstn1": 212,
                "grstn2": 573
            }
        }

        # testing correct internal case
        message = nats.create_message({"action": "sending", "id": "sat1"}, MessageSchemas.RL_ACTION_MESSAGE)

        await take_action(message, nats, shared_storage, None)
        self.assertEqual(len(nats._dict["internal.rl-action.mode"]), 1)
        self.assertEqual(nats._dict["internal.rl-action.mode"][0].data, "sending")
        self.assertEqual(len(nats._dict["command.point"]), 1)
        self.assertEqual(nats._dict["command.point"][0].data, "sat1")


        # testing wrong not internal case
        message = nats.create_message({"action": "sending", "id": "sat1"}, MessageSchemas.RL_ACTION_MESSAGE)
        message.origin_id = "sat2"
        await take_action(message, nats, shared_storage, None)
        self.assertEqual(len(nats._dict["internal.rl-action.mode"]), 1)
        self.assertEqual(nats._dict["internal.rl-action.mode"][0].data, "sending")
        self.assertEqual(len(nats._dict["command.point"]), 1)
        self.assertEqual(nats._dict["command.point"][0].data, "sat1")

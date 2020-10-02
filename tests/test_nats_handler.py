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

"""
Tests for the NatsHandler class. Expects that a nats server is running on 0.0.0.0:4222 and has user "a"
with password "b". This can be done by running "nats-server --user a --pass b" in terminal.
"""
import asyncio
import unittest
from unittest import TestCase, IsolatedAsyncioTestCase
from time import sleep
import sys
import os
from kubesat.nats_handler import NatsHandler
from kubesat.message import Message
from kubesat.validation import MessageSchemas
from jsonschema.exceptions import ValidationError

class Tests(IsolatedAsyncioTestCase):

    async def test_connect(self):
        """
        Testing whether connecting to the NATS server works.
        """
        loop = self._asyncioTestLoop
        nats = NatsHandler("test", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        result = await nats.connect()
        self.assertTrue(result)
        await nats.disconnect()

    async def test_disconnect(self):
        """
        Testing whether disconnecting from the NATS server works
        """
        loop = self._asyncioTestLoop
        nats = NatsHandler("test", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        result = await nats.connect()
        self.assertTrue(result)
        result = await nats.disconnect()
        self.assertTrue(result)

    async def test_subscribe(self):
        """
        Testing whether the subscription mechanism works properly and rejects invalid channel names
        """

        loop = self._asyncioTestLoop
        nats = NatsHandler("test", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()

        async def callback(msg):
            print("Got message")

        result = await nats.subscribe_callback("subscribe-test", callback)
        self.assertTrue(result)
        await nats.disconnect()

    async def test_unsubscribe(self):
        """
        Tests unsubscribing from a channel and whether invalid names get rejected
        """

        loop = self._asyncioTestLoop
        nats = NatsHandler("test", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()

        async def callback(msg):
            print("Got message")

        await nats.subscribe_callback("subscribe-test", callback)
        result = await nats.unsubscribe_callback("foo", callback)
        self.assertFalse(result)
        result = await nats.unsubscribe_callback("subscribe-test", callback)
        self.assertTrue(result)
        await nats.disconnect()

    async def test_publish(self):
        """
        Testing publishing to a channel
        """

        loop = self._asyncioTestLoop
        nats = NatsHandler("test", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()

        message = Message.decode_json({
            "sender_ID": "User",
            "time_sent": "2020-07-06",
            "data": {
                "testData": "This is a test"
            }
        }, MessageSchemas.TEST_MESSAGE)

        result = await nats.send_message("subscribe-test", message)
        self.assertTrue(result)
        await nats.disconnect()

    async def test_send_data(self):
        """
        Testing whether sending data to a channel works.
        """

        loop = self._asyncioTestLoop
        nats = NatsHandler("test", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()

        message = Message.decode_json({
            "sender_ID": "User",
            "time_sent": "2020-07-06",
            "data": {
                "testData": "This is a test"
            }
        }, MessageSchemas.TEST_MESSAGE)

        result = await nats.send_data("subscribe-test", message)
        self.assertTrue(result)
        await nats.disconnect()
        self.assertEqual(len(nats.data_table), 1)


    async def test_receive(self):
        """
        TODO: LOOK at first comment inside test--see if resolved yet
        
        Testing whether receiving actually works and whether the callback is called. Could not figure out yet
        how to assert within the callback. USE WITH CAUTION!! Must check the print output to see if the messages
        were actually received
        """
        # TODO: Figure out how to assert within the callback and check that it is called in the first place

        print("Starting")
        loop = self._asyncioTestLoop
        nats = NatsHandler("test", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()

        async def callback(msg):
            print("Got message")
            print(msg)
            self.assertEquals(Message.decode_raw(msg.data, MessageSchemas.TEST_MESSAGE).encode_json(), 
                {
                    "sender_ID": "User",
                    "time_sent": "2020-07-06",
                    "data": {
                        "testData": "This is a test"
                    }
                }
            )
            print("Is equal")
            raise ValueError("TEST")

        await nats.subscribe_callback("subscribe-test", callback)

        message = Message.decode_json({
            "sender_ID": "User",
            "time_sent": "2020-07-06",
            "data": {
                "testData": "This is a test"
            }
        }, MessageSchemas.TEST_MESSAGE)
        await nats.send_message("subscribe-test", message)
        await nats.disconnect()

    async def test_request_response(self):
        """
        Testing whether request response works and whether the callback is called.
        """

        loop = self._asyncioTestLoop
        loop.set_exception_handler(None)
        nats = NatsHandler("test", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()

        async def callback(msg):
            print("Got message")
            loop = self._asyncioTestLoop
            raw_message = msg
            msg = Message.decode_raw(msg.data, MessageSchemas.TEST_MESSAGE)
            print(msg)
            self.assertEqual(msg.encode_json(), {
                    "sender_ID": "User",
                    "origin_ID": "User",
                    "message_type": "test_message",
                    "time_sent": "2020-07-06",
                    "data": {
                        "testData": "This is a test"
                    }
                })
            await nats.send_message(raw_message.reply, msg)

        await nats.subscribe_callback("response-test", callback)

        message = Message.decode_json({
            "sender_ID": "User",
            "time_sent": "2020-07-06",
            "data": {
                "testData": "This is a test"
            }
        }, MessageSchemas.TEST_MESSAGE)

        response = await nats.request_message("response-test", message, MessageSchemas.TEST_MESSAGE, timeout=1)
        self.assertEqual(response.encode_json(), {
                    "sender_ID": "test",
                    "origin_ID": "User",
                    "message_type": "test_message",
                    "time_sent": "2020-07-06",
                    "data": {
                        "testData": "This is a test"
                    }
                })
        result = await nats.unsubscribe_callback("response-test", callback)
        self.assertTrue(result)
        await nats.disconnect()

    async def test_create_message(self):
        """
        Testing whether message creation works.
        """
        loop = self._asyncioTestLoop
        nats = NatsHandler("test", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        nats.time_sent = "2020-07-06"
        nats.sender_id = "1"
        message = nats.create_message({
                        "testData": "This is a test"
                    }, MessageSchemas.TEST_MESSAGE)
        self.assertEqual(message.sender_id, "1")
        self.assertEqual(message.time_sent, "2020-07-06")
        self.assertEqual(message.data, {
                        "testData": "This is a test"
                    })
        with self.assertRaises(ValidationError):
            message = nats.create_message({
                        "testData": "This is a test"
                    }, MessageSchemas.ORBIT_MESSAGE)

    async def test_retrieve_data_message(self):
        """
        Testing whether retrieving data from the internal table and creating a message works
        """
        loop = self._asyncioTestLoop
        nats = NatsHandler("test", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        message = nats.create_message({
                        "testData": "This is a test"
                    }, MessageSchemas.TEST_MESSAGE)
        nats.data_table["someID"] = message
        self.assertEqual(len(nats.data_table), 1)
        new_message = await nats.retrieve_data_message("someID")
        self.assertEqual(message.data, new_message.data)
        self.assertEqual(len(nats.data_table), 0)

        with self.assertRaises(KeyError):
            new_message = await nats.retrieve_data_message("someID")

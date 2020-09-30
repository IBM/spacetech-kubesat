import asyncio
import unittest
from unittest import TestCase, IsolatedAsyncioTestCase
from data_service import receive_packet, buffer, buffer_packet, update_pointing_list, send_data
from kubesat.message import Message
from kubesat.nats_handler import NatsHandler
from kubesat.validation import MessageSchemas, check_pointing_and_mode, check_internal, check_internal_data, check_pointing
from kubesat.testing import FakeNatsHandler
import time

class Tests(IsolatedAsyncioTestCase):

    async def test_receive_data(self):
        """
        Testing true case and edge cases for iot send data
        """

        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("data1", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()

        # testing whether receiving works
        shared_storage = {
            "pointing": ["sat1"],
            "pointing_to": "sat1",
            "mode": "receiving"
        }
        message = nats.create_message(23.12, MessageSchemas.IOT_DATA_MESSAGE)
        message.sender_id = "sat1"
        self.assertTrue(check_pointing_and_mode(message, nats, shared_storage, None))
        await receive_packet(message, nats, shared_storage, None)
        self.assertEqual(len(nats._dict["internal.data.in"]), 1)

        # testing whether receiving blocks if in wrong mode
        shared_storage = {
            "pointing": ["sat1"],
            "pointing_to": "sat1",
            "mode": "sending"
        }
        message = nats.create_message(23.12, MessageSchemas.IOT_DATA_MESSAGE)
        message.sender_id = "sat1"
        self.assertFalse(check_pointing_and_mode(message, nats, shared_storage, None))

        # testing whether receiving blocks if not pointing
        shared_storage = {
            "pointing": ["sat2"],
            "pointing_to": "sat1",
            "mode": "receiving"
        }
        message = nats.create_message(23.12, MessageSchemas.IOT_DATA_MESSAGE)
        message.sender_id = "sat1"
        self.assertFalse(check_pointing_and_mode(message, nats, shared_storage, None))

        # testing whether receiving blocks not pointing
        shared_storage = {
            "pointing": ["sat1"],
            "pointing_to": "sat2",
            "mode": "receiving"
        }
        message = nats.create_message(23.12, MessageSchemas.IOT_DATA_MESSAGE)
        message.sender_id = "sat1"
        self.assertFalse(check_pointing_and_mode(message, nats, shared_storage, None))

    async def test_buffer_packet(self):
        """
        Testing relay callback and edge cases
        """

        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("data1", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect() 
        shared_storage = {
            "pointing": ["sat1"],
            "mode": "receiving"
        }

        message = nats.create_message(23.12, MessageSchemas.IOT_DATA_MESSAGE)
        self.assertTrue(check_internal_data(message, nats, shared_storage, None))

        await buffer_packet(message, nats, shared_storage, None)
        self.assertEqual(buffer.qsize(), 1)
        buffer.get()

        shared_storage = {
            "pointing": ["sat1"],
            "mode": "receiving"
        }

        message = nats.create_message(23.12, MessageSchemas.IOT_DATA_MESSAGE)
        message.sender_id = "sat2"
        self.assertFalse(check_internal_data(message, nats, shared_storage, None))

    async def test_update_pointing_list(self):
        """
        Tests whether the list of sats pointing at the satellite is properly updated
        """

        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("sat3", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()
        shared_storage = {
            "pointing": []
        }

        message = nats.create_message({
            "state":{
                "sat1": {
                    "orbit":{
                        "semimajor_axis": 12742500.0,
                        "eccentricity": 0.0,
                        "inclination": 0.78,
                        "perigee_argument": 1.570796,
                        "right_ascension_of_ascending_node": 0.0,
                        "anomaly": 1.570796,
                        "anomaly_type": "TRUE",
                        "orbit_update_date":"2021-12-02T00:00:00.000",
                        "frame": "EME",
                        "attitude":"sat3"
                    },
                    "target_in_view": True,
                    "last_update_time": "2021-12-02T03:00:00.000",
                    "mode": "sending"
                }
            }
        }, MessageSchemas.STATE_MESSAGE)

        message.origin_id = "sat1"
        await update_pointing_list(message, nats, shared_storage, None)
        self.assertEqual(shared_storage["pointing"], ["sat1"])

        message = nats.create_message({
            "state":{
                "sat2": {
                    "orbit":{
                        "semimajor_axis": 12742500.0,
                        "eccentricity": 0.0,
                        "inclination": 0.1,
                        "perigee_argument": 1.0,
                        "right_ascension_of_ascending_node": 0.0,
                        "anomaly": 0.0,
                        "anomaly_type": "TRUE",
                        "orbit_update_date":"2021-12-02T00:00:00.000",
                        "frame": "EME",
                        "attitude":"sat3"
                    },
                "target_in_view": True,
                "last_update_time": "2021-12-02T03:00:00.000",
                "mode": "sending"
                }
            }
        }, MessageSchemas.STATE_MESSAGE)
        message.origin_id = "sat2"
        await update_pointing_list(message, nats, shared_storage, None)
        self.assertEqual(shared_storage["pointing"], ["sat1", "sat2"])

        message = nats.create_message({
            "state":{
                "sat1": {
                    "orbit":{
                        "semimajor_axis": 12742500.0,
                        "eccentricity": 0.0,
                        "inclination": 0.78,
                        "perigee_argument": 1.570796,
                        "right_ascension_of_ascending_node": 0.0,
                        "anomaly": 1.570796,
                        "anomaly_type": "TRUE",
                        "orbit_update_date":"2021-12-02T00:00:00.000",
                        "frame": "EME",
                        "attitude":"ground1"
                    },
                    "target_in_view": True,
                    "last_update_time": "2021-12-02T03:00:00.000",
                    "mode": "sending"
                }
            }
        }, MessageSchemas.STATE_MESSAGE)
        message.origin_id = "sat1"
        await update_pointing_list(message, nats, shared_storage, None)
        self.assertEqual(shared_storage["pointing"], ["sat2"])

        message = nats.create_message({
            "state":{
                "sat2": {
                    "orbit":{
                        "semimajor_axis": 12742500.0,
                        "eccentricity": 0.0,
                        "inclination": 0.1,
                        "perigee_argument": 1.0,
                        "right_ascension_of_ascending_node": 0.0,
                        "anomaly": 0.0,
                        "anomaly_type": "TRUE",
                        "orbit_update_date":"2021-12-02T00:00:00.000",
                        "frame": "EME",
                        "attitude":"sat3"
                    },
                    "target_in_view": False,
                    "last_update_time": "2021-12-02T03:00:00.000",
                    "mode": "sending"
                }
            }
        }, MessageSchemas.STATE_MESSAGE)
        message.origin_id = "sat2"
        await update_pointing_list(message, nats, shared_storage, None)
        self.assertEqual(shared_storage["pointing"], [])

        message = nats.create_message({
            "state":{
                "sat1": {
                    "orbit":{
                        "semimajor_axis": 12742500.0,
                        "eccentricity": 0.0,
                        "inclination": 0.78,
                        "perigee_argument": 1.570796,
                        "right_ascension_of_ascending_node": 0.0,
                        "anomaly": 1.570796,
                        "anomaly_type": "TRUE",
                        "orbit_update_date":"2021-12-02T00:00:00.000",
                        "frame": "EME",
                        "attitude":"sat3"
                    },
                    "target_in_view": False,
                    "last_update_time": "2021-12-02T03:00:00.000",
                    "mode": "sending"
                }
            }
        }, MessageSchemas.STATE_MESSAGE)
        message.origin_id = "sat1"
        await update_pointing_list(message, nats, shared_storage, None)
        self.assertEqual(shared_storage["pointing"], [])

        shared_storage = {
            "pointing_to": "io1"
        }

        message = nats.create_message({
            "state":{
                "sat3": {
                    "orbit":{
                        "semimajor_axis": 12742500.0,
                        "eccentricity": 0.0,
                        "inclination": 0.78,
                        "perigee_argument": 1.570796,
                        "right_ascension_of_ascending_node": 0.0,
                        "anomaly": 1.570796,
                        "anomaly_type": "TRUE",
                        "orbit_update_date":"2021-12-02T00:00:00.000",
                        "frame": "EME",
                        "attitude":"sat1"
                    },
                    "target_in_view": True,
                    "last_update_time": "2021-12-02T03:00:00.000",
                    "mode": "sending"
                }
            }
        }, MessageSchemas.STATE_MESSAGE)
        await update_pointing_list(message, nats, shared_storage, None)
        self.assertEqual(shared_storage["pointing_to"], "sat1")

        message = nats.create_message({
            "state":{
                "sat3": {
                    "orbit":{
                        "semimajor_axis": 12742500.0,
                        "eccentricity": 0.0,
                        "inclination": 0.78,
                        "perigee_argument": 1.570796,
                        "right_ascension_of_ascending_node": 0.0,
                        "anomaly": 1.570796,
                        "anomaly_type": "TRUE",
                        "orbit_update_date":"2021-12-02T00:00:00.000",
                        "frame": "EME",
                        "attitude":"sat1"
                    },
                    "target_in_view": False,
                    "last_update_time": "2021-12-02T03:00:00.000",
                    "mode": "sending"
                }
            }
        }, MessageSchemas.STATE_MESSAGE)
        await update_pointing_list(message, nats, shared_storage, None)
        self.assertEqual(shared_storage["pointing_to"], "nadir_tracking")

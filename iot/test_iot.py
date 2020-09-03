import asyncio
import unittest
import math
from unittest import TestCase, IsolatedAsyncioTestCase
from iot_service import send_data, soil_water_content, fertilization_level
from kubesat.message import Message
from kubesat.nats_handler import NatsHandler
from kubesat.validation import MessageSchemas
from kubesat.testing import FakeNatsHandler
from datetime import datetime
import time

class Tests(IsolatedAsyncioTestCase):

    async def test_iot_send_data(self):
        """
        Tests whether a new data packet is sent upon receiving a timestep signal
        """
        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("iot1", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()
        message = nats.create_message({"time": "2020-07-05T09:51:49.8"}, MessageSchemas.TIMESTEP_MESSAGE)
        shared_storage = {
            "data_rate": 5
        }
        await send_data(message, nats, shared_storage, None)
        self.assertEqual(len(nats._dict["data.out"]), 5)
    
    async def test_soil_water_content(self):
        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("iot1", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()

        shared_storage = {
            "data_rate": 5
        }

        message = nats.create_message({"time": "2020-07-05T09:51:49.8"}, MessageSchemas.TIMESTEP_MESSAGE)
        await soil_water_content(message, nats, shared_storage, None)

        time_struct = datetime.strptime("2020-07-05T09:51:49.8", "%Y-%m-%dT%H:%M:%S.%f").timetuple()
        total_seconds = time_struct.tm_hour*3600 + time_struct.tm_min*60 + time_struct.tm_sec
        data_value = 10 * math.cos(2 * math.pi * total_seconds * (1 / 86400)) + 40

        self.assertEqual(nats._dict["data.out"][0].data, data_value)

    async def test_fertilization_level(self):
        """
        Tests creating fertilization data
        """
        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("iot1", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()

        shared_storage = {
            "data_rate": 5
        }

        message = nats.create_message({"time": "2020-07-05T09:51:49.8"}, MessageSchemas.TIMESTEP_MESSAGE)
        await fertilization_level(message, nats, shared_storage, None)

        time_struct = datetime.strptime("2020-07-05T09:51:49.8", "%Y-%m-%dT%H:%M:%S.%f")
        total_seconds = (time_struct-datetime(1970,1,1)).total_seconds()
        seconds_in_week = total_seconds % (60 * 60 * 24 * 7)
        data_value = 0.25 * math.sin(2 * math.pi * seconds_in_week * (1/604800)) + 0.25

        self.assertEqual(nats._dict["data.out"][0].data, data_value)

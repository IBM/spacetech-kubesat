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
        

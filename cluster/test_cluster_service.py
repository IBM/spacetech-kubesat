import asyncio
import unittest
from unittest import TestCase, IsolatedAsyncioTestCase

from kubesat.testing import FakeNatsHandler, FakeLogger
from cluster_service import send_ip_address
from kubesat.validation import MessageSchemas, check_internal_data, SharedStorageSchemas



class Test(IsolatedAsyncioTestCase):
    async def test_send_ip_address(self):
        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("cubesat_1", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()
        
        shared_storage = dict()

        message = nats.create_message({"time":""}, MessageSchemas.TIMESTEP_MESSAGE)
        
        await send_ip_address(message, nats, shared_storage, None)
        self.assertEqual(nats._dict["cluster.ip"][0].data, "api_host")
    
    async def test_cluster(self):
        # test here
        pass
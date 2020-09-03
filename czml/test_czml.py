import asyncio
import unittest
from unittest import TestCase, IsolatedAsyncioTestCase
from kubesat.message import Message
from kubesat.nats_handler import NatsHandler
from kubesat.validation import MessageSchemas
from kubesat.testing import FakeNatsHandler, FakeLogger
import czml_service as graphics_service
import time
import json

class Tests(IsolatedAsyncioTestCase):
    #TODO make this test work (after finishing graphics service)
    async def test_send_visualization_packet(self):
        """
        TODO
        """
        logger = FakeLogger()
        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("cubesat_1", "4222", loop=loop, user="a", password="b")
        await nats.connect()
        f = open("./config/simulation_config/simulation/czml.json")
        
        shared_storage = json.load(f)["shared_storage"]
        shared_storage["swarm"]["cubesat_1"] = {
                "orbit":{
                    "semimajor_axis": 6801395.04,
                    "eccentricity": 0.0008641,
                    "inclination": 0.0,
                    "perigee_argument": 2.0150855958,
                    "right_ascension_of_ascending_node": 3.6338243719,
                    "anomaly": 4.270387838,
                    "anomaly_type": "MEAN",
                    "orbit_update_date":"2020-07-15T00:00:00.000",
                    "frame": "EME",
                    "attitude": "nadir_tracking"
                },
                "target_in_view": True,
                "last_update_time": "2010-07-02T03:00:00.000",
                "mode": "receiving"
            }
        shared_storage["grstns"]["grstn_1"] = {
                "location": {
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "altitude": 0.0
                }
            }
        data = {
                "sender_ID": "cubesat_2",
                "time_sent": "2021-07-31T03:00:00.000",
                "data":{
                    "time": "2021-07-31T03:00:00.000"
                }
            }
        message = nats.create_message(data["data"], MessageSchemas.TIMESTEP_MESSAGE)
        print(shared_storage)
        await graphics_service.send_visualization_packet(message, nats, shared_storage, logger)

        for i in nats._dict["graphics.grstn2sat"]:
            print(i.data)
        self.assertTrue(False)      

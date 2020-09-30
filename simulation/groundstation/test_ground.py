import asyncio
import unittest
from unittest import TestCase, IsolatedAsyncioTestCase
from kubesat.testing import FakeNatsHandler
from kubesat.validation import MessageSchemas, check_pointing_data
from kubesat.message import Message
from ground_service import receive_data, update_pointing_list, update_cluster
import ground_service as ground_service


class Tests(IsolatedAsyncioTestCase):

    async def test_receive_data(self):
        """
        Testing true case and edge cases for receiving data
        """

        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("ground1", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()

        # testing whether receiving works
        shared_storage = {
            "pointing": ["sat1"],
            "packets_received": 0
        }
        message = nats.create_message(23.12, MessageSchemas.IOT_DATA_MESSAGE)
        message.sender_id = "sat1"
        self.assertTrue(check_pointing_data(message, nats, shared_storage, None))
        await receive_data(message, nats, shared_storage, None)
        self.assertEqual(len(nats._dict["groundstation.packets_received"]), 1)
        self.assertEqual(shared_storage["packets_received"], 1)

        # testing whether edge case is actually not working
        shared_storage = {
            "pointing": ["sat1"],
            "packets_received": 0
        }
        message = nats.create_message(23.12, MessageSchemas.IOT_DATA_MESSAGE)
        message.sender_id = "sat2"
        self.assertFalse(check_pointing_data(message, nats, shared_storage, None))

    async def test_update_pointing_list(self):
        """
        Tests whether the list of sats pointing at the ground station is properly updated
        """

        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("ground1", "0.0.0.0", "4222", loop=loop, user="a", password="b")
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
                        "attitude":"ground1"
                    },
                    "target_in_view": True,
                    "last_update_time": "2021-12-02T03:00:00.000"
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
                        "attitude":"ground1"
                    },
                "target_in_view": True,
                "last_update_time": "2021-12-02T03:00:00.000"
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
                        "attitude":"iot2"
                    },
                    "target_in_view": True,
                    "last_update_time": "2021-12-02T03:00:00.000"
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
                        "attitude":"ground1"
                    },
                "target_in_view": False,
                "last_update_time": "2021-12-02T03:00:00.000"
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
                        "attitude":"ground1"
                    },
                    "target_in_view": False,
                    "last_update_time": "2021-12-02T03:00:00.000"
                }
            }
        }, MessageSchemas.STATE_MESSAGE)
        message.origin_id = "sat1"
        await update_pointing_list(message, nats, shared_storage, None)
        self.assertEqual(shared_storage["pointing"], [])
    
    async def test_update_cluster(self):
        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("cubesat_1", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()

        shared_storage = {
            "ip_map":{
                "cubesat_1":"ip_1",
                "cubesat_2":"ip_2",
                "cubesat_3":"ip_3"
            },
            "ip_cluster_map":{
                "cubesat_1":[],
                "cubesat_2":[],
                "cubesat_3":[]
            }
        }
        message = nats.create_message({"cubesat_1": True, "cubesat_2": True, "cubesat_3":True}, MessageSchemas.PHONEBOOK_MESSAGE)
        await update_cluster(message, nats, shared_storage, None)
        
        cluster_message = {
            "recipient": "cubesat_1",
            "ip_map":["ip_2","ip_3"]
        }

        self.assertTrue(nats._dict["command.cluster"][0], cluster_message)
        self.assertTrue(shared_storage["ip_cluster_map"]["cubesat_1"] == ["ip_2","ip_3"])
    
    async def test_update_sat_ip(self):
        
        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("cubesat_1", "0.0.0.0", "4222", loop=loop, user="a", password="b")
        await nats.connect()

        shared_storage = {
            "ip_map":{},
            "ip_cluster_map":{}
        }

        message = nats.create_message("ip_1", MessageSchemas.IP_ADDRESS_MESSAGE)
        await ground_service.update_sat_ip(message, nats, shared_storage, None)

        self.assertEqual(shared_storage["ip_map"], {"cubesat_1":"ip_1"})
        self.assertEqual(shared_storage["ip_cluster_map"], {"cubesat_1":[]})
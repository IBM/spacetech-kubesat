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
from time import sleep
import sys
import os
import pdb
import orbit_service as orbit_service
from kubesat.message import Message
from kubesat.nats_handler import NatsHandler
from kubesat.orekit import absolute_time_converter_utc_manual, absolute_time_converter_utc_string
from kubesat.validation import MessageSchemas
from kubesat.testing import FakeNatsHandler, FakeLogger
import kubesat.orekit as orekit_utils
import kubesat.testing as utils
import json
import time

class CONSTS:
    """
    Orbits that will be used throughout the test
    """
    ORBIT_1 = {
                    "semimajor_axis": 12742500.0,
                    "eccentricity": 0.0,
                    "inclination": 1.518436,
                    "perigee_argument": 0.34906585,
                    "right_ascension_of_ascending_node": 0.1745329,
                    "anomaly": 0.0,
                    "anomaly_type": "TRUE",
                    "orbit_update_date":"1111-01-01T00:00:00.000",
                    "frame": "EME",
                    "attitude":"nadir_tracking"
    }
    ORBIT_2 = {
                    "semimajor_axis": 12742500.0,
                    "eccentricity": 0.0,
                    "inclination": 1.518436,
                    "perigee_argument": 0.34906585,
                    "right_ascension_of_ascending_node": 0.1745329,
                    "anomaly": 0.0,
                    "anomaly_type": "TRUE",
                    "orbit_update_date":"2222-01-01T00:00:00.000",
                    "frame": "EME",
                    "attitude":"nadir_tracking"
    }
    ORBIT_3 = {
                    "semimajor_axis": 12742500.0,
                    "eccentricity": 0.0,
                    "inclination": 1.518436,
                    "perigee_argument": 0.34906585,
                    "right_ascension_of_ascending_node": 0.1745329,
                    "anomaly": 0.0,
                    "anomaly_type": "TRUE",
                    "orbit_update_date":"3333-01-01T00:00:00.000",
                    "frame": "EME",
                    "attitude":"nadir_tracking"
    }

class Orbit_Tests(IsolatedAsyncioTestCase):
    """
    The test for the orbit_service
    """
    async def test_simulation_timepulse_propagate(self):
        """
        Test the simulation_timepulse_propagate() callback
        """
        # Creating variables that will be used as arguments for the callback
        logger = FakeLogger()
        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("cubesat_1", "4222", loop=loop, user="a", password="b")
        await nats.connect()

        # opening a file that contains a sample shared storage
        f = open("test_orbits_config.json")
        shared_storage = json.load(f)

        # Testing the callback across mulitple timesteps
        for i in range(10, 59):
            # creating sample data
            data = {
                "sender_ID": "cubesat_2",
                "time_sent": "2021-12-05T00:"+str(i)+":00.000",
                "data":{
                    "time": "2021-12-05T00:"+str(i)+":00.000"
                }
            }
            
            orbit_1 = shared_storage["swarm"]["cubesat_1"]["orbit"]
            orbit_2 = shared_storage["swarm"]["cubesat_2"]["orbit"]

            attitude_provider_1 = {"type":"moving_body_tracking", "parameters": shared_storage["swarm"][shared_storage["swarm"]["cubesat_1"]["orbit"]["attitude"]]["orbit"]}
            attitude_provider_2 = {"type":"moving_body_tracking", "parameters": shared_storage["swarm"][shared_storage["swarm"]["cubesat_2"]["orbit"]["attitude"]]["orbit"]}

            message = Message.decode_json(data, MessageSchemas.TIMESTEP_MESSAGE)
            await orbit_service.simulation_timepulse_propagate(message, nats, shared_storage, logger)

            time = absolute_time_converter_utc_string(data["data"]["time"])

            # Creating propagators and attitude provider from orbit configuration of satellites
            propagator_1 = orekit_utils.analytical_propagator(orbit_1)
            propagator_2 = orekit_utils.analytical_propagator(orbit_2)
            attitude_provider_1 = orekit_utils.attitude_provider_constructor(attitude_provider_1["type"], attitude_provider_1["parameters"])
            attitude_provider_2 = orekit_utils.attitude_provider_constructor(attitude_provider_2["type"], attitude_provider_2["parameters"])

            # Setting attitude and propagating the orbit 
            propagator_1.setAttitudeProvider(attitude_provider_1)
            propagator_2.setAttitudeProvider(attitude_provider_2)
            state_1 = propagator_1.propagate(time)
            state_2 = propagator_2.propagate(time)
            
            # Updating param
            cubesat_1_param = orekit_utils.get_keplerian_parameters(state_1)
            cubesat_1_param.update({"attitude": "cubesat_2"})
            cubesat_1_param.update({"frame": "EME"})
            cubesat_2_param = orekit_utils.get_keplerian_parameters(state_2)
            cubesat_2_param.update({"attitude": "cubesat_1"})
            cubesat_2_param.update({"frame": "EME"})

            # Checking to see if simulation_timestep_propagate updated params correctly
            self.assertTrue(shared_storage["swarm"]["cubesat_1"]["orbit"] == cubesat_1_param)
            self.assertTrue(shared_storage["swarm"]["cubesat_2"]["orbit"] == cubesat_2_param)
            self.assertTrue(shared_storage["swarm"]["cubesat_1"]["orbit"]["attitude"] == "cubesat_2")
            self.assertTrue(shared_storage["swarm"]["cubesat_2"]["orbit"]["attitude"] == "cubesat_1")
            print(shared_storage["swarm"]["cubesat_1"]["target_in_view"])
            print(shared_storage["swarm"]["cubesat_2"]["target_in_view"])
            # Making sure that phonebook gets updated properly
            if i <= 48:
                self.assertTrue(shared_storage["sat_phonebook"]["cubesat_2"])
                self.assertTrue(shared_storage["swarm"]["cubesat_2"]["target_in_view"])
            else:
                self.assertFalse(shared_storage["sat_phonebook"]["cubesat_2"])
                self.assertFalse(shared_storage["swarm"]["cubesat_2"]["target_in_view"])
        
    async def test_cubesat_state(self):
        """
        Test for cubesat_state() callback
        """
        # Creating variables that will be used as arguments for the callback
        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("cubesat_1", "4222", loop=loop, user="a", password="b")
        await nats.connect()

        # Opening a file that contains a sample shared storage
        f = open("test_orbits_config.json")
        shared_storage = json.load(f)

        # Updated state that will be sent
        state = {
            "cubesat_1":{
                "orbit":CONSTS.ORBIT_3, "last_update_time":"2022-12-02T03:00:00.000"}
            }

        # Data that will be sent in the message
        data = {
                "sender_ID": "cubesat_2",
                "time_sent": "2020-07-05T09:51:49",
                "data":{
                        "id": "cubesat_1",
                        "state": state
                        }
                }

        message = Message.decode_json(data, MessageSchemas.STATE_MESSAGE)
        await orbit_service.cubesat_state(message, nats, shared_storage, None)
        # Verifying that cubesat_state() worked properly
        self.assertTrue(shared_storage["swarm"]["cubesat_1"] == state["cubesat_1"])


    async def test_cubesat_X_attitude_provider(self):
        """
        Test for cubesat_X_attitude_provider() callback
        """
        # Creating variables that will be used as arguments for the callback
        loop = asyncio.get_running_loop()
        nats = utils.FakeNatsHandler("cubesat_2", "4222", loop=loop, user="a", password="b")
        await nats.connect()

        # Opening a file that contains a sample shared storage
        f = open("test_orbits_config.json")
        shared_storage = json.load(f)

        # Data that will be sent in the message
        data = {
                "sender_ID": "cubesat_2",
                "time_sent": "2020-07-05T09:51:49",
                "data":{
                        "id": "cubesat_1",
                        "attitude": "nadir_tracking",
                        "time":"2022-12-02T03:00:00.000"
                        }
                }

        message = Message.decode_json(data, MessageSchemas.ATTITUDE_MESSAGE)
        await orbit_service.cubesat_X_attitude_provider(message, nats, shared_storage, None)
        # Verifying that "cubesat_1"'s state was updated properly
        self.assertTrue(shared_storage["swarm"]["cubesat_1"]["orbit"]["attitude"] == message.data["attitude"])

    async def test_cubesat_X_point_to_cubesat_Y(self):
        """
        Testing the cubesat_X_point_to_cubesat_Y() callback 
        """
        # Creating variables that will be used as arguments for the callback
        logger = utils.FakeLogger()
        loop = asyncio.get_running_loop()
        nats = utils.FakeNatsHandler("cubesat_1", "4222", loop=loop, user="a", password="b")
        nats.time_sent = "2020-07-05T09:51:49"
        await nats.connect()

        # Opening a file that contains a sample shared storage
        f = open("test_orbits_config.json")
        shared_storage = json.load(f)

        message = nats.create_message("cubesat_3", MessageSchemas.POINTING_MESSAGE)
        await orbit_service.cubesat_X_point_to_cubesat_Y(message, nats, shared_storage, None)
        # Verifying that "cubesat_1"'s state was updated properly
        self.assertTrue(shared_storage["swarm"]["cubesat_1"]["orbit"]["attitude"] == "cubesat_3")
        

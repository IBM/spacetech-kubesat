"""
Tests for the Orbit simulation class. Expects that a nats server is running on 0.0.0.0:4222 and has user "a"
with password "b". This can be done by running "nats-server --user a --pass b" in terminal.
"""

import asyncio 
import unittest
from unittest import TestCase
from time import sleep

import sys
import os

from kubesat.base_simulation import BaseSimulation
from kubesat.validation import MessageSchemas, SharedStorageSchemas

class Tests(TestCase):
    """
    Testing the baseSimulation. TODO: Was not able yet to automate this test. need to check for output and need to 
    send a message from a separate program.
    """

    def test_register_nats(self):
        """
        Testing whether registering routes for NATS works
        """

        sim = BaseSimulation("template_service",SharedStorageSchemas.TEMPLATE_STORAGE)

        @sim.subscribe_nats_callback("publish.test", MessageSchemas.TEST_MESSAGE)
        async def test_one(msg, nats, shared_storage, logger):
            pass

        self.assertEqual(len(sim._nats_routes), 2)
        self.assertEqual(len(sim._unsubscribe_nats_routes), 2)

    def test_register_nats_data(self):
        """
        Testing whether registering a NATS data route works
        """

        sim = BaseSimulation("template_service",SharedStorageSchemas.TEMPLATE_STORAGE)

        @sim.subscribe_data_callback("data.test", MessageSchemas.TEST_MESSAGE)
        async def test_two(msg, nats, shared_storage, logger):
            pass

        self.assertEqual(len(sim._nats_routes), 2)
        self.assertEqual(len(sim._unsubscribe_nats_routes), 2)

    def test_register_request(self):
        """
        Testing whether registering requests works
        """

        sim = BaseSimulation("template_service",SharedStorageSchemas.TEMPLATE_STORAGE)

        @sim.request_nats_callback("data.test", MessageSchemas.TEST_MESSAGE)
        async def test_two(msg, nats, shared_storage, logger):
            pass

        self.assertEqual(len(sim._nats_routes), 2)
        self.assertEqual(len(sim._unsubscribe_nats_routes), 2)

    def test_register_schedule(self):
        """
        Testing whether scheduling a callback
        """

        sim = BaseSimulation("template_service",SharedStorageSchemas.TEMPLATE_STORAGE)

        @sim.schedule_callback(3)
        async def test_two(nats, shared_storage, logger):
            pass

        self.assertEqual(len(sim._nats_routes), 2)
        self.assertEqual(len(sim._unsubscribe_nats_routes), 1)

    def test_register_startup_callback(self):
        """
        Testing whether the startup callback registration works
        """

        sim = BaseSimulation("template_service",SharedStorageSchemas.TEMPLATE_STORAGE)

        @sim.startup_callback
        async def startup(nats, shared_storage, logger):
            pass

        self.assertEqual(sim._startup_callback, startup)


        
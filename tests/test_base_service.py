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
Tests for the BaseService class.
"""

import asyncio
import unittest
from unittest import TestCase
from time import sleep

import sys
import os

from kubesat.base_service import BaseService
from kubesat.validation import MessageSchemas, SharedStorageSchemas


class Tests(TestCase):
    """
    Testing the BaseService.
    """

    def test_register_subscribe_nats_callback(self):
        """
        Testing whether registering a NATS subscribe works
        """

        svc = BaseService("template_service",
                          SharedStorageSchemas.TEMPLATE_STORAGE)

        @svc.subscribe_nats_callback("publish.test", MessageSchemas.TEST_MESSAGE)
        async def test_func(msg, nats, shared_storage, logger):
            pass

        self.assertEqual(len(svc._registered_callbacks), 2)
        self.assertEqual(len(svc._unsubscribe_nats_routes), 2)

    def test_register_subscribe_data_callback(self):
        """
        Testing whether registering a data subscribe works
        """

        svc = BaseService("template_service",
                          SharedStorageSchemas.TEMPLATE_STORAGE)

        @svc.subscribe_data_callback("data.test", MessageSchemas.TEST_MESSAGE)
        async def test_func(msg, nats, shared_storage, logger):
            pass

        self.assertEqual(len(svc._registered_callbacks), 2)
        self.assertEqual(len(svc._unsubscribe_nats_routes), 2)

    def test_register_request_nats_callback(self):
        """
        Testing whether registering requests works
        """

        svc = BaseService("template_service",
                          SharedStorageSchemas.TEMPLATE_STORAGE)

        @svc.request_nats_callback("data.test", MessageSchemas.TEST_MESSAGE)
        async def test_func(msg, nats, shared_storage, logger):
            pass

        self.assertEqual(len(svc._registered_callbacks), 2)
        self.assertEqual(len(svc._unsubscribe_nats_routes), 2)

    def test_register_schedule_callback(self):
        """
        Testing whether registering scheduling works
        """

        svc = BaseService("template_service",
                          SharedStorageSchemas.TEMPLATE_STORAGE)

        @svc.schedule_callback(3)
        async def test_func(nats, shared_storage, logger):
            pass

        self.assertEqual(len(svc._registered_callbacks), 2)

    def test_register_startup_callback(self):
        """
        Testing whether the startup callback registration works
        """

        svc = BaseService("template_service",
                          SharedStorageSchemas.TEMPLATE_STORAGE)

        @svc.startup_callback
        async def startup(nats, shared_storage, logger):
            pass

        self.assertEqual(svc._startup_callback, startup)

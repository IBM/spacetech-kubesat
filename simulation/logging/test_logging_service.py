import asyncio
import unittest
from unittest import TestCase, IsolatedAsyncioTestCase
import os.path
from kubesat.message import Message
from kubesat.nats_handler import NatsHandler
from kubesat.validation import MessageSchemas
from kubesat.testing import FakeNatsHandler, FakeLogger
import logging_service as logging_service
from datetime import datetime

class Test(IsolatedAsyncioTestCase):
    async def test_create_log_file(self):
        """
        Testing the creation of the log files
        """
        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("cubesat_1", "4222", loop=loop, user="a", password="b")
        await nats.connect()

        shared_storage={
            "log_path":"./"
        }
        await logging_service.create_log_file(nats, shared_storage, None)
        file_made = False
        for i in os.listdir():
            if f"log-{datetime.utcnow().isoformat()[:19]}" in i:
                file_made = True
                os.remove(f"./{i}")
                break
        self.assertTrue(file_made)

    async def test_print_log(self):
        """
        Testing printing the log info
        """
        loop = asyncio.get_running_loop()
        nats = FakeNatsHandler("cubesat_1", "4222", loop=loop, user="a", password="b")
        await nats.connect()

        shared_storage={
            "log_path":"logger_test"
        }

        message = nats.create_message({
                                            "logged_at":"logging_service",
                                            "line_number":43,
                                            "function": "logger_test",
                                            "level": "level one",
                                            "msg": "This is a test!"
        }, MessageSchemas.LOG_MESSAGE)
        
        await logging_service.print_log(message, nats, shared_storage, None)

        self.assertTrue("logger_test" in os.listdir())
        os.remove("./logger_test")
        

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
import json

from datetime import datetime
from aiologger.loggers.json import JsonLogger
from aiologger.formatters.json import ExtendedJsonFormatter
from aiologger.handlers.base import Handler

from kubesat.message import Message
from kubesat.validation import MessageSchemas
from kubesat.nats_handler import NatsHandler

class NatsLoggingHandler(Handler):
    """
    Custom Handler to log Nats
    """
    def __init__(self, nats_handler, service_type):
        """
        Initialize a NatsLoggingHandler object
        Args:
            nats_handler: nats_handler objects
            service_type: type of service initializing this object
        """
        Handler.__init__(self)
        self.nats_handler = nats_handler
        self.channel = f"logging.{service_type}.{nats_handler.sender_id}"
        self.sender_id = nats_handler.sender_id
        self.service_type = service_type

    async def emit(self, record):
        """
        Format and send the record
        Args:
            record: nats record
        """
        msg = json.loads(self.formatter.format(record))
        # change the way that the time is accessed
        msg = self.nats_handler.create_message(msg, MessageSchemas.LOG_MESSAGE)
        if self.nats_handler:
            assert await self.nats_handler.send_message(self.channel, msg) is True

    async def close(self):
        """
        Close the logger when there is no nats_handler
        """
        self.nats_handler = None

class NatsLoggerFactory:
    """
    Creates Nats loggers
    """
    @staticmethod
    def get_logger(nats_handler, service_type):
        """
        Creates and returns a nats logging handler
        Args:
            nats_handler: a nats_handler object
            service_type: type of service 
        """
        handler = NatsLoggingHandler(nats_handler, service_type)
        formatter = ExtendedJsonFormatter(exclude_fields=["file_path"])
        handler.formatter = formatter
        logger = JsonLogger(name=nats_handler.sender_id)
        logger.add_handler(handler)
        return logger

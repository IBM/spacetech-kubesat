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
from aiologger.loggers.json import JsonLogger

from kubesat.base_service import BaseService
from kubesat.message import Message
from kubesat.nats_handler import NatsHandler
from kubesat.nats_logger import NatsLoggerFactory
from kubesat.validation import validate_json, MessageSchemas


class BaseSimulation(BaseService):
    def __init__(self, service_type: str, schema: dict, config_path: str = None):
        """
        Registers a NATS callback that subscribes to the subject "simulation.timestep". When the callback receives a message, 
        it updates the current time internal to the simulation's NATS handler object. 
        """
        super().__init__(service_type, schema, config_path)

        # subscribing to timestep by default to update time in nats_handler
        @self.subscribe_nats_callback("simulation.timestep", MessageSchemas.TIMESTEP_MESSAGE)
        async def simulation_timepulse(message: Message, nats_handler: NatsHandler, shared_storage: dict, logger: JsonLogger):
            nats_handler.time_sent = message.data["time"]

    async def _load_config(self):
        """
        Override _load_config to get the configuration from a cluster service that has a callback registered on channel "initialize.service"
        for simulation
        """

        try:
            # requesting a config from the config service
            message = self.nats_client.create_message(
                self.service_type, MessageSchemas.SERVICE_TYPE_MESSAGE)
            print(
                f"Requesting config from config service for node {self.service_type}")
            config_response = await self.nats_client.request_message("initialize.service", message, MessageSchemas.CONFIG_MESSAGE, timeout=3)
            print(f"Got config from config service: {config_response}")
            print(f"Validating ...")

            # validate the shared storage section of the config
            validate_json(
                config_response.data["shared_storage"], self._schema)
            self.sender_id = config_response.data["sender_id"]
            self.shared_storage = config_response.data["shared_storage"]

            # write the shared storage and sender ID to Redis
            self.redis_client.set_sender_id(self.sender_id)
            self.redis_client.set_shared_storage(self.shared_storage)
            print(
                f"Successfully initialized {self.sender_id} {self.service_type} from config service")
        except:
            try:
                await super()._load_config()
            except Exception as e:
                raise ValueError(
                    f"Failed to load configuration: {e}")

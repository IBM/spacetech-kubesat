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
import time

from kubesat.base_service import BaseService

SERVICE_TYPE = 'hello'
hello = BaseService(service_type=SERVICE_TYPE,
                    config_path='./service.json')


@hello.schedule_callback(2)
# Send a hello message every two seconds.
async def send_hello_message(nats, shared_storage, logger):
    """
    Send a hello message.

    Args:
        nats (NatsHandler): connection to nats used to send and receive messages
        shared_storage (dict): dictionary that stores local data for the service
        logger (NatsLogger): logger that can be used to communicate the state of the system
    """
    message = nats.create_message({"message": "hello"})

    # Send a hello message to public.hello subject
    await nats.send_message("public.hello", message)
    print(f"SEND : {message.encode_json()}")


@hello.subscribe_nats_callback("public.hello")
# Subscribe public.hello subject
async def receive_ping_message(message, nats, shared_storage, logger):
    message_json = message.encode_json()
    print(f"RECEIVED : {message_json}")
    shared_storage["last_sent"] = message_json['time_sent']


@hello.startup_callback
# Invoke the startup function at the start time
async def startup(nats_handler, shared_storage, logger):
    print(f"{SERVICE_TYPE} in {hello.sender_id} has started.")

if __name__ == '__main__':
    # Start the hello service
    hello.run()

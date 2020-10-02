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

from kubesat.validation import MessageSchemas, SharedStorageSchemas
from kubesat.services import ServiceTypes
from kubesat.base_simulation import BaseSimulation

simulation = BaseSimulation(ServiceTypes.Template, SharedStorageSchemas.TEMPLATE_STORAGE, "./template_config.json")

@simulation.startup_callback
async def test_zero(natsHandler, shared_storage, logger):
    print("Hello, I am starting!!")

@simulation.subscribe_nats_callback("publish-test", MessageSchemas.TEST_MESSAGE)
async def test_one(msg, natsHandler, shared_storage, logger):
    print(msg.encode_json())
    print(natsHandler._connection_string)
    print(shared_storage)
    await logger.error("This is template service")
    message = natsHandler.create_message({
        "testData": "Hello, it's me, 1!"
    }, MessageSchemas.TEST_MESSAGE)
    await natsHandler.send_data("data.test", message)
    print("Sent data 1 ")


@simulation.subscribe_nats_callback("publish-test", MessageSchemas.TEST_MESSAGE)
async def test_two(msg, natsHandler, shared_storage, logger):
    message = natsHandler.create_message({
        "testData": "Hello, it's me, 2!"
    }, MessageSchemas.TEST_MESSAGE)
    message.sender_id = "bogus"
    await natsHandler.send_data("data.test", message)
    print("Sent data 2")

# demonstrating how a validator could work in theory. Normally, you would check the sender_id
async def validator(msg, natsHandler, shared_storage, logger):
    if shared_storage["test_value"] != msg.sender_id:
        shared_storage["test_value"] = msg.sender_id
        return True
    return False

@simulation.subscribe_data_callback("data.test", MessageSchemas.TEST_MESSAGE, validator=validator)
async def test_three(msg, natsHandler, shared_storage, logger):
    print(f"received data response: {msg.encode_json()}")

@simulation.request_nats_callback("get.test.data.", MessageSchemas.TEST_MESSAGE, append_sender_id=True)
async def test_four(msg, natsHandler, shared_storage, logger):
    print(f"Received request {msg.data}")
    return natsHandler.create_message({
        "testData": "Back to you!"
    }, MessageSchemas.TEST_MESSAGE)

@simulation.subscribe_nats_callback("publish-test", MessageSchemas.TEST_MESSAGE)
async def test_five(msg, natsHandler, shared_storage, logger):
    message = natsHandler.create_message({
        "testData": "Are you here?"
    }, MessageSchemas.TEST_MESSAGE)
    response = await natsHandler.request_message(f"get.test.data.{natsHandler.sender_id}", message, MessageSchemas.TEST_MESSAGE)
    print(f"Received response {response.data}")

@simulation.schedule_callback(5)
async def test_six(natsHandler, shared_storage, logger):
    print("Hello again")
    message = natsHandler.create_message({"testData": "This is a test"}, MessageSchemas.TEST_MESSAGE)
    await natsHandler.send_message("publish-test", message)


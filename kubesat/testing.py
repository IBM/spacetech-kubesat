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

# File is used to contain fake handlers, classes, methods, etc
# that are necessary to run test
from queue import Queue
from random import randint
from kubesat.message import Message

class FakeLogger:
    """
    TODO
    """
    async def info(self, msg):
        print(msg)

class FakeNatsHandler:
    """
    Handler that is the interface to a NATS server. Responsible for interacting with the server, checking whether the
    channel the user interacts with are allowed, which is specified through a config file.
    """

    def __init__(self, sender_id, host="0.0.0.0", port="4222", user=None, password=None, nc="NATS", loop="asyncio.get_event_loop()"):
        """
        Initializes NatsHandler.

        Args:
            connection_string (String): Host and port of the NATS server
            nc (nats.aio.client.Client, optional): NATS client object. Defaults to NATS().
            loop (asyncio.event_loop, optional): event loop used to run the callbacks. Defaults to asyncio.get_event_loop().
            filepath (str, optional): Path to the config file. Defaults to "config.json".
        """
        self.sender_id = sender_id
        self.origin_id = sender_id
        self.time_sent = "sometime"
        self._dict = {}
        self.data_table = {}
        self.time_sent = ""
        self.api_host = "api_host"
        
    async def subscribe_callback(self, topic, callback, orig_callback=None):
        """
        TODO
        """
        self._dict[topic] = []

    async def response_callback(self, topic, callback):
        """
        TODO
        """
        async def callback_wrapper(msg):
            pass

    async def unsubscribe_callback(self, topic, callback):
        """
        Unsubscribes callback from a topic.
        Args:
            topic (string): Topic name to unsubscribe from
            callback (function): callback function to remove
        Returns:
            bool: True if successfully unsubscribed, otherwise false
        """
        return True

    async def connect(self):
        """
        Returns:
            bool: True
        """
        return True

    async def send_message(self, topic, message):
        """
        Sends a message to a channel
        Args:
            topic (string): channel name to publish to
            message (object): message to send
        Returns:
            bool: True
        """
        if topic not in self._dict:
            self._dict[topic] = []
        self._dict[topic].append(message)
        return True

    async def send_data(self, topic, message):
        """
        Sends a message to a channel
        Args:
            topic (string): channel name to publish to
            message (object): message to send
        Returns:
            bool: True
        """
        if topic not in self._dict:
            self._dict[topic] = []
        self._dict[topic].append(message)
        return True

    async def request_message(self, topic, message, schema, timeout=1):
        """
        Sends a request to a channel and returns the response.
        Args:
            topic (string): channel name to publish to
            message (object): message to send
            timeout (int, optional): Timeout that limits how long to wait for a response. Defaults to 1.
        Returns:
            object: returns the message
        """
        message = message.encode_raw()
        return message

    async def disconnect(self, cb=None):
        """
        Disconnects from the NATS server.
        Args:
            cb (function, optional): Callback function to run after disconnecting. Defaults to None.
        Returns:
            bool: True
        """
        return True

    def create_message(self, data, schema):
        """
        Create a new message instance pre populated with the sender_ID and time known  to the nats_handler.
        Uses the data arg as value for the "data" field and validates on the provided schema. Raises an exception
        if the validation is unsuccessful.
        Args:
            data (dict): Data used to populate the "data" field of a message.
            schema (dict): Schema to validate the message
        Returns:
            Message: Message object populated with the data.
        """
        message_type = "unknown"
        if "name" in schema.keys():
            message_type = schema["name"]
        return Message.decode_json({
            "sender_ID": self.sender_id,
            "origin_ID": self.sender_id,
            "message_type": message_type,
            "time_sent": self.time_sent,
            "data": data
        }, schema)

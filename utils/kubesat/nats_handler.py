import asyncio
import json
from json import dumps, loads
import secrets
from queue import Queue
from datetime import datetime

from nats.aio.client import Client as NATS

from kubesat.message import Message
from kubesat.validation import MessageSchemas


class NatsHandler:
    """
    Handler that is the interface to a NATS server. Responsible for interacting with the server, checking whether the
    channel the user interacts with are allowed, which is specified through a config file.
    """

    def __init__(self, sender_id, host="nats", port="4222", user=None, password=None, api_host="127.0.0.1", api_port="8000", nc=NATS(), loop=asyncio.get_event_loop()):
        """
        Initializes NatsHandler.

        Args:
            connection_string (String): Host and port of the NATS server
            nc (nats.aio.client.Client, optional): NATS client object. Defaults to NATS().
            loop (asyncio.event_loop, optional): event loop used to run the callbacks. Defaults to asyncio.get_event_loop().
            filepath (str, optional): Path to the config file. Defaults to "config.json".
        """

        self._connection_string = "nats://"
        if user is not None and password is not None:
            self._connection_string += f"{user}:{password}@"
        self._connection_string += f"{host}:{port}"
        print(f"Connection String: {self._connection_string}")
        self.nc = nc
        self.loop = loop
        self.sender_id = sender_id
        self.user = user
        self.password = password
        self.host = host
        self.time_sent = ""
        self.sid_table = dict()
        self.data_table = dict()
        self.api_host = api_host
        self.api_port = str(api_port)
        self.API_DATA_ROUTE = "/data"
        self.buffer_time = 5

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
        time_sent = self.time_sent
        if not time_sent:
            time_sent = datetime.now().isoformat(timespec='milliseconds')
        if "name" in schema.keys():
            message_type = schema["name"]
        return Message.decode_json({
            "sender_ID": self.sender_id,
            "origin_ID": self.sender_id,
            "message_type": message_type,
            "time_sent": time_sent,
            "data": data
        }, schema)

    async def retrieve_data_message(self, data_id):
        """
        Creates a new message from a message stored in the data table of the NATS handler with updated time_sent.

        Args:
            data_id (string): ID of the data message used to get it from the dictionary

        Returns:
            Message: Message object populated with the data.
        """
        message = self.data_table[data_id]
        await self.delete_data_message(data_id)
        message.time_sent = self.time_sent
        message.sender_id = self.sender_id
        return message

    async def delete_data_message(self, data_id, timeout=0):
        """
        Delete a data message from the internal table.

        Args:
            data_id (string): key of the data table that refers to the message to be deleted
            timeout (int, optional): Timeout before deleting the message. Defaults to 0.

        Returns:
            bool: True
        """

        await asyncio.sleep(timeout)
        try:
            del self.data_table[data_id]
        except:
            pass
        return True

    async def subscribe_callback(self, topic, callback, orig_callback=None):
        """
        Subscribes to a topic if it is allowed and specifies a callback. The given callback should expect one
        argument representing the nats message. The message is loaded from json, so msg.data is a dictionary.

        Args:
            topic (string): topic name
            callback (function): callback function (must be async)
            orig_callback (function, optional): original callback function provided by the client used to store
                the subscription in the sid table. Defaults to None.
        Returns:
            bool: True if successfully subscribed, False otherwise
        """
        sid = await self.nc.subscribe(topic, cb=callback)
        if orig_callback:
            table_entry = (topic, orig_callback)
        else:
            table_entry = (topic, callback)
        self.sid_table[table_entry] = sid
        print(f"Subscribed to {topic}")
        return True

    async def unsubscribe_callback(self, topic, callback):
        """
        Unsubscribes callback from a topic.

        Args:
            topic (string): Topic name to unsubscribe from
            callback (function): callback function to remove
        Returns:
            bool: True if successfully unsubscribed, otherwise false
        """
        try:
            sid = self.sid_table[(topic, callback)]
        except KeyError:
            return False
        del self.sid_table[(topic, callback)]
        await self.nc.unsubscribe(sid)
        return True

    async def connect(self):
        """
        Connects to the NATS server.

        Returns:
            bool: True if successfully connected
        """

        await self.nc.connect(self._connection_string, io_loop=self.loop, connect_timeout=1, max_reconnect_attempts=1, allow_reconnect=False)
        return True

    async def send_message(self, topic, message):
        """
        Sends a message to a channel

        Args:
            topic (string): channel name to publish to
            message (object): message to send

        Returns:
            bool: True if successfully sent message, False otherwise
        """
        message.sender_id = self.sender_id
        message = message.encode_raw()
        await self.nc.publish(topic, message)
        return True

    async def send_data(self, topic, message):
        """
        Store the data attribute in the internal dictionary and assign id a unique ID. Then creates a new message
        instance that is compliant with the API_MESSAGE schema to broadcast the unique ID on the channel given, so
        that others can send get requests and access the data.

        Args:
            topic (string): channel name to publish to
            message (object): message including the data to send

        Returns:
            bool: True if successfully sent message
        """

        message.sender_id = self.sender_id
        message.time_sent = self.time_sent
        if not message.time_sent:
            message.time_sent = datetime.now().isoformat(timespec='milliseconds')

        data_id = secrets.token_urlsafe()
        self.data_table[data_id] = message
        api_message = self.create_message({
            "host": self.api_host,
            "port": self.api_port,
            "route": self.API_DATA_ROUTE,
            "data_id": data_id
        }, MessageSchemas.API_MESSAGE)

        # Not sure if really necessary to specify original id in API message as well
        api_message.origin_id = message.origin_id
        await self.send_message(topic, api_message)

        # schedule deletion of the data packet
        loop = asyncio.get_running_loop()
        loop.create_task(self.delete_data_message(
            data_id, timeout=self.buffer_time))

        return True

    async def request_message(self, topic, message, schema, timeout=1):
        """
        Sends a request to a channel and returns the response.

        Args:
            topic (string): channel name to publish to
            message (object): message to send
            schema (dict): Schema of the expected response
            timeout (int, optional): Timeout that limits how long to wait for a response. Defaults to 1.

        Returns:
            object: returns the response.
        """
        message = message.encode_raw()
        result = await self.nc.request(topic, message, timeout)
        return Message.decode_raw(result.data, schema)

    async def disconnect(self, cb=None):
        """
        Disconnects from the NATS server.

        Args:
            cb (function, optional): Callback function to run after disconnecting. Defaults to None.

        Returns:
            bool: True if successfully disconnected.
        """

        await self.nc.close()
        if cb is not None:
            await cb()
        return True

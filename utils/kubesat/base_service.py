import json
import socket
import asyncio
import aiohttp
import uvicorn
import traceback
import subprocess
from functools import wraps
from aiologger.loggers.json import JsonLogger
from fastapi import FastAPI, Request, HTTPException
from typing import Callable

from kubesat.message import Message
from kubesat.nats_handler import NatsHandler
from kubesat.redis_handler import RedisHandler
from kubesat.nats_logger import NatsLoggerFactory
from kubesat.validation import validate_json, MessageSchemas


class BaseService():
    """
    Class that provides functionality for registering callbacks on different NATS channels. It is responsible for connecting
    with NATS, Redis, loading configs, and running the python asyncio event loop. This combines NATS and a FastAPI application
    and runs them in the same event loop, so that extending with more REST endpoints is possible in the future. Currently,
    the REST API is just used for a special callbacks that are meant to send data too large to be transmitted over NATS.
    """

    def __init__(self, service_type: str, schema: dict, config_path: str = None):
        """
        Initializes the base service. It subscribes a subject "node.status.{SERVICE_TYPE}.{SENDER_ID}" and provides a request
        response endpoint that can be pinged to see if the service is alive.

        Args:
            service_type (string): Name of the service type for this instance
            schema (dict): Schema used to validate the shared_storage internal to this instance.
            config_path (string, optional): Path to a config file. If not None, will be used to get the
            sender_id and initial shared storage of this instance once the BaseService.run method is called.
        """

        super().__init__()
        # initializing nats

        self.service_type = service_type
        self._schema = schema
        self.config_path = config_path
        self.sender_id = None
        self.nats_client = None
        self.redis_client = None
        self._api = None
        self._logger = None
        self.shared_storage = None
        self._startup_callback = None
        self._registered_callbacks = []
        self._unsubscribe_nats_routes = []

        # subscribing to node status by default to provide channel to ping and see whether service is alive
        @self.request_nats_callback(f"node.status.{self.service_type}.", MessageSchemas.STATUS_MESSAGE, append_sender_id=True)
        async def heartbeat(message: Message, nats_handler: NatsHandler, shared_storage: dict, logger: JsonLogger) -> Message:
            return nats_handler.create_message("ALIVE", MessageSchemas.STATUS_MESSAGE)

    async def _register_callbacks(self):
        """
        Private method that activates all the NATS channel subscriptions.
        """

        for route in self._registered_callbacks:
            await route()

    async def _stop(self):
        """
        Stops the service by unsubscribing the callbacks and disconnecting from the NATS server.
        """

        for unsubscribe_route in self._unsubscribe_nats_routes:
            await unsubscribe_route()
        await self.nats_client.disconnect()

    def startup_callback(self, callback_function: Callable) -> Callable:
        """
        Decorator used to register a callback that will be called at service startup in the BaseService.run() method.
        The callback will be called with arguments nats_handler, shared_storage, logger (in that order).
        There can only be one startup callback registered, so but subsequent calls will just overwrite the
        previously set callback. Usage example:

        @base_service_instance.startup_callback
        async def sample_callback(nats_handler, shared_storage, logger):
            print("I am the startup callback")

        Args:
            callback_function (function): Async callback function that should be executed.

        Returns:
            function: The original function that was passed as argument
        """
        self._startup_callback = callback_function
        return callback_function

    def subscribe_nats_callback(self, channel: str, message_schema: dict) -> Callable:
        """
        Decorator used to register a callback for a specific NATS channel. The actual registration of
        the callback with the NATS server happens when BaseService.run() is called. Will call the callback
        with arguments message, nats_handler, shared_storage, logger (in that order). Usage example:

        @base_service_instance.subscribe_nats_callback("sample.route", MessageSchema)
        async def sample_callback(msg, nats, shared_storage, logger):
            print(msg.data)

        Args:
            channel (string): Name of the channel that the callback should be registered with.
            message_schema (dict): Schema to validate incoming messages against

        Returns:
            function: Returns decorator function that takes in the actual callback.
        """

        def decorator(callback_function: Callable) -> Callable:

            # wrap the callback so we can actually subscribe once the service runs
            async def subscription_wrapper():

                async def callback_wrapper(msg):

                    # try executing the callback and log if exception occurs
                    try:
                        # decode message
                        msg = Message.decode_raw(msg.data, message_schema)

                        # temporarily copy shared storage, so callback cannot perform invalid changes
                        shared_storage = self.shared_storage.copy()

                        # execute callback
                        await callback_function(msg, self.nats_client, shared_storage, self._logger)

                        # check whether the shared storage is still valid and set it if that is the case
                        if not validate_json(shared_storage, self._schema):
                            raise ValueError(
                                "Invalid change in shared storage")
                        self.shared_storage = shared_storage

                        # buffer the current shared storage in redis
                        self.redis_client.set_shared_storage(
                            self.shared_storage)
                    except Exception as e:
                        await self._logger.error(traceback.format_exc())

                # subscribe to the NATS channel
                await self.nats_client.subscribe_callback(channel, callback_wrapper, orig_callback=callback_function)

            self._registered_callbacks.append(subscription_wrapper)

            # create a wrapper so we can unsubscribe at a later time
            async def unsubscription_wrapper():
                return await self.nats_client.unsubscribe_callback(channel, callback_function)
            self._unsubscribe_nats_routes.append(unsubscription_wrapper)
            return callback_function
        return decorator

    def request_nats_callback(self, channel: str, message_schema: dict, append_sender_id: bool = True) -> Callable:
        """
        Decorator used to register a request callback for a specific NATS channel. This means that any
        callback registered using this decorator is expected to return an object of type Message which will
        be sent back via NATS to the sender. That implies that messages sent to the registered channel must
        be sent using NatsHandler.request_message. The actual registration of the callback with the NATS server
        happens when BaseService.run() is called. If append_sender_id is True, the sender_id of the service
        object will be appended to the channel name. Will call the callback with arguments message, nats_handler,
        shared_storage, logger (in that order). Usage example:

        @base_service_instance.request_nats_callback("sample-route", MessageSchema, append_sender_id=True)
        async def sample_callback(msg, nats, shared_storage, logger):
            print(msg.data)

        Args:
            channel (string): Name of the channel that the callback should be registered with.
            message_schema (dict): Schema to validate incoming messages against
            append_sender_id (bool): Indicates whether the sender_id should be appended to the channel name
                at service runtime.


        Returns:
            function: Returns decorator function that takes in the actual callback.
        """

        def decorator(callback_function: Callable) -> Callable:

            # wrap the callback so we can actually subscribe once the service runs
            async def request_wrapper() -> Callable:

                async def callback_wrapper(msg):

                    # try executing the callback and log if exception occurs
                    try:
                        # decode message and copy raw message to preserve the response channel name
                        raw_message = msg
                        msg = Message.decode_raw(msg.data, message_schema)

                        # temporarily copy shared storage, so callback cannot perform invalid changes

                        shared_storage = self.shared_storage.copy()

                        # execute callback
                        response = await callback_function(msg, self.nats_client, shared_storage, self._logger)

                        # check whether the shared storage is still valid and set it if that is the case
                        if not validate_json(shared_storage, self._schema):
                            raise ValueError(
                                "Invalid change in shared storage")
                        self.shared_storage = shared_storage

                        # buffer the current shared storage in redis
                        self.redis_client.set_shared_storage(
                            self.shared_storage)

                        # send the response via NATS
                        await self.nats_client.send_message(raw_message.reply, response)
                    except Exception as e:
                        await self._logger.error(traceback.format_exc())

                # if specified, appending sender_id to channel name
                sub_channel = channel
                if append_sender_id:
                    sub_channel += self.sender_id

                # subscribe to the NATS channel
                await self.nats_client.subscribe_callback(sub_channel, callback_wrapper, orig_callback=callback_function)

            self._registered_callbacks.append(request_wrapper)

            # create a wrapper so we can unsubscribe at a later time
            async def unsubscription_wrapper():
                return await self.nats_client.unsubscribe_callback(channel, callback_function)
            self._unsubscribe_nats_routes.append(unsubscription_wrapper)
            return callback_function
        return decorator

    def schedule_callback(self, timeout: float) -> Callable:
        """
        Decorator used to register a callback to be executed in a regular time interval. The actual registration of
        the callback happens when BaseService.run() is called, so the callback will not be active before then.
        Will call the callback with arguments nats_handler, shared_storage, logger (in that order). Usage example:


        @base_service_instance.schedule_callback(1)
        async def sample_callback(nats, shared_storage, logger):
            print("hi"!)

        Args:
            timeout (float): Timeout to wait until running the callback again.

        Returns: Returns decorator function that takes in the actual callback.

        """

        def decorator(callback_function: Callable) -> Callable:

            # wrap the callback so we can actually subscribe once the service runs
            async def subscription_wrapper():

                async def callback_wrapper():

                    # try executing the callback and log if exception occurs
                    try:
                        while True:

                            # temporarily copy shared storage, so callback cannot perform invalid changes
                            shared_storage = self.shared_storage.copy()

                            # execute callback
                            await callback_function(self.nats_client, shared_storage, self._logger)

                            # check whether the shared storage is still valid and set it if that is the case
                            if not validate_json(self.shared_storage, self._schema):
                                self._schema = self.shared_storage
                            self.shared_storage = shared_storage

                            # buffer the current shared storage in redis
                            self.redis_client.set_shared_storage(
                                self.shared_storage)

                            # timeout until next loop execution
                            await asyncio.sleep(timeout)
                    except Exception as e:
                        await self._logger.error(traceback.format_exc())

                # append the task to the event loop
                loop = asyncio.get_running_loop()
                loop.create_task(callback_wrapper())

            # add the wrapper to the nats_routes list so calling it
            self._registered_callbacks.append(subscription_wrapper)
            return callback_function
        return decorator

    def subscribe_data_callback(self, channel, message_schema, validator=None):
        """
        Decorator used to register a callback for a specific NATS channel that is used to send data via the REST API. Any broadcasting
        on channels attached to this callback should be done with NatsHandler.send_data(). Internall this callbacks expects messages
        of schema API_MESSAGE on the registered channel. It then extracts the host, port, and route for for the GET endpoint to get
        the data, makes an HTTP request and parses the response into a Message object of schema message_schema. The actual registration
        of the callback with the NATS server happens when BaseService.run() is called. Will call the callback
        with arguments message, nats_handler, shared_storage, logger (in that order). Optionally, you can provide a validator as a
        keyword argument, which should have the same function signature of a callback function and should return True or False depending
        on whether the message coming from the REST API should be processed. Usage example:

        @base_service_instance.subscribe_data_callback("sample.route", MessageSchema, validator=some_validator_function)
        async def sample_callback(msg, nats, shared_storage, logger):
            print(msg.data)

        Args:
            channel (string): Name of the channel that the callback should be registered with.
            message_schema (dict): Schema to validate the incoming API messages against.
            validator (function, optional): function to check whether a certain NATS API message should be processed. Must have args message,
                nats_handler, shared_storage, logger (in that order) and return True or False.
        """

        def decorator(callback_function):

            # subscribe to the given NATS channel but listen for messages of schema API_MESSAGE
            @self.subscribe_nats_callback(channel, MessageSchemas.API_MESSAGE)
            async def handle_api_message(message, nats, shared_storage, logger):

                # if a validator function was given, call it to determine whether the message should be processed
                if not validator or validator(message, nats, shared_storage, logger):
                    async with aiohttp.ClientSession() as session:

                        # construct the URL to access the data using the info from the API message
                        url = f"http://{message.data['host']}:{message.data['port']}{message.data['route']}/{message.data['data_id']}"
                        async with session.get(url) as response:

                            # check whether GET was successful
                            if response.status == 200:

                                # decode the message and execute the callback
                                msg = Message.decode_json(await response.json(), message_schema)
                                await callback_function(msg, self.nats_client, self.shared_storage, self._logger)
                                return
                            await self._logger.error(json.dumps(await response.json()))
            return callback_function
        return decorator

    async def _load_config(self):
        """
        attempt to fetch a configuration json
        containing the sender_id and initial shared_storage from a file, if that fails attempts to get it from redis.
        """
        if self.config_path is not None:

            # if a path to a config file is given, initializes from there
            with open(self.config_path, "r") as f:
                config = json.load(f)

            # get own sender_id from config
            self.sender_id = config["sender_id"]

            # validate the shared_storage section of the config
            validate_json(config["shared_storage"], self._schema)
            self.shared_storage = config["shared_storage"]

            # write the shared storage and sender ID to Redis
            self.redis_client.set_shared_storage(self.shared_storage)
            self.redis_client.set_sender_id(self.sender_id)
            print(
                f"Successfully initialized {self.sender_id} {self.service_type} from file")
        else:
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
                    # try initializing from redis
                    self.sender_id = self.redis_client.get_sender_id()
                    if not self.sender_id:
                        raise ValueError(
                            "Could not get sender id from redis")
                    self.shared_storage = self.redis_client.get_shared_storage()
                    print(
                        f"Successfully initialized {self.sender_id} {self.service_type} from redis")
                except Exception as e:
                    raise ValueError(
                        f"Failed to initialize from redis. Aborting. Error: {e}")

    def run(self, nats_host="nats", nats_port="4222", nats_user=None, nats_password=None, api_host="127.0.0.1", api_port=8000, redis_host="redis", redis_port=6379, redis_password=None):
        """
        Main entrypoint to starting the service. Will register all the callbacks with NATS and REST and start the event loop. Will first attempt to fetch a configuration json
        containing the sender_id and initial shared_storage from a file, if that fails attempts to get it from redis.

        Args:
            nats_host (str, optional): NATS server host. Defaults to "nats".
            nats_port (str, optional): NATS server port. Defaults to "4222".
            nats_user (str, optional): NATS user. Defaults to None.
            nats_password (str, optional): NATS password. Defaults to None.
            api_host (str, optional): Host under which the own REST API is accesible. Defaults to "127.0.0.1".
            api_port (int, optional): Port to run the REST API on. Defaults to 8000.
            redis_host (str, optional): Redis server host. Defaults to "redis".
            redis_port (int, optional): Redis server port. Defaults to 6379.
            redis_password (str, optional): Redis server password. Defaults to None.
        """

        self.nats_host = nats_host
        self.nats_port = nats_port
        self.nats_user = nats_user
        self.nats_password = nats_password
        self.api_host = api_host
        self.api_port = api_port
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_password = redis_password

        # creating redis client
        self.redis_client = RedisHandler(
            self.service_type, self._schema, host=self.redis_host, port=self.redis_port, password=self.redis_password)

        # creating api
        self._api = FastAPI()

        # registering the data REST endpoint used to query data messages
        @self._api.get("/data/{data_id}")
        async def get_data(data_id: str):
            try:
                # retrieve the data from the NATS client buffer and return it
                message = await self.nats_client.retrieve_data_message(data_id)
                message.sender_id = self.nats_client.sender_id
                return message.encode_json()
            except Exception as e:
                print("Error!")
                await self._logger.error(traceback.format_exc())
                raise HTTPException(
                    status_code=500,
                    detail="An error occured"
                )

        # Since our initialization consists of async functions, registers it as a startup callback that executes
        # once the event loop starts
        @self._api.on_event("startup")
        async def run():

            # set the execption handler to None. This makes exception actually stop code execution instead of going unnoticed
            loop = asyncio.get_running_loop()
            loop.set_exception_handler(None)

            # connect to the NATS server
            self.nats_client = NatsHandler("default", host=self.nats_host, port=self.nats_port, user=self.nats_user,
                                           password=self.nats_password, api_host=self.api_host, api_port=self.api_port, loop=asyncio.get_running_loop())
            await self.nats_client.connect()

            # creating logger
            self._logger = NatsLoggerFactory.get_logger(
                self.nats_client, self.service_type)

            # retrieving initial shared_storage
            await self._load_config()

            # setting nats sender id
            self.nats_client.sender_id = self.sender_id

            # registering callbacks
            await self._register_callbacks()

            # execute startup callback
            if self._startup_callback:
                await self._startup_callback(self.nats_client, self.shared_storage, self._logger)

        # registering the nats shutdown with the api server
        @self._api.on_event("shutdown")
        async def stop():
            await self._stop()

        # run application
        uvicorn.run(self._api, host="0.0.0.0", port=self.api_port,
                    debug=False, log_level='error')

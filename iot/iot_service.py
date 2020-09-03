import math
import asyncio
from datetime import datetime
from kubesat.base_simulation import BaseSimulation
from kubesat.services import ServiceTypes
from kubesat.validation import MessageSchemas, SharedStorageSchemas

#Note: Data is randomly generated for IOT sensors currently--can easily route in true data or data from a model

simulation = BaseSimulation(ServiceTypes.Iot, SharedStorageSchemas.IOT_SERVICE_STORAGE)

@simulation.subscribe_nats_callback("simulation.timestep", MessageSchemas.TIMESTEP_MESSAGE)
async def send_data(message, nats_handler, shared_storage, logger):
    """
    Calulate the current values for this IoT sensor and broadcast them.

    Args:
        message (Message): incoming message with the current time
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc,

    Returns:
        None
    """
    time = message.data["time"]
    for i in range(shared_storage["data_rate"]):
        time_struct= datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f").timetuple()
        x = time_struct.tm_mon + time_struct.tm_mday/30 + time_struct.tm_hour/720 + time_struct.tm_min/43200 + time_struct.tm_sec/2592000
        data_value = 4.2*math.sin((270000*(x + 1))*3.14/6) + 13.7
        message = nats_handler.create_message(data_value, MessageSchemas.IOT_DATA_MESSAGE)
        message.message_type = "temperature"
        await nats_handler.send_data("data.out", message)
        await asyncio.sleep(0.5/shared_storage["data_rate"])

@simulation.subscribe_nats_callback("simulation.timestep", MessageSchemas.TIMESTEP_MESSAGE)
async def soil_water_content(message, nats_handler, shared_storage, logger):
    """
    Calulate the current soil water content (in %) values for this IoT sensor and broadcast them.

    Args:
        message (Message): incoming message with the current time
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc,

    Returns:
        None
    """

    time = message.data["time"]
    for i in range(shared_storage["data_rate"]):
        time_struct = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f").timetuple()
        total_seconds = time_struct.tm_hour*3600 + time_struct.tm_min*60 + time_struct.tm_sec
        data_value = 10 * math.cos(2 * math.pi * total_seconds * (1 / 86400)) + 40
        message = nats_handler.create_message(data_value, MessageSchemas.IOT_DATA_MESSAGE)
        message.message_type = "soil_water_content"
        await nats_handler.send_data("data.out", message)
        await asyncio.sleep(0.5/shared_storage["data_rate"])

@simulation.subscribe_nats_callback("simulation.timestep", MessageSchemas.TIMESTEP_MESSAGE)
async def fertilization_level(message, nats_handler, shared_storage, logger):
    """
    Calulate the current values fertilization level (between 0 and 1) for this IoT sensor and broadcast them.

    Args:
        message (Message): incoming message with the current time
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc,

    Returns:
        None
    """

    time = message.data["time"]
    for i in range(shared_storage["data_rate"]):
        time_struct = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f")
        total_seconds = (time_struct-datetime(1970,1,1)).total_seconds()
        seconds_in_week = total_seconds % (60 * 60 * 24 * 7)
        data_value = 0.25 * math.sin(2 * math.pi * seconds_in_week * (1/604800)) + 0.25
        message = nats_handler.create_message(data_value, MessageSchemas.IOT_DATA_MESSAGE)
        message.message_type = "fertilization"
        await nats_handler.send_data("data.out", message)
        await asyncio.sleep(0.5/shared_storage["data_rate"])

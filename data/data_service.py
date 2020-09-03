import math
import asyncio
from queue import Queue
from datetime import datetime
from kubesat.base_simulation import BaseSimulation
from kubesat.services import ServiceTypes
from kubesat.validation import MessageSchemas, SharedStorageSchemas
from kubesat.validation import check_pointing_and_mode, check_internal, check_internal_data, check_pointing

simulation = BaseSimulation(ServiceTypes.Data, SharedStorageSchemas.DATA_SERVICE_STORAGE)
buffer = Queue()

@simulation.subscribe_data_callback("data.out", MessageSchemas.IOT_DATA_MESSAGE, validator=check_pointing_and_mode)
async def receive_packet(message, nats_handler, shared_storage, logger):
    """
    Receives a data packet and then forwards it to the internal satellite services (such as agriculture). Sends a logger message to signify it has received data.
    Args:
        message (Message): incoming message with the ID of the sending Satellite
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc,

    Returns:
        None
    """
    await nats_handler.send_data("internal.data.in", message)
    if logger:
        await logger.info(f"Sat got {message.message_type} data {message.data}")

@simulation.subscribe_data_callback("internal.data.out", MessageSchemas.IOT_DATA_MESSAGE, validator=check_internal_data)
async def buffer_packet(message, nats_handler, shared_storage, logger):
    """
    Receives a data packet from an internal service (such as agriculture) then puts it in the outgoing message buffer.

    Args:
        message (Message): outgoing data message
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc,

    Returns:
        None
    """

    buffer.put(message)
    message = nats_handler.create_message(buffer.qsize(), MessageSchemas.BUFFER_MESSAGE)
    await nats_handler.send_message("internal.buffer_size", message)

# later on, maybe subscribe this to a different channel that communicates where a satellite is actually pointing instead of the command
@simulation.subscribe_nats_callback("state", MessageSchemas.STATE_MESSAGE)
async def update_pointing_list(message, nats_handler, shared_storage, logger):
    """
    Updates the list of other satellites pointing at itself in order to determine whether they can communicate or not.

    Args:
        message (Message): incoming message with current pointing target of the sender
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc,

    Returns:
        None
    """
    if not nats_handler.sender_id in message.data["state"].keys():
        if message.origin_id in message.data["state"].keys():
            target = message.data["state"][message.origin_id]["orbit"]["attitude"]
            visible = message.data["state"][message.origin_id]["target_in_view"]
            if message.origin_id in shared_storage["pointing"] and (target != nats_handler.sender_id or not visible):
                shared_storage["pointing"].remove(message.origin_id)
            elif (message.origin_id not in shared_storage["pointing"] and target == nats_handler.sender_id) and visible:
                shared_storage["pointing"].append(message.origin_id)
    else:
        target = message.data["state"][list(message.data["state"].keys())[0]]["orbit"]["attitude"]
        visible = message.data["state"][list(message.data["state"].keys())[0]]["target_in_view"]
        if visible:
            shared_storage["pointing_to"] = target
        else:
            shared_storage["pointing_to"] = "nadir_tracking"
        shared_storage["mode"] = message.data["state"][list(message.data["state"].keys())[0]]["mode"]

@simulation.subscribe_nats_callback("simulation.timestep", MessageSchemas.TIMESTEP_MESSAGE)
async def send_data(message, nats_handler, shared_storage, logger):
    """
    Sends data from the outgoing message buffer as well as calculating battery data (and possibly other telemetry data in the future) and putting that in the message buffer and sending it.
    Args:
        message (Message): incoming message with the current time
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc,

    Returns:
        None
    """
    while shared_storage["pointing_to"] in shared_storage["pointing"] and shared_storage["mode"] == "sending" and not buffer.empty():
        await nats_handler.send_data("data.out", buffer.get())
        await asyncio.sleep(shared_storage["timestep"] * 0.5 / shared_storage["data_rate"])
        print(f"Sent packet while {shared_storage['pointing_to']} and {shared_storage['pointing']} and {shared_storage['mode']}")
    print(f"{nats_handler.sender_id}: Buffer size {buffer.qsize()}")
    time_struct = datetime.strptime(nats_handler.time_sent, "%Y-%m-%dT%H:%M:%S.%f").timetuple()
    seconds_in_hour = time_struct.tm_min*60 + time_struct.tm_sec
    data_value = 50 * -math.cos(2 * math.pi * seconds_in_hour * (1 / 3600)) + 50
    message = nats_handler.create_message(data_value, MessageSchemas.IOT_DATA_MESSAGE)
    message.message_type = "battery_percentage"
    await nats_handler.send_data("data.out", message)

    message = nats_handler.create_message(buffer.qsize(), MessageSchemas.BUFFER_MESSAGE)
    await nats_handler.send_message("internal.buffer_size", message)

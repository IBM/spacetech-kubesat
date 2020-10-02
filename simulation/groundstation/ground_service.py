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

from kubesat.base_simulation import BaseSimulation
from kubesat.services import ServiceTypes
from kubesat.validation import MessageSchemas, check_pointing_data, SharedStorageSchemas

simulation = BaseSimulation(ServiceTypes.Groundstation, SharedStorageSchemas.GROUND_STATION_SERVICE_STORAGE)

@simulation.subscribe_data_callback("data.out", MessageSchemas.IOT_DATA_MESSAGE, validator=check_pointing_data)
async def receive_data(message, nats_handler, shared_storage, logger):
    """
    Receives a data packet, updates the number of received packets, and requests more.

    Args:
        message (Message): incoming message with current pointing target of the sender
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc,

    Returns:
        None
    """

    shared_storage["packets_received"] += 1
    if logger:
        await logger.info(f"Ground got {message.message_type} data {message.data} from {message.origin_id}")
    buffer_message = nats_handler.create_message(1, MessageSchemas.BUFFER_MESSAGE)
    await nats_handler.send_message("groundstation.packets_received", buffer_message)
    if message.message_type == "battery_percentage":
        await nats_handler.send_message("received.battery_percentage", message)
    elif message.message_type == "temperature":
        await nats_handler.send_message("received.temperature", message)
    elif message.message_type == "soil_water_content":
        await nats_handler.send_message("received.soil_water_content", message)
    elif message.message_type == "fertilization":
        await nats_handler.send_message("received.fertilization", message)
    else:
        if logger:
            await logger.info(f"Ground got unknown message type {message.message_type}")

# later on, maybe subscribe this to a different channel that communicates where a satellite is actually pointing instead of the command
@simulation.subscribe_nats_callback("state", MessageSchemas.STATE_MESSAGE)
async def update_pointing_list(message, nats_handler, shared_storage, logger):
    """
    Updates the internal list of satellites currently pointing at this groundstation

    Args:
        message (Message): incoming message with current pointing target of the sender
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc,

    Returns:
        None
    """

    if message.origin_id in message.data["state"].keys():
        target = message.data["state"][message.origin_id]["orbit"]["attitude"]
        visible = message.data["state"][message.origin_id]["target_in_view"]
        if message.origin_id in shared_storage["pointing"] and (target != nats_handler.sender_id or not visible):
            shared_storage["pointing"].remove(message.origin_id)
        elif message.origin_id not in shared_storage["pointing"] and target == nats_handler.sender_id and visible:
            shared_storage["pointing"].append(message.origin_id)

@simulation.subscribe_nats_callback("internal.phonebook", MessageSchemas.PHONEBOOK_MESSAGE)
async def update_cluster(message, nats_handler, shared_storage, logger):
    """
    Checks the phonebook and sends a clustering command if two satellites are in range

    Args:
        message (Message): incoming message with the current phonebook of a satellite
        nats_handler (NatsHandler): NatsHandler use to interact with nats
        shared_storage (dict): Dictionary to persis memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc
    Returns:
        None
    """
    phonebook = message.data
    cubesat_id = message.origin_id
    ip_cluster_message = {
                            "recipient": cubesat_id,
                            "ip_map": []
                        }
    if message.origin_id not in shared_storage["ip_map"]:
        return
    for sat in phonebook:
        if (sat != cubesat_id) and (phonebook[sat]) and (sat not in shared_storage["ip_cluster_map"][cubesat_id]) and (sat in shared_storage["ip_map"]):
            # replace 'sat' in line 87 and  88 with 'shared_storage["ip_map"][sat]'
            ip_cluster_message["ip_map"].append(sat)
            shared_storage["ip_cluster_map"][cubesat_id].append(sat)
    if ip_cluster_message["ip_map"]:
        message = nats_handler.create_message(ip_cluster_message, MessageSchemas.CLUSTER_MESSAGE)
        await nats_handler.send_message("command.cluster", message)


@simulation.subscribe_nats_callback("cluster.ip", MessageSchemas.IP_ADDRESS_MESSAGE)
async def update_sat_ip(message, nats_handler, shared_storage, logger):
    """
    Receives and stores the ip address of a satellite in shared_storage

    Args:
        message (Message): incoming message with ip address of a satellite
        nats_handler (NatsHandler): NatsHandler use to interact with nats
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc
    """
    ip_address = message.data
    cubesat_id = message.origin_id
    shared_storage["ip_map"][cubesat_id] = ip_address
    if cubesat_id not in shared_storage["ip_cluster_map"]:
        await logger.info(f"Updating in update_sat_ip {cubesat_id}")
        shared_storage["ip_cluster_map"][cubesat_id] = []


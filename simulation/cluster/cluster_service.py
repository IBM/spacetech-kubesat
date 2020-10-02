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

import socket
from kubesat.message import Message
from kubesat.base_simulation import BaseSimulation
from kubesat.services import ServiceTypes
from kubesat.validation import MessageSchemas, SharedStorageSchemas

simulation = BaseSimulation("cluster", SharedStorageSchemas.CLUSTER_SERVICE_STORAGE)

@simulation.subscribe_nats_callback("simulation.timestep", MessageSchemas.TIMESTEP_MESSAGE)
async def send_ip_address(message, nats_handler, shared_storage, logger):
    """
    Broadcasts the nats host on each time step which will be read by the ground station

    Args:
        message (Message): incoming message with the timestep
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc,
    """
    hostname = nats_handler.api_host
    ip_message = nats_handler.create_message(hostname, MessageSchemas.IP_ADDRESS_MESSAGE)
    await nats_handler.send_message("cluster.ip", ip_message)

@simulation.subscribe_nats_callback("command.cluster", MessageSchemas.CLUSTER_MESSAGE)
async def cluster(message, nats_handler, shared_storage, logger):
    """
    Receives command from groundstation to cluster with other satellites and runs the
    bash script/edits config map so that clusters satellites


    Args:
        message (Message): incoming message with the ip address/host names of other sats
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc,
    """
    if message.data["recipient"] == nats_handler.sender_id:
        # This is where the controller needs to be used to cluster the satellites
        # 'm'essage.data["ip_map"]' is a list of the api host the satellite can cluster with
        await logger.info(f'{nats_handler.sender_id} is clustering with {message.data["ip_map"]}')
        print(f"{nats_handler.sender_id} is clustering with {message.data['ip_map']}")
        pass
	    

                    

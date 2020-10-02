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

from datetime import datetime, timedelta
from kubesat.message import Message
from kubesat.services import ServiceTypes
from kubesat.base_simulation import BaseSimulation
from kubesat.validation import MessageSchemas, SharedStorageSchemas

simulation = BaseSimulation(ServiceTypes.Clock, SharedStorageSchemas.CLOCK_SERVICE_STORAGE)

@simulation.schedule_callback(0.4)
async def send_timestep(nats, shared_storage, logger):
    """
    Broadcast the current time of the simulation and updates it by the timestep interval defined in the config.

    Args:
        nats (NatsHandler): connection to nats used to send and receive messages
        shared_storage (dict): dictionary that stores local data for the service
        logger (NatsLogger): logger that can be used to communicate the state of the system
    """
    time = shared_storage["start_time"]

    message = nats.create_message({
            "time": time
        }, MessageSchemas.TIMESTEP_MESSAGE)

    await nats.send_message("simulation.timestep", message)
    shared_storage["start_time"] = (datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f") + timedelta(seconds=shared_storage["time_step"])).strftime("%Y-%m-%dT%H:%M:%S.%f")
    print(f"Sent timestep {time}")

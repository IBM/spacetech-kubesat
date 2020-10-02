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
from kubesat.validation import MessageSchemas, SharedStorageSchemas, check_internal_data

simulation = BaseSimulation("agriculture", SharedStorageSchemas.APPLICATION_SERVICE_STORAGE)

@simulation.subscribe_data_callback("internal.data.in", MessageSchemas.IOT_DATA_MESSAGE, validator=check_internal_data)
async def process_data(message, nats_handler, shared_storage, logger):
    """
    Receives IOT data packets from the data service, processes them (currently not doing any processing), and then sends processed data back to the data service.

    Args:
        message (Message): incoming message with data to be forwarded
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc,

    Returns:
        None
    """
    await nats_handler.send_data("internal.data.out", message)

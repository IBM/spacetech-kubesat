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

"""
Available service list is in 'services' configmap in 'kube-system' namespace. If you don't have the 
services configmap, create a new one. The following is an example:
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: services
  namespace: kube-system
data:
  hello-world: "hello-world:latest"
---
"""

import asyncio
import time

from kubesat.validation import MessageSchemas, SharedStorageSchemas
from kubesat.base_service import BaseService

SERVICE_TYPE = 'manager'
manager = BaseService(
    SERVICE_TYPE, SharedStorageSchemas.STORAGE, './service.json')


@manager.schedule_callback(2)
# Broadcast service availability check request every two seconds.
async def send_availabilty_check_request(nats, shared_storage, logger):
    """
    Send availabiltiy check request
    """
    message = nats.create_message({
        "type": "request",
        "function": "is_available",
        "parameters": {
            "service": "hello-world"
        }
    }, MessageSchemas.MESSAGE)

    # Send the message to resource subject
    await nats.send_message("resource", message)
    print(f"check service availability: {message.encode_json()}")


@manager.subscribe_nats_callback("resource",  MessageSchemas.MESSAGE)
# Subscribe resource subject
async def handle_resource_request(message, nats, shared_storage, logger, kubernetes_handler):
    message_json = message.encode_json()['data']
    if message_json["type"] == 'request':
        if message_json['function'] == 'is_available':
            service = message_json['parameters']['service']
            # Check the status of kubernetes resources
            availability = kubernetes_handler.get_availability(service)
            message_json["type"] = "response"
            message_json["result"] = str(availability)
            reply_message = nats.create_message(
                message_json, MessageSchemas.MESSAGE)
            await nats.send_message("resource", reply_message)
    else:
        print("Got a result message." + str(message_json))


@manager.startup_callback
# Invoke the startup function at the start time
async def startup(nats_handler, shared_storage, logger):
    print(f"{SERVICE_TYPE} in {manager.sender_id} has started.")

if __name__ == '__main__':
    """
    Start the manager service
    If the service is in a kubernetes cluster, it uses kubernetes service account provided by the cluster
    If OS environment has KUBECONFIG, the service uses it to initialize the kubernetes handler
    If there is a kubernetes client configuration file, refer to the following example:
    manager.run(kubernetes_config_file="[PATH_OF_KUBERNETES_CLIENT_CONFIGURATION_FILE")
    """
    manager.run()

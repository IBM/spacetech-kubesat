# Manage Kuberntes Resources

KubeSat package provides functions to manage Kubernees resources. In this example, users will create an application that sends and receives messages via NATs and query Kubernetes APIs. 

Refer to [Getting Started](getting-started.md) and install the KubeSat package and spin up NATs and Redis.

## Kubernetes cluster configuration

Prepare a target Kubernetes cluster and log into the cluster using a kubectl command. 
To access the Kubernetes API from outside, it is necessary to have a kubeconfig file. The following command exports the kubeconfig file and saves it as a filename `kubeconfig.yaml`

```sh
 kubectl config view --raw > kubeconfig.yaml
```

Available service list is stored as a ConfigMap. The following example contains a hello-world service with the container image `hello-world:latest`. Create `services.yaml` file with the following: 

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: services
  namespace: kube-system
data:
  hello-world: "hello-world:latest"
```

Apply it to Kuberntes.

```
kubectl apply -f services.yaml
```


## Create a manager service
 
The following application invokes `kubernetes_handler.get_availability` and check if it can deploy `hello-world` job. Create `manager_service.py` file with the following:

```python
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
    manager.run()

```

The service requires configuration file to get a sender ID. Create `service.json` file in the same directory with `manager_service.py`. 

```json
{
    "sender_id": "node_01",
    "shared_storage": {}
}
```

Start the application. 

```sh
python manager_service.py
```
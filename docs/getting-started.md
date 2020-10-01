# Getting Started

KubeSat pacakge requires NATs server, Redis server, and python libraries. 

## Install KubeSat package

Clone a Github repository and move to the directory.

```sh
git clone https://github.com/IBM/spacetech-kubesat.git
cd spacetech-kubesat
```

The KubeSat package has been developed and tested on Python 3.8. Install [conda](https://docs.conda.io/en/latest/) and create a new virtual environment for keeping dependencies separate from your system Python installation, as an example

```sh
conda env create -n kubesat -f conda-env.yaml
```

Activate the environment.

```
conda activate kubesat
```

Install the KubeSat package. 
```python
python setup.py install
```

## Environment setup

KubeSat package requires NATs server and Redis server. You can install and start them on your local system. If docker is installed and running, you can use the following commands:

Start NATs server.

```sh
docker run --rm --name nats-server -p 4222:4222 nats
```

Start Redis server.

```
docker run --rm --name redis-server -p 6379:6379 redis
```

## Create a hello service

Create a `hello_service.py` python file with the following code. This application sends and receives `hello` messages using NATs. A `send_hello_message` function sends a `hello` message every two seconds to a `public.hello` subject. A `receive_hello_message` funcion is triggered when a new message comes on the `public.hello` topic.  

```python
import asyncio
import time

from kubesat.base_service import BaseService

SERVICE_TYPE = 'hello'
hello = BaseService(service_type=SERVICE_TYPE,
                    config_path='./service.json')


@hello.schedule_callback(2)
# Send a hello message every two seconds.
async def send_hello_message(nats, shared_storage, logger):
    message = nats.create_message({"message": "hello"})

    # Send a hello message to public.hello subject
    await nats.send_message("public.hello", message)
    print(f"SEND : {message.encode_json()}")


@hello.subscribe_nats_callback("public.hello")
# Subscribe public.hello subject
async def receive_hello_message(message, nats, shared_storage, logger):
    message_json = message.encode_json()
    print(f"RECEIVED : {message_json}")
    shared_storage["last_sent"] = message_json['time_sent']


@hello.startup_callback
# Invoke the startup function at the start time
async def startup(nats_handler, shared_storage, logger):
    print(f"{SERVICE_TYPE} in {hello.sender_id} has started.")

if __name__ == '__main__':
    # Start the hello service
    hello.run()
```

The service requires configuration file to get a sender ID. Create `service.json` file in the same directory with `hello_service.py`. 

```json
{
    "sender_id": "node_01",
    "shared_storage": {}
}
```

Start the application. 

```sh
python hello_service.py
```

Congratulations! You successfully complete KubeSat application development. You can continue the next example in [Manage Kuberntes Resources](manage-kubernetes-resources.md).  
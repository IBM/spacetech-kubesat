# Template for Generic Service Repository

Follow this template to create a new service for the simulation, whether a new use-case or more advanced operations.

## hello world example

In this example we are going to create a new service called "hello world".

Create a new service python file, in this case we will call our file hello_world_service.py
Then insert the following sample code

```python
import asyncio

from kubesat.validation import MessageSchemas, SharedStorageSchemas
from kubesat.services import ServiceTypes
from kubesat.base_simulation import BaseSimulation

simulation = BaseSimulation(ServiceTypes.HelloWorld, SharedStorageSchemas.HELLO_WORLD_STORAGE, "./hello_world_config.json")

@simulation.startup_callback
async def hello_world(natsHandler, shared_storage, logger):
    print("Hello World!!!")

@simulation.subscribe_nats_callback("hello-kubesat", MessageSchemas.TEST_MESSAGE)
async def welcome_message(msg, natsHandler, shared_storage, logger):
    print(msg.encode_json())
    print(natsHandler._connection_string)
    print(shared_storage)
    await logger.error("This is hello_world service")
    message = natsHandler.create_message({
        "testData": "Hello Welcome To Kubesat"
    }, MessageSchemas.TEST_MESSAGE)
    await natsHandler.send_data("task", message)
    print("Sent data 1 ")

@simulation.subscribe_data_callback("task", MessageSchemas.TEST_MESSAGE, validator=validator)
async def work_on_task(msg, natsHandler, shared_storage, logger):
    print(f"received data response: {msg.encode_json()}")
```

The first callback "hello_world" will be called when the service is started. (NOTE: there should be only one startup_callback per one service(ie:- one use-case)).
Then "welcome_message" will be called whenever there is any message published to 'hello-kubesat' channel/topic/subject. In this example once we then publish to the 'task' topic.
The last callback is "work_on_task" which is called when there is a message in the 'task' topic, in our case this was published from "welcome_message" callback.

Create a config file, example:- hello_world_config.json.

```json
{
    "sender_id": "hello_world",
    "shared_storage": {
        "greeting": "Hello From Config"
    }
}
```

This config file is passed as a paramter in the "hello_world_service.py" . Also note the structure used in this config file since it will be used when creating a SharedStoragesSchema

We then have to add our SharedStorageSchema in "utils/kubesat/validation.py" in the "SharedStorageSchemas" class.

```python
HELLO_WORLD_STORAGE = {
        "type": "object",
        "additionalProperties": False,
        "required": ["greeting"],
        "properties": {
            "greeting": {
                "type": "string",
            }
        }
    }
```

One more thing we need to do is to add/append 'HelloWorld' service to the ServiceTypes class in "util/kubesat/services.py".
Add this line to the class:-
```python
HelloWorld = "helloworld"
```

We can use the same "run.py", only change the line "from template_service import simulation" to "from hello_world_service import simulation"

In order to test this service you can execute the "run.py" with the respective arguments.

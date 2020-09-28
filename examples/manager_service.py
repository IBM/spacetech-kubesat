import asyncio
import time

from kubesat.validation import MessageSchemas, SharedStorageSchemas
from kubesat.base_service import BaseService

SERVICE_TYPE = 'manager'
manager = BaseService(
    SERVICE_TYPE, SharedStorageSchemas.STORAGE, './manager_service.json')


@manager.schedule_callback(2)
# Broadcast service availability check request every two seconds.
async def send_availabilty_check_request(nats, shared_storage, logger):
    """
    Send availabiltiy check request

    Args:
        nats (NatsHandler): connection to nats used to send and receive messages
        shared_storage (dict): dictionary that stores local data for the service
        logger (NatsLogger): logger that can be used to communicate the state of the system
    """
    message = nats.create_message({
        "type": "request",
        "function": "is_available",
        "parameters": {
            "service": "weather_service"
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
    # Start the manager service
    manager.run(kubernetes_config_file="./msvm1.yaml")

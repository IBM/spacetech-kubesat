import asyncio

from kubesat.validation import MessageSchemas, SharedStorageSchemas
from kubesat.base_service import BaseService

SERVICE_TYPE = 'basic'
basic = BaseService(
    SERVICE_TYPE, SharedStorageSchemas.STORAGE, './basic_service.json')


@basic.schedule_callback(2)
async def send_ping_message(nats, shared_storage, logger):
    """
    Send a ping message.

    Args:
        nats (NatsHandler): connection to nats used to send and receive messages
        shared_storage (dict): dictionary that stores local data for the service
        logger (NatsLogger): logger that can be used to communicate the state of the system
    """
    message = nats.create_message({
        "message": "ping"
    }, MessageSchemas.MESSAGE)

    # Send a ping message to ping.basic.basic_service_1 subject
    await nats.send_message("ping.basic.basic_service_1", message)
    print(f"send_ping_message: {message.encode_json()}")


@basic.subscribe_nats_callback("ping.basic.basic_service_1",  MessageSchemas.MESSAGE)
async def receive_ping_message(message, nats, shared_storage, logger):
    message_json = message.encode_json()
    print(f"got a ping message: {message_json}")
    shared_storage["last_ping"] = message_json['time_sent']


@basic.startup_callback
async def main(nats_handler, shared_storage, logger):
    print(f"{SERVICE_TYPE} service has started with a sender ID {basic.sender_id}")

if __name__ == '__main__':
    basic.run()

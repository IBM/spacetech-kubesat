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

import csv
from datetime import datetime
from kubesat.base_simulation import BaseSimulation
from kubesat.services import ServiceTypes
from kubesat.validation import MessageSchemas, SharedStorageSchemas

simulation = BaseSimulation(ServiceTypes.Logging, SharedStorageSchemas.LOGGING_SERVICE_STORAGE)

@simulation.startup_callback
async def create_log_file(nats_handler, shared_storage, logger):
    """
    Creates CSV for logger outputs 

    Args:
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc.
    """
    if shared_storage["log_path"][-1] == "/":
        shared_storage["log_path"] = shared_storage["log_path"] + f"log-{datetime.utcnow().isoformat()}.csv"
        with open(shared_storage["log_path"], "a+") as f:
            writer = csv.writer(f)
            writer.writerow(["sender_id", "time_sent", "message"])
    elif shared_storage["log_path"][-4:] == ".csv":
        return
    else:
        raise ValueError(f"Invalid logging file path {shared_storage['log_path']} is neither folder nor csv")

@simulation.subscribe_nats_callback("logging.>", MessageSchemas.LOG_MESSAGE)
async def print_log(message, nats_handler, shared_storage, logger):
    """
    Callback that prints out incoming logs

    Args:
        message (Message): incoming message with current pointing target of the sender
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc.
    """
    print(f"Sender: {message.sender_id} at {message.time_sent}: {message.data}")
    with open(shared_storage["log_path"], "a+") as f:
        writer = csv.writer(f)
        writer.writerow([str(message.sender_id), str(message.time_sent), str(message.data)])

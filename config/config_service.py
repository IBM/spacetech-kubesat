import json
from kubesat.validation import MessageSchemas, SharedStorageSchemas
from kubesat.base_simulation import BaseSimulation
from kubesat.services import ServiceTypes

simulation = BaseSimulation(ServiceTypes.Config, SharedStorageSchemas.CONFIG_SERVICE_STORAGE, "./simulation_config/simulation/config.json")

@simulation.request_nats_callback("initialize.service", MessageSchemas.SERVICE_TYPE_MESSAGE, append_sender_id=False)
async def initialize_service(message, nats_handler, shared_storage, logger):
    """
    Initalizes services based on given config files

    Args:
        message (Message): incoming message with the ID of the sending Satellite
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc,
    """

    service_type = message.data
    print(f"Initializing {service_type} while config storage is {shared_storage}")
    for service in shared_storage["simulation"]:
        if service == service_type and not shared_storage["simulation"][service]:
            with open(f"{shared_storage['config_path']}/simulation/{service}.json", "r") as f:
                shared_storage["simulation"][service] = True
                new_config = json.load(f)
                return nats_handler.create_message(new_config, MessageSchemas.CONFIG_MESSAGE)
    for cubesat in shared_storage["cubesats"]:
        for service in shared_storage["cubesats"][cubesat]:
            if service == service_type and not shared_storage["cubesats"][cubesat][service]:
                with open(f"{shared_storage['config_path']}/cubesats/{cubesat}/{service}.json", "r") as f:
                    shared_storage["cubesats"][cubesat][service] = True
                    new_config = json.load(f)
                    return nats_handler.create_message(new_config, MessageSchemas.CONFIG_MESSAGE)
    for groundstation in shared_storage["groundstations"]:
        for service in shared_storage["groundstations"][groundstation]:
            if service == service_type and not shared_storage["groundstations"][groundstation][service]:
                with open(f"{shared_storage['config_path']}/groundstations/{groundstation}/{service}.json", "r") as f:
                    shared_storage["groundstations"][groundstation][service] = True
                    new_config = json.load(f)
                    return nats_handler.create_message(new_config, MessageSchemas.CONFIG_MESSAGE)
    for iot in shared_storage["iots"]:
        for service in shared_storage["iots"][iot]:
            if service == service_type and not shared_storage["iots"][iot][service]:
                with open(f"{shared_storage['config_path']}/iots/{iot}/{service}.json", "r") as f:
                    shared_storage["iots"][iot][service] = True
                    new_config = json.load(f)
                    return nats_handler.create_message(new_config, MessageSchemas.CONFIG_MESSAGE)

    raise ValueError("Invalid Service Type or already activated: (bad)")

@simulation.schedule_callback(10)
async def check_status(nats, shared_storage, logger):
    """
    Every 10 seconds sends a Nats request to every service that in its shared storage is "true" (ie: running) and
    then if there is no reply changes the service status to false (ie: not running). 
    Args:
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc,
    """
    message = nats.create_message("STATUS", MessageSchemas.STATUS_MESSAGE)
    for service in shared_storage["simulation"]:
        if shared_storage["simulation"][service] == True:
            try:
                await nats.request_message("node.status." + service + ".simulation", message, MessageSchemas.STATUS_MESSAGE, 5)
            except Exception as e:
                await logger.info(f"Service has died: {service}")
                shared_storage["simulation"][service] = False
    for node in shared_storage["cubesats"]:
        for service in shared_storage["cubesats"][node]:
            if shared_storage["cubesats"][node][service] == True:
                try:
                    await nats.request_message("node.status." + service + "."+node, message, MessageSchemas.STATUS_MESSAGE, 5)
                except Exception as e:
                    await logger.info(f"Service has died: {node} {service}")
                    shared_storage["cubesats"][node][service] = False
    for node in shared_storage["groundstations"]:
        for service in shared_storage["groundstations"][node]:
            if shared_storage["groundstations"][node][service] == True:
                try:
                    await nats.request_message("node.status." + service + "."+node, message, MessageSchemas.STATUS_MESSAGE, 5)
                except Exception as e:
                    await logger.info(f"Service has died: {node} {service}")
                    shared_storage["groundstations"][node][service] = False
    for node in shared_storage["iots"]:
        for service in shared_storage["iots"][node]:
            if shared_storage["iots"][node][service] == True:
                try:
                    await nats.request_message("node.status." + service + "."+node, message, MessageSchemas.STATUS_MESSAGE, 5)
                except Exception as e:
                    await logger.info(f"Service has died: {node} {service}")
                    shared_storage["iots"][node][service] = False

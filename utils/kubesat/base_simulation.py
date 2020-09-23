from aiologger.loggers.json import JsonLogger

from kubesat.base_service import BaseService
from kubesat.message import Message
from kubesat.nats_handler import NatsHandler
from kubesat.nats_logger import NatsLoggerFactory
from kubesat.validation import validate_json, MessageSchemas


class BaseSimulation(BaseService):
    def __init__(self, service_type: str, schema: dict, config_path: str = None):
        """
        Registers a NATS callback that subscribes to the subject "simulation.timestep". When the callback receives a message, 
        it updates the current time internal to the simulation's NATS handler object. 
        """
        super().__init__(service_type, schema, config_path)

        # subscribing to timestep by default to update time in nats_handler
        @self.subscribe_nats_callback("simulation.timestep", MessageSchemas.TIMESTEP_MESSAGE)
        async def simulation_timepulse(message: Message, nats_handler: NatsHandler, shared_storage: dict, logger: JsonLogger):
            nats_handler.time_sent = message.data["time"]

        """
        if that fails attempts to get it from a different
        service that has a callback registered on channel "initialize.service". 
        """

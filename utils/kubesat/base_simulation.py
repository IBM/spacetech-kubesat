from kubesat.base_service import BaseService


class BaseSimulation(BaseService):
    def __init__(self, service_type: str, schema: dict, config_path: str = None):
        super().__init__(service_type, schema, config_path)

import os
from kubernetes import client, config
import json


class KubernetesHandler:
    def __init__(self, kubernetes_config_file=None):
        """
        Creates a kubernetes handler object
        Args:
            kubernets_config(optional): kubernetes config file path
        """

        self.kubernetes = None
        self._namespace = 'services'

        # Initialize Kubernetes Client
        if kubernetes_config_file:
            try:
                config.load_kube_config(kubernetes_config_file)
                self.kubernetes = client.CoreV1Api()
            except Exception as e:
                raise RuntimeError(
                    'Can not load kubernetes config from the file %s, error: %s', kubernetes_config_file, e)
        elif os.environ.get('KUBERNETES_SERVICE_HOST'):
            try:
                config.load_incluster_config()
                self.kubernetes = client.CoreV1Api()
            except:
                raise RuntimeError(
                    'Can not initialize with in-cluster config.')

    def get_pods(self):
        """
        Gets pod list in the namespace
        Args:
        """
        pods = self.kubernetes.list_namespaced_pod(self._namespace)
        return pods

    def get_availability(self, service: str):
        """
        Return the system availability
        """
        if len(self.get_pods().items) > 0:
            return False
        return True

    def start_service(self, service: str):
        pass

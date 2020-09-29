import os
from kubernetes import client, config
import json


class KubernetesHandler:
    def __init__(self, kubernetes_config_file=None, namespace=None):
        """
        Creates a kubernetes handler object
        Args:
            kubernets_config(optional): kubernetes config file path
            namespace(optional): kubernetes namespace
        """

        self.kubernetes = None

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
        else:
            try:
                config.load_kube_config()
                self.kubernetes = client.CoreV1Api()
            except:
                pass

        if namespace is not None:
            self._namespace = namespace
        else:
            self._namespace = 'default'

    def get_pods(self, namespace=None):
        """
        Gets pod list in the namespace
        Args:
            namespace(optional): kubernetes namespace
        """
        if not namespace:
            namespace = self._namespace
        pods = self.kubernetes.list_namespaced_pod(namespace)
        return pods

    def get_availability(self, service: str, namespace=None):
        """
        Return the system availability
        """
        services = self.get_services()
        if len(self.get_pods(namespace).items) == 0 and (service in services):
            return True
        return False

    def start_service(self, service: str, namespace=None):
        pass

    def get_services(self):
        """
        Read the services configmap in the kube-system namespace and returns data.
        The data has a dict structure with a structure of 'SERVICE_NAME':'IMAGE_NAME'.
        """
        config_map = self.kubernetes.read_namespaced_config_map(
            'services', 'kube-system')
        return config_map.data

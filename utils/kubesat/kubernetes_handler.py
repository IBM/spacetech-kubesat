import os
import json
import string
import random
from kubernetes import client, config
from kubernetes.client.rest import ApiException


class KubernetesHandler:
    def __init__(self, kubernetes_config_file: str = None, namespace: str = 'default'):
        """
        Creates a kubernetes handler object
        Args:
            kubernets_config_file(optional): kubernetes config file path
            namespace(optional): kubernetes namespace
        """

        self._namespace = namespace
        self.kubernetes_api = {}

        # Load a configuration from the config file.
        if kubernetes_config_file:
            try:
                config.load_kube_config(kubernetes_config_file)
                self.kubernetes_api = {
                    'core': client.CoreV1Api(), 'batch': client.BatchV1Api()}
            except Exception as e:
                raise RuntimeError(
                    'Unable to load kubernetes config from the file %s, error: %s', kubernetes_config_file, e)
        # Load in-cluster configuration.
        elif os.environ.get('KUBERNETES_SERVICE_HOST'):
            try:
                config.load_incluster_config()
                self.kubernetes_api = {
                    'core': client.CoreV1Api(), 'batch': client.BatchV1Api()}
            except:
                raise RuntimeError(
                    'Unable to not initialize with in-cluster config.')
        # Try to load default configuration.
        else:
            try:
                config.load_kube_config()
                self.kubernetes_api = {
                    'core': client.CoreV1Api(), 'batch': client.BatchV1Api()}
            except:
                pass

    def _get_namespace(self, namespace: str):
        if not namespace:
            return self._namespace
        return namespace

    def _get_pods(self, namespace: str = None):
        """
        Gets pod list in the namespace
        Args:
            namespace(optional): kubernetes namespace
        """
        namespace = self._get_namespace(namespace)
        pods = self.kubernetes_api['core'].list_namespaced_pod(namespace)
        return pods

    def get_availability(self, service: str, namespace: str = None):
        """
        Return the system availability
        """
        services = self.get_services()
        if len(self._get_pods(namespace).items) == 0 and (service in services):
            return True
        return False

    def _create_job_object(self, name: str, container_image: str, namespace: str = None, container_name: str = "servicecontainer", env_vars: dict = {}, command: list = [], active_deadline_seconds: int = 3600):
        namespace = self._get_namespace(namespace)
        body = client.V1Job(api_version="batch/v1", kind="Job")
        body.metadata = client.V1ObjectMeta(namespace=namespace, name=name)
        body.status = client.V1JobStatus()
        template = client.V1PodTemplate()
        template.template = client.V1PodTemplateSpec()
        env_list = []
        for env_name, env_value in env_vars.items():
            env_list.append(client.V1EnvVar(name=env_name, value=env_value))
        container = client.V1Container(
            name=container_name, image=container_image, env=env_list, command=command)
        template.template.spec = client.V1PodSpec(
            containers=[container], restart_policy='Never')
        # Set active_deadline_seconds
        body.spec = client.V1JobSpec(
            ttl_seconds_after_finished=600, template=template.template, active_deadline_seconds=active_deadline_seconds)
        return body

    def start_service(self, service: str, namespace: str = None):
        """
        Find a container image information from a configmap and start a new job
        """
        namespace = self._get_namespace(namespace)
        container_image = self._get_service_image(service)
        name = service + "-" + \
            ''.join(random.choice('abcdefghijklmnopqrstuvwxyz')
                    for _ in range(3))
        body = self._create_job_object(
            name, container_image, namespace=namespace)
        try:
            self.kubernetes_api['batch'].create_namespaced_job(
                namespace, body, pretty=True)
        except ApiException as e:
            print("Exception when start a service: %s\n" % e)
        return

    def get_services(self):
        """
        Read the services configmap in the kube-system namespace and returns data.
        The data has a dict structure with a structure of 'SERVICE_NAME':'IMAGE_NAME'.
        """
        config_map = self.kubernetes_api['core'].read_namespaced_config_map(
            'services', 'kube-system')
        return config_map.data

    def _get_service_image(self, service: str):
        return self.get_services()[service]

    def _delete_inactive_jobs(self, namespace=None):
        namespace = self._get_namespace(namespace)
        try:
            jobs = self.kubernetes_api['batch'].list_namespaced_job(namespace,
                                                                    pretty=True,
                                                                    timeout_seconds=60)
        except ApiException as e:
            print("Exception in _delete_inactive_jobs: %s\n" % e)

        for job in jobs.items:
            if job.status.active is None:
                try:
                    api_response = self.kubernetes_api['batch'].delete_namespaced_job(job.metadata.name,
                                                                                      namespace,
                                                                                      grace_period_seconds=0,
                                                                                      propagation_policy='Background')
                except ApiException as e:
                    print(
                        "Exception in _delete_inactive_jobs: %s\n" % e)
        return

variable ibmcloud_api_key {}
variable iaas_classic_username {}
variable iaas_classic_api_key {}

variable "ssh_key_name" {
  description = "sshkey name/label in IBM Cloud"
  type = string
  default = ""
}

variable "namespace" {
  description = "k8s namespace"
  type = string
  default = "demo"
}

variable "deploy_kubesat" {
  default = true
}

variable "app" {
  type = string
  default = "kubesat"
}

variable "ver" {
  type = string
  default = "1.0"
}

variable "swarm_domain" {
  description = "DNS domain for swarm nodes"
  type = string
  default = "kubesat.demo"
}

variable "ground_hostname" {
  description = "ground server dns hostname"
  type = string
  default = "groundstation"
}

variable "swarm_hostname" {
  description = "swarm server dns hostname"
  type = string
  default = "cubesat"
}

variable "number_of_ground_stations" {
  description = "number of ground stations"
  default = 1
}

variable "swarm_size" {
  description = "number of nodes in swarm"
  default = 1
}

variable "number_of_iot_sensors" {
  description = "number of iot sensors"
  default = 2
}

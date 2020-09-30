## Build and Deploy
Build each service as a container image using the respective Dockerfile. Services can be deployed to a Kubernetes cluster.

Build and deployment can be done though a terraform plan targeting IBM Cloud. After you make code changes, test them in your local dev environment where each service runs as a Python process, and then apply the terraform plan using the commands below to deploy to IBM Cloud. 

In coming weeks, CI/CD pipeline will be implemented to run the code builds and deployment triggered by code changes pushed to SCM.

## Deploy to IBM Cloud

Deploy KubeSat with satellites and ground stations setup in a distributed model running on IBM Cloud virtual server instances.

Each satellite node and ground-station node will be hosted on a separate VSIs running K3s on Ubuntu. NATS, Redis, and the satellite services are all deployed on K3s.

NATS service on satellite nodes will be connected to the ground-stations as a NATS leafnode. All ground station nodes form a NATS super-cluster. Satellite nodes form NATS clusters on demand as determined by the KubeSat cluster microservice. This provides the secure high-speed messaging platform for asynchronous exchange of messages and data between all the microservices hosted on the different nodes in the swarm.

Run the following commands to apply a terraform plan to deploy KubeSat to IBM Cloud.

```bash
cd spacetech-kubesat/deploy/tf-ibmcloud
```

In `tf-ibmcloud` folder, create `terraform.tfvars` with following minimum set of values. Refer to `variables.tf` for full list of available variables.

```terraform
ibmcloud_api_key = "your-ibm-cloud-platform-apikey"
iaas_classic_username = "your-ibm-cloud-classic-username"
iaas_classic_api_key = "your-ibm-cloud-classic-apikey"
ssh_key_name="ssh-key"
```

Run following terraform commands
```
terraform init
terraform apply
```

Go to __http://\<ip-address-of-groundstation-0\>:8080__ to view KubeSat dashboard.

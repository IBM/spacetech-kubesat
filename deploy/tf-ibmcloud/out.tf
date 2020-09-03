output "ground_hostnames" {
  value = ibm_compute_vm_instance.ground.*.hostname
}

output "ground_IPs" {
  value = ibm_compute_vm_instance.ground.*.ipv4_address
}

output "ground_IPs_private" {
  value = ibm_compute_vm_instance.ground.*.ipv4_address_private
}

output "swarm_hostnames" {
  value = ibm_compute_vm_instance.swarm.*.hostname
}

output "swarm_IPs" {
  value = ibm_compute_vm_instance.swarm.*.ipv4_address
}

output "swarm_IPs_private" {
  value = ibm_compute_vm_instance.swarm.*.ipv4_address_private
}

output "ssh_key" {
  value = data.ibm_compute_ssh_key.ssh_key_name.label
}

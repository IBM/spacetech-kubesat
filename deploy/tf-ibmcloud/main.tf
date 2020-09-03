data "ibm_compute_ssh_key" "ssh_key_name" {
  label = var.ssh_key_name
}

resource "tls_private_key" "tf_ssh_key" {
  algorithm   = "RSA"
}

resource "random_password" "lf_pass" {
  count = var.swarm_size
  length = 16
  special = false
}

output "vm_external_ip" {
  description = "Static external IP of the Ember Grid VM"
  value       = google_compute_address.static_ip.address
}

output "vm_internal_ip" {
  description = "Internal IP of the VM within the VPC subnet"
  value       = google_compute_instance.vm.network_interface[0].network_ip
}

output "vm_name" {
  description = "GCE instance name"
  value       = google_compute_instance.vm.name
}

output "vm_zone" {
  description = "Zone the VM was deployed into"
  value       = google_compute_instance.vm.zone
}

output "service_account_email" {
  description = "Email of the VM service account"
  value       = google_service_account.ember_sa.email
}

output "data_disk_name" {
  description = "Name of the persistent data disk"
  value       = google_compute_disk.data.name
}

output "ssh_command" {
  description = "SSH command to connect to the VM as the provisioning user"
  value       = "ssh ${var.ssh_user}@${google_compute_address.static_ip.address}"
}

output "ansible_inventory_entry" {
  description = "Paste this into infra/ansible/inventory.ini under [ember_grid]"
  value       = "ember-grid-vm ansible_host=${google_compute_address.static_ip.address} ansible_user=${var.ssh_user}"
}

output "service_urls" {
  description = "Service URLs once provisioning is complete"
  value = {
    flask_dashboard = "http://${google_compute_address.static_ip.address}:5000"
    grafana         = "http://${google_compute_address.static_ip.address}:3000"
    prometheus      = "http://${google_compute_address.static_ip.address}:9090"
    rundeck         = "http://${google_compute_address.static_ip.address}:4440"
    ollama          = "http://${google_compute_address.static_ip.address}:11434"
    elasticsearch   = "http://${google_compute_address.static_ip.address}:9200"
  }
}

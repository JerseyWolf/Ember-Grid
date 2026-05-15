terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  # Uncomment to store state in GCS:
  # backend "gcs" {
  #   bucket = "ember-grid-tf-state"
  #   prefix = "ops-knowledge-loop"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------

resource "google_compute_network" "vpc" {
  name                    = "ember-grid-vpc"
  auto_create_subnetworks = false
  description             = "Dedicated VPC for ops-knowledge-loop infrastructure"
}

resource "google_compute_subnetwork" "subnet" {
  name          = "ember-grid-subnet"
  ip_cidr_range = "10.10.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id

  # Enable flow logs for network-level observability (future: feed into SIEM)
  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

resource "google_compute_address" "static_ip" {
  name        = "ember-grid-static-ip"
  region      = var.region
  description = "Static external IP for the ops-knowledge-loop VM"
}

# ---------------------------------------------------------------------------
# Firewall rules
# ---------------------------------------------------------------------------

# SSH — restricted to operator IP(s) via var.ssh_source_ranges
resource "google_compute_firewall" "allow_ssh" {
  name        = "ember-grid-allow-ssh"
  network     = google_compute_network.vpc.name
  description = "SSH access for operators and Ansible provisioning"
  priority    = 1000

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = var.ssh_source_ranges
  target_tags   = ["ember-grid"]
}

# Internal health-check probes from GCP
resource "google_compute_firewall" "allow_health_checks" {
  name        = "ember-grid-allow-health-checks"
  network     = google_compute_network.vpc.name
  description = "GCP health-check probe ranges"
  priority    = 900

  allow {
    protocol = "tcp"
    ports    = ["80", "443", "5000"]
  }

  source_ranges = ["35.191.0.0/16", "130.211.0.0/22"]
  target_tags   = ["ember-grid"]
}

# Web / dashboard surface — Nginx (80/443), Flask (5000), Grafana (3000), Rundeck (4440)
resource "google_compute_firewall" "allow_web" {
  name        = "ember-grid-allow-web"
  network     = google_compute_network.vpc.name
  description = "Operator-facing web UIs: Nginx, Flask dashboard, Grafana, Rundeck"
  priority    = 1000

  allow {
    protocol = "tcp"
    ports    = [
      "80",   # Nginx HTTP
      "443",  # Nginx HTTPS (TLS termination for all services)
      "5000", # Flask ops dashboard (direct, bypasses Nginx for dev)
      "3000", # Grafana
      "4440", # Rundeck web console
    ]
  }

  source_ranges = var.internal_service_source_ranges
  target_tags   = ["ember-grid"]
}

# Observability / data — Prometheus (9090), Elasticsearch (9200/9300), Redis (6379)
resource "google_compute_firewall" "allow_data_services" {
  name        = "ember-grid-allow-data-services"
  network     = google_compute_network.vpc.name
  description = "Prometheus scrape, Elasticsearch HTTP/transport, Redis — restrict to internal in production"
  priority    = 1000

  allow {
    protocol = "tcp"
    ports    = [
      "9090", # Prometheus UI + remote-write endpoint
      "9200", # Elasticsearch HTTP API
      "9300", # Elasticsearch transport (cluster inter-node, future multi-node)
      "6379", # Redis (used by product-search service, notification dedup)
    ]
  }

  source_ranges = var.internal_service_source_ranges
  target_tags   = ["ember-grid"]
}

# Ollama API — intentionally narrow; only allow from VPC or explicit operator ranges
resource "google_compute_firewall" "allow_ollama" {
  name        = "ember-grid-allow-ollama"
  network     = google_compute_network.vpc.name
  description = "Ollama inference API (11434). Kept internal — no data should leave the machine."
  priority    = 900

  allow {
    protocol = "tcp"
    ports    = ["11434"]
  }

  source_ranges = var.ollama_source_ranges
  target_tags   = ["ember-grid"]
}

# Explicitly deny all other inbound traffic (defense-in-depth)
resource "google_compute_firewall" "deny_all_ingress" {
  name        = "ember-grid-deny-all-ingress"
  network     = google_compute_network.vpc.name
  description = "Explicit deny-all for unmatched ingress (lower priority than allow rules)"
  priority    = 65534
  direction   = "INGRESS"

  deny {
    protocol = "all"
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["ember-grid"]
}

# ---------------------------------------------------------------------------
# Service account
# ---------------------------------------------------------------------------

resource "google_service_account" "ember_sa" {
  account_id   = "ember-grid-sa"
  display_name = "Ember Grid VM Service Account"
  description  = "Attached to the ops-knowledge-loop VM. Add roles as integrations are enabled."
}

# Cloud Logging write — pipeline and Ollama logs → Cloud Logging
resource "google_project_iam_member" "sa_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.ember_sa.email}"
}

# Cloud Monitoring write — Prometheus → GCP Metrics (optional, useful for alerting)
resource "google_project_iam_member" "sa_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.ember_sa.email}"
}

# Secret Manager read — future: store ServiceNow / Rundeck / GitHub tokens here
resource "google_project_iam_member" "sa_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.ember_sa.email}"
}

# ---------------------------------------------------------------------------
# Storage — persistent data disk
# ---------------------------------------------------------------------------

resource "google_compute_disk" "data" {
  name        = "ember-grid-data"
  type        = "pd-ssd"
  zone        = var.zone
  size        = var.data_disk_size_gb
  description = "Persistent SSD for Ollama models, ChromaDB, Elasticsearch, Prometheus TSDB"

  labels = {
    env     = var.env
    project = "ember-grid"
  }
}

# ---------------------------------------------------------------------------
# VM instance
# ---------------------------------------------------------------------------

resource "google_compute_instance" "vm" {
  name         = "ember-grid-vm"
  machine_type = var.machine_type
  zone         = var.zone

  tags = ["ember-grid"]

  labels = {
    env     = var.env
    project = "ember-grid"
    role    = "ops-knowledge-loop"
  }

  boot_disk {
    initialize_params {
      # Ubuntu 22.04 LTS — well-supported NVIDIA driver path, Python 3.11 available from deadsnakes PPA
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = var.boot_disk_size_gb
      type  = "pd-ssd"
    }
    auto_delete = false  # preserve OS disk on instance deletion
  }

  # Persistent data disk mounted by Ansible at /data
  attached_disk {
    source      = google_compute_disk.data.id
    device_name = "ember-grid-data"
    mode        = "READ_WRITE"
  }

  network_interface {
    network    = google_compute_network.vpc.id
    subnetwork = google_compute_subnetwork.subnet.id

    access_config {
      nat_ip = google_compute_address.static_ip.address
    }
  }

  # NVIDIA L4 — 24 GB VRAM. Fits qwen3:14b Q4_K_M (9.3 GB) with headroom for
  # sentence-transformers all-MiniLM-L6-v2 and future larger models.
  # For qwen3:32b (future), upgrade to g2-standard-16 or add a second L4.
  guest_accelerator {
    type  = var.gpu_type
    count = var.gpu_count
  }

  scheduling {
    # GPU instances must terminate on live-migrate events
    on_host_maintenance = "TERMINATE"
    automatic_restart   = true
    preemptible         = false  # set true for staging to cut costs (~70%)
  }

  service_account {
    email  = google_service_account.ember_sa.email
    scopes = ["cloud-platform"]
  }

  metadata = {
    ssh-keys               = "${var.ssh_user}:${file(var.ssh_public_key_path)}"
    # Disabling legacy metadata server endpoints hardens the instance
    block-project-ssh-keys = "false"
    serial-port-enable     = "false"
  }

  # Minimal cloud-init: ensures SSH is ready before Ansible connects
  metadata_startup_script = <<-STARTUP
    #!/bin/bash
    apt-get update -qq
    apt-get install -y python3-apt python3-minimal openssh-server
    systemctl enable --now ssh
  STARTUP

  shielded_instance_config {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }
}

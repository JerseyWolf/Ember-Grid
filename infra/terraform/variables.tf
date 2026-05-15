variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region. europe-west2 (London) is closest to UK retail ops."
  type        = string
  default     = "europe-west2"
}

variable "zone" {
  description = "GCP zone. L4 GPU availability varies by zone — check before changing."
  type        = string
  default     = "europe-west2-a"
}

variable "machine_type" {
  description = <<-EOT
    GCP machine type.
    - g2-standard-8  : 8 vCPU, 32 GB RAM, NVIDIA L4 24 GB VRAM  (recommended — fits qwen3:14b Q4_K_M at 9.3 GB)
    - g2-standard-16 : 16 vCPU, 64 GB RAM, NVIDIA L4 24 GB VRAM (if Elasticsearch + Ollama run together under load)
    - n1-standard-8 + nvidia-tesla-t4 : budget alternative, 16 GB VRAM (tight for qwen3:14b)
  EOT
  type        = string
  default     = "g2-standard-8"
}

variable "gpu_type" {
  description = "GPU accelerator type. nvidia-l4 for g2 series, nvidia-tesla-t4 for n1 series."
  type        = string
  default     = "nvidia-l4"
}

variable "gpu_count" {
  description = "Number of GPUs to attach."
  type        = number
  default     = 1
}

variable "boot_disk_size_gb" {
  description = "Boot disk size in GB. OS + Python env + Docker images."
  type        = number
  default     = 100
}

variable "data_disk_size_gb" {
  description = <<-EOT
    Persistent data disk size in GB. Budget:
    - qwen3:14b Q4_K_M       ~9.3 GB
    - qwen2.5-coder:7b Q4    ~4.1 GB
    - nomic-embed-text        ~0.3 GB  (optional: faster than sentence-transformers at runtime)
    - ChromaDB + knowledge base ~2 GB (grows with incident corpus)
    - Elasticsearch indices   ~20 GB  (grows with repo indexing in future phases)
    - Docker images           ~15 GB
    - Prometheus TSDB         ~10 GB  (90-day retention at low cardinality)
    Total floor ~61 GB; 300 GB gives comfortable growth headroom.
  EOT
  type        = number
  default     = 300
}

variable "ssh_user" {
  description = "OS-level username injected via instance metadata."
  type        = string
  default     = "ember"
}

variable "ssh_public_key_path" {
  description = "Local path to the SSH public key to inject into the VM."
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "ssh_source_ranges" {
  description = "CIDR blocks allowed to reach port 22. Restrict to your office/VPN egress IP in production."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "internal_service_source_ranges" {
  description = "CIDR blocks allowed to reach dashboard, Grafana, Rundeck, Prometheus, and Elasticsearch."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "ollama_source_ranges" {
  description = "CIDR blocks allowed to reach the Ollama API on port 11434. Keep internal-only unless a remote LLM client is needed."
  type        = list(string)
  default     = ["10.0.0.0/8"]
}

variable "github_repo_url" {
  description = "Git clone URL for the ops-knowledge-loop repository. Used in Ansible, documented here for reference."
  type        = string
  default     = "https://github.com/ember-grid/ops-knowledge-loop.git"
}

variable "env" {
  description = "Deployment environment label (production / staging)."
  type        = string
  default     = "production"
}

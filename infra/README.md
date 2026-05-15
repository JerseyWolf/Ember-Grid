# Ember Grid — Infrastructure

Terraform + Ansible for provisioning the ops-knowledge-loop environment on a
Google Cloud GPU VM.

---

## Architecture

```
GCP project
└── ember-grid-vpc  (10.10.0.0/24, europe-west2)
    └── ember-grid-vm  (g2-standard-8, NVIDIA L4 24 GB VRAM)
        ├── boot disk   100 GB SSD  (OS, Docker images, Python env)
        └── data disk   300 GB SSD  /data
            ├── ollama_models/      qwen3:14b, qwen2.5-coder:7b, nomic-embed-text
            ├── chroma_db/          ChromaDB vector store
            ├── elasticsearch/      search index + future repo/Confluence indexing
            ├── redis/              cache + notification dedup + future Celery queue
            ├── prometheus/         90-day TSDB
            ├── grafana/            dashboard state
            ├── rundeck/            job audit log
            └── logs/               pipeline, RAG rebuild, Nginx, Ollama
```

---

## Prerequisites

| Tool | Minimum version |
|------|----------------|
| Terraform | 1.5.0 |
| Ansible | 2.15 |
| `community.general` collection | 8.x (`ansible-galaxy collection install community.general`) |
| GCP project with Compute Engine API enabled | — |
| `gcloud` authenticated (`gcloud auth application-default login`) | — |

---

## Quickstart

### 1 — Terraform (provision VM)

```bash
cd infra/terraform

# Create a terraform.tfvars with at minimum:
# project_id = "your-gcp-project-id"

terraform init
terraform plan -out=tfplan
terraform apply tfplan

# Copy the inventory line printed in outputs
terraform output ansible_inventory_entry
```

### 2 — Ansible (configure VM)

```bash
cd infra/ansible

cp inventory.ini.example inventory.ini
# Paste the IP from the Terraform output into inventory.ini

# Full provisioning (~25 min, dominated by model pulls and apt upgrades)
ansible-playbook -i inventory.ini playbook.yml

# Partial run — re-run a single section after a change
ansible-playbook -i inventory.ini playbook.yml --tags ollama
ansible-playbook -i inventory.ini playbook.yml --tags elasticsearch
ansible-playbook -i inventory.ini playbook.yml --tags observability
ansible-playbook -i inventory.ini playbook.yml --tags project
```

### 3 — Verify

```bash
ssh ember@<EXTERNAL_IP>
cd /opt/ember-grid
source .venv/bin/activate

# Smoke test
python query_live.py "checkout service OOM kill, container hitting memory limit"

# Full demo sequence
python run_demo_sequence.py
```

---

## Services installed

| Service | Port | Purpose | Current status |
|---------|------|---------|---------------|
| Ollama | 11434 | Local LLM inference (qwen3:14b, qwen2.5-coder:7b) | Active at project launch |
| ChromaDB | — | Vector store (embedded, no server) | Active at project launch |
| Elasticsearch | 9200 | Search index, future repo/Confluence indexing | Pre-installed, ready |
| Redis | 6379 | Product-search cache, notification dedup, future Celery queue | Pre-installed, ready |
| Nginx | 80 | Reverse proxy for all HTTP services | Active |
| Prometheus | 9090 | Metrics (confidence distribution, gate rates, P99 latency) | Active via Docker |
| Grafana | 3000 | Dashboards (default creds: admin / ember-grid-admin) | Active via Docker |
| Rundeck | 4440 | Audited job execution (Docker, MOCK_MODE switch-ready) | Pre-installed, ready |
| OPA | 8181 | PR policy enforcement (pr_rules.rego) | Enabled when GitHub Actions runner connected |
| Flask dashboard | 5000 | Live ops dashboard (systemd unit pre-wired) | Disabled until Flask migration |

---

## Mapped to future work (slides_content.md — SLIDE FUTURE)

| Future feature | Infra component pre-installed |
|---------------|-------------------------------|
| Shadow deployment pipeline | systemd timer (`ember-pipeline.timer`), Celery (`celery` + Redis) |
| Repository-aware context | Elasticsearch index (`ops-runbooks`), `PyGithub` in venv |
| Living organisational memory (JIRA, Confluence) | `atlassian-python-api` in venv, Elasticsearch ready for ingestion |
| Slack alerting (extension point in README) | `slack-sdk` in venv, `SLACK_WEBHOOK_URL` in `.env` |
| OPA in GitHub Actions | OPA binary + `.service` unit, policy already on disk |
| Real ServiceNow / Rundeck | `.env` vars pre-wired, Rundeck Docker running, `MOCK_MODE=false` flips it |

---

## Terraform variables

| Variable | Default | Notes |
|---------|---------|-------|
| `project_id` | — | Required |
| `region` | `europe-west2` | London, nearest to UK retail ops |
| `zone` | `europe-west2-a` | L4 GPU available here |
| `machine_type` | `g2-standard-8` | 8 vCPU, 32 GB RAM, NVIDIA L4 24 GB VRAM |
| `data_disk_size_gb` | `300` | Increase if pulling qwen3:32b or large Elasticsearch indices |
| `ssh_source_ranges` | `["0.0.0.0/0"]` | Restrict to your egress IP/VPN in production |
| `ollama_source_ranges` | `["10.0.0.0/8"]` | Keep internal — no prompts leave the machine |

Override in `terraform.tfvars`:
```hcl
project_id          = "my-gcp-project"
ssh_source_ranges   = ["203.0.113.0/32"]
data_disk_size_gb   = 500
```

---

## Cost estimate (europe-west2, on-demand, May 2026)

| Resource | $/hour | $/month (730h) |
|---------|--------|---------------|
| g2-standard-8 + 1× L4 | ~$1.10 | ~$803 |
| 300 GB pd-ssd (data) | ~$0.07 | ~$51 |
| 100 GB pd-ssd (boot) | ~$0.02 | ~$17 |
| Static IP | ~$0.01 | ~$7 |
| **Total** | **~$1.20** | **~$878** |

To reduce cost in staging: set `preemptible = true` in `main.tf` scheduling block (~70% discount).

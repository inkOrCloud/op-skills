---
name: portainer
description: Control Docker containers, stacks, and environments via Portainer API. List containers, start/stop/restart, view logs, inspect containers (docker inspect JSON), redeploy stacks from git, and manage environments (CRUD).
version: 2.1.1
platforms: [macos, linux]
metadata:
  hermes:
    tags: [docker, portainer, containers, devops, deployment]
    category: devops
    requires_toolsets: [terminal, python]
    config:
      - key: PORTAINER_URL
        description: "Portainer server URL (e.g. https://portainer.example.com:9443)"
        default: ""
      - key: PORTAINER_API_KEY
        description: "Portainer API access token (e.g. ptr_...)"
        default: ""
---

# 🐳 Portainer Skill

```
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🐳  P O R T A I N E R   C O N T R O L   C L I  🐳      ║
    ║                                                           ║
    ║       Manage Docker containers via Portainer API          ║
    ║            Start, stop, deploy, redeploy                  ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
```

> *"Docker containers? I'll handle them from my lily pad."* 🐸

---

## 📖 What Does This Skill Do?

The **Portainer Skill** gives you control over your Docker infrastructure through Portainer's REST API. Manage containers, stacks, and deployments without touching the web UI.

**Features:**
- 📊 **Status** — Check Portainer server status
- 🖥️ **Endpoints** — List all Docker environments
- 🔍 **Env Info** — Show detailed info for one environment
- ➕ **Env Create** — Add a new environment (local Docker, Agent, Edge)
- ✏️ **Env Update** — Rename, change URL/group/public-URL
- 🗑️ **Env Delete** — Remove an environment
- 📦 **Containers** — List, start, stop, restart containers
- 📚 **Stacks** — List and view Docker Compose stacks
- ➕ **Stack Create** — Create a new stack from a local compose file
- ⏹️ **Stack Stop / ▶️ Start** — Start or stop an entire stack
- 🔄 **Stack Update** — Update a stack's compose content in-place
- 🗑️ **Stack Delete** — Delete a stack
- 🔄 **Redeploy** — Pull from git and redeploy stacks
- 📜 **Logs** — View container logs
- 🔎 **Inspect** — Full Docker `inspect` JSON for a container (same as `docker inspect`, pretty-printed)
- 🖼️ **Image List** — List all images with size and usage status
- 🔍 **Image Info** — Show image details (entrypoint, env, ports, arch)
- ⬇️ **Image Pull** — Pull an image from a registry
- 🗑️ **Image Delete** — Delete an image by name or ID
- 🧹 **Image Prune** — Remove dangling or all unused images
- 🌐 **Network List** — List all networks on an environment
- 🔍 **Network Info** — Show network details and connected containers
- ➕ **Network Create** — Create a network (bridge/overlay, custom subnet)
- 🗑️ **Network Delete** — Delete a network
- 🔗 **Network Connect** — Connect a container to a network
- 🔌 **Network Disconnect** — Disconnect a container from a network

---

## ⚙️ Requirements

| What | Details |
|------|---------|
| **Portainer** | Version 2.x with API access |
| **Runtime** | Python 3 (stdlib only, no pip dependencies) |
| **Auth** | API Access Token |

### Setup

1. **Get API Token from Portainer:**
   - Log into Portainer web UI
   - Click username → My Account
   - Scroll to "Access tokens" → Add access token
   - Copy the token (you won't see it again!)

2. **Configure credentials (choose one):**

   **Option A — Environment variables:**
   ```bash
   export PORTAINER_URL=https://your-portainer-server:9443
   export PORTAINER_API_KEY=ptr_your_token_here
   ```

   **Option B — `.env` file (auto-loaded from project root):**
   Create a `.env` file in the project root (the parent of `scripts/`):
   ```bash
   PORTAINER_URL=https://your-portainer-server:9443
   PORTAINER_API_KEY=ptr_your_token_here
   ```
   > The script auto-detects and loads `.env` from the project root (the parent of `scripts/`). Environment variables take precedence over `.env` values.

3. **Ready!** 🚀

### Usage

```bash
# All commands follow the same interface
python3 scripts/portainer.py status
python3 scripts/portainer.py endpoints
python3 scripts/portainer.py containers
python3 scripts/portainer.py stacks
```

> 💡 **Agent Note**: Written in pure Python 3 with no external dependencies. Do NOT use `curl` or raw HTTP requests — the `scripts/portainer.py` script handles auth, error handling, and output formatting for all Portainer operations.

---

## 🤖 Agent Instructions

**Always use the Python script for ALL Portainer operations.**

This skill provides a single, authoritative CLI (`python3 scripts/portainer.py`) that wraps the Portainer REST API. You MUST follow these rules:

1. **Do NOT construct `curl` commands** — the Python script handles authentication, endpoint routing, error handling, and JSON formatting automatically.
2. **Do NOT call the Portainer REST API directly** — always delegate through `python3 scripts/portainer.py`.
3. **Do NOT use `jq` or pipe to JSON processors** — the script already pretty-prints output and supports all filtering needs.
4. **All operations** (listing containers, inspecting, logs, stack redeploy, etc.) have a corresponding script subcommand — look up the exact syntax in the reference docs below or run `python3 scripts/portainer.py --help`.

> ⚠️ Using `curl` or raw HTTP calls bypasses error handling and is officially disallowed by this skill.

## 🛠️ Command Overview

Detailed usage for each command group can be found in the `references/` directory:

| Group | File | Commands |
|------|------|------|
| **Endpoints** | `references/endpoints.md` | `status`, `endpoints`, `env-info`, `env-create`, `env-update`, `env-delete` |
| **Containers** | `references/containers.md` | `container-create`, `containers`, `start`, `stop`, `restart`, `logs`, `inspect`, `exec` |
| **Images** | `references/images.md` | `image-list`, `image-info`, `image-pull`, `image-delete`, `image-prune` |
| **Networks** | `references/networks.md` | `network-list`, `network-info`, `network-create`, `network-delete`, `network-connect`, `network-disconnect` |
| **Stacks** | `references/stacks.md` | `stacks`, `stack-info`, `stack-create`, `stack-start`, `stack-stop`, `stack-update`, `stack-delete`, `redeploy` |

## 🎯 Example Workflows

### 🚀 "Deploy Website Update"
```bash
# After merging PR
python3 scripts/portainer.py redeploy 25
python3 scripts/portainer.py logs steinbergerraum-web-1 4 20
```

### ➕ "Launch a New Stack"
```bash
python3 scripts/portainer.py stack-create myapp ./docker-compose.yml 4
python3 scripts/portainer.py stacks
```

### 🔄 "Update a Running Stack"
```bash
python3 scripts/portainer.py stack-update 5 ./docker-compose.v2.yml
python3 scripts/portainer.py stack-info 5
```

### ⏹️▶️ "Maintenance Window"
```bash
python3 scripts/portainer.py stack-stop 5
# ... do maintenance ...
python3 scripts/portainer.py stack-start 5
```

### 🖼️ "Image Housekeeping"
```bash
# See what's taking up space
python3 scripts/portainer.py image-list

# Pull a new version
python3 scripts/portainer.py image-pull nginx 1.27

# Remove the old one
python3 scripts/portainer.py image-delete nginx:1.26

# Clean up all dangling layers
python3 scripts/portainer.py image-prune
```

### 🌐 "Network Management"
```bash
# Overview
python3 scripts/portainer.py network-list

# Create isolated network for a project
python3 scripts/portainer.py network-create myproject-net bridge 172.50.0.0/24 172.50.0.1

# Wire up containers
python3 scripts/portainer.py network-connect myproject-net app
python3 scripts/portainer.py network-connect myproject-net db

# Inspect who's connected
python3 scripts/portainer.py network-info myproject-net

# Cleanup
python3 scripts/portainer.py network-disconnect myproject-net app
python3 scripts/portainer.py network-delete myproject-net
```

### 🗑️ "Tear Down a Stack"
```bash
python3 scripts/portainer.py stack-stop 5
python3 scripts/portainer.py stack-delete 5
```

### 🔧 "Debug Container"
```bash
python3 scripts/portainer.py containers
python3 scripts/portainer.py inspect cora-web-1
python3 scripts/portainer.py logs cora-web-1
python3 scripts/portainer.py restart cora-web-1
```

### 📊 "System Overview"
```bash
python3 scripts/portainer.py status
python3 scripts/portainer.py endpoints
python3 scripts/portainer.py containers
python3 scripts/portainer.py stacks
```

---

## 🔧 Troubleshooting

### ❌ "Authentication required / Repository not found"

**Problem:** Stack redeploy fails with git auth error

**Solution:** The stack needs `repositoryGitCredentialID` parameter. The script handles this automatically by reading from the existing stack config.

---

### ❌ "Container not found"

**Problem:** Container name doesn't match

**Solution:** Use exact name from `python3 scripts/portainer.py containers`:
- Include the full name: `steinbergerraum-web-1` not `steinbergerraum`
- Names are case-sensitive

---

### ❌ "PORTAINER_URL and PORTAINER_API_KEY must be set"

**Problem:** Credentials not configured

**Solution:**
```bash
export PORTAINER_URL=https://your-server:9443
export PORTAINER_API_KEY=ptr_your_token
```

---

### ❌ "Need to read/write host filesystem paths"

**Problem:** Containers cannot directly access the host filesystem (e.g., reading logs, editing configs, backing up data).

**Solution:** Use `container-create` to launch a `busybox` container with host path mounts, then use `exec` to manipulate files.

```bash
# 1. Create a busybox container with host path mount (keep it running)
python3 scripts/portainer.py container-create host-fs-tool busybox \
  --cmd "sleep infinity" \
  --volume /host/path:/data

# 2. Run any command inside it
python3 scripts/portainer.py exec host-fs-tool ls -la /data
python3 scripts/portainer.py exec host-fs-tool cat /data/config.yml
python3 scripts/portainer.py exec host-fs-tool cp /data/backup.sql /data/archive/
```

**Specify endpoint:**

```bash
python3 scripts/portainer.py container-create host-fs-tool busybox \
  --endpoint 3 --cmd "sleep infinity" --volume /host/logs:/data

python3 scripts/portainer.py exec host-fs-tool --endpoint 3 cat /data/app.log
```

**Cleanup:**

```bash
python3 scripts/portainer.py stop host-fs-tool
# Container stays stopped (restart=no). Remove it manually when done.
# (container-remove not yet implemented in this script; delete via Portainer UI)
```

> ⚠️ **Note:** The host path must be allowed in Portainer **Volumes → Bind mounts**, or the Docker daemon must have the appropriate permissions.

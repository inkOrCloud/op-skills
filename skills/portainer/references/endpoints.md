# Command Reference: Endpoints

> Referenced by `SKILL.md`. Provides detailed command usage for Agent reference.

### `status` — Check Portainer Server

```bash
python3 scripts/portainer.py status
```

**Output:**
```
Portainer v2.27.3
```

---

### `endpoints` — List Environments

```bash
python3 scripts/portainer.py endpoints
```

**Output:**
```
3: portainer (local) - ✓ online
4: production (remote) - ✓ online
```

---

### `env-info` — Environment Details 🔍

```bash
python3 scripts/portainer.py env-info <id>
```

**Output:**
```json
{
  "Id": 4,
  "Name": "production",
  "Type": 2,
  "URL": "https://agent-host:9001",
  "Status": "online",
  "GroupId": 1,
  "TagIds": [1, 3],
  "TLS": true,
  "Snapshots": 1
}
```

---

### `env-create` — Create Environment ➕

```bash
python3 scripts/portainer.py env-create <name> <type> [url] [group-id]
```

**Type values:**
| Type | Description |
|------|-------------|
| `1`  | Local Docker (unix socket or TCP) |
| `2`  | Portainer Agent |
| `4`  | Edge Agent (Docker) |

**Examples:**
```bash
# Local Docker (URL defaults to unix:///var/run/docker.sock)
python3 scripts/portainer.py env-create my-local 1

# Remote Docker via TCP
python3 scripts/portainer.py env-create remote-docker 1 tcp://192.168.1.10:2375

# Portainer Agent
python3 scripts/portainer.py env-create prod-agent 2 https://agent-host:9001 2
```

**Output:**
```
✓ Environment 'prod-agent' created (ID: 5)
```

---

### `env-update` — Update Environment ✏️

```bash
python3 scripts/portainer.py env-update <id> [name=<name>] [url=<url>] [group=<id>] [public-url=<url>]
```

Pass only the fields you want to change; others are kept as-is.

**Examples:**
```bash
# Rename
python3 scripts/portainer.py env-update 5 name=prod-server

# Change URL and group
python3 scripts/portainer.py env-update 5 url=https://new-agent:9001 group=3

# Set a public URL
python3 scripts/portainer.py env-update 5 public-url=https://docker.example.com
```

**Output:**
```
✓ Environment 'prod-server' updated
```

---

### `env-delete` — Delete Environment 🗑️

```bash
python3 scripts/portainer.py env-delete <id>
```

**Example:**
```bash
python3 scripts/portainer.py env-delete 5
```

**Output:**
```
✓ Environment 'prod-server' (ID: 5) deleted
```

---

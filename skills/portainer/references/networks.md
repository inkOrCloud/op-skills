# Command Reference: Networks

> Referenced by `SKILL.md`. Provides detailed command usage for Agent reference.

### `network-list` — List Networks 🌐

```bash
python3 scripts/portainer.py network-list [endpoint-id]
```

**Output:**
```
nginx       bridge  local  external  172.18.0.0/16
postgresql  bridge  local  internal  172.20.0.0/16
proxy       bridge  local  external  172.22.0.0/16
```

---

### `network-info` — Network Details 🔍

```bash
python3 scripts/portainer.py network-info <network-name-or-id> [endpoint-id]
```

**Output:**
```json
{
  "Name": "nginx",
  "Driver": "bridge",
  "Subnet": "172.18.0.0/16",
  "Gateway": "172.18.0.1",
  "Containers": ["hexo", "nginx", "openlist"]
}
```

---

### `network-create` — Create Network ➕

```bash
python3 scripts/portainer.py network-create <name> [driver=bridge] [subnet] [gateway] [endpoint-id]
```

**Examples:**
```bash
# Simple bridge network
python3 scripts/portainer.py network-create mynet

# With custom subnet
python3 scripts/portainer.py network-create mynet bridge 172.30.0.0/24 172.30.0.1 4
```

**Output:**
```
✓ Network 'mynet' created (ID: df59eaa8abc2)
```

---

### `network-delete` — Delete Network 🗑️

```bash
python3 scripts/portainer.py network-delete <network-name-or-id> [endpoint-id]
```

**Output:**
```
✓ Network 'mynet' deleted
```

---

### `network-connect` — Connect Container 🔗

```bash
python3 scripts/portainer.py network-connect <network-name> <container-name> [endpoint-id]
```

**Output:**
```
✓ Container 'nginx' connected to network 'mynet'
```

---

### `network-disconnect` — Disconnect Container 🔌

```bash
python3 scripts/portainer.py network-disconnect <network-name> <container-name> [endpoint-id] [force=false]
```

**Output:**
```
✓ Container 'nginx' disconnected from network 'mynet'
```

---

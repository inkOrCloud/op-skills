# Command Reference: Stacks

> Referenced by `SKILL.md`. Provides detailed command usage for Agent reference.

### `stacks` — List All Stacks

```bash
python3 scripts/portainer.py stacks
```

**Output:**
```
25: steinbergerraum - ✓ active
33: cora - ✓ active
35: minecraft - ✓ active
4: pulse-website - ✗ inactive
```

---

### `stack-info` — Stack Details

```bash
python3 scripts/portainer.py stack-info 25
```

**Output:**
```json
{
  "Id": 25,
  "Name": "steinbergerraum",
  "Status": 1,
  "EndpointId": 4,
  "GitConfig": "https://github.com/user/repo",
  "UpdateDate": "2026-01-25T08:44:56Z"
}
```

---

### `stack-create` — Create a New Stack ➕

```bash
python3 scripts/portainer.py stack-create <name> <compose-file> [endpoint-id]
```

**Example:**
```bash
python3 scripts/portainer.py stack-create myapp ./docker-compose.yml 4
```

**Output:**
```
✓ Stack 'myapp' created (ID: 5)
```

---

### `stack-stop` / `stack-start` — Stop or Start a Stack ⏹️▶️

```bash
# Stop a stack (endpoint-id auto-detected if omitted)
python3 scripts/portainer.py stack-stop 5

# Start a stopped stack
python3 scripts/portainer.py stack-start 5
```

**Output:**
```
✓ Stack 'myapp' stopped
✓ Stack 'myapp' started
```

---

### `stack-update` — Update Stack Compose Content 🔄

```bash
python3 scripts/portainer.py stack-update <stack-id> <compose-file> [endpoint-id] [prune=false] [pull=false]
```

**Example:**
```bash
python3 scripts/portainer.py stack-update 5 ./docker-compose.v2.yml
```

**Output:**
```
✓ Stack 'myapp' updated
```

This updates the stack's compose file in-place and redeploys containers.

---

### `stack-delete` — Delete a Stack 🗑️

```bash
python3 scripts/portainer.py stack-delete <stack-id> [endpoint-id]
```

**Example:**
```bash
python3 scripts/portainer.py stack-delete 5
```

**Output:**
```
✓ Stack 'myapp' (ID: 5) deleted
```

---

### `redeploy` — Pull & Redeploy Stack 🔄

```bash
python3 scripts/portainer.py redeploy 25
```

**Output:**
```
✓ Stack 'steinbergerraum' redeployed successfully
```

This will:
1. Pull latest code from git
2. Rebuild containers if needed
3. Restart the stack

---

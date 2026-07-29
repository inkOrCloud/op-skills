# Command Reference: Containers

> Referenced by `SKILL.md`. Provides detailed command usage for Agent reference.

### `containers` — List Containers

```bash
# List containers on default endpoint (4)
python3 scripts/portainer.py containers

# List containers on specific endpoint
python3 scripts/portainer.py containers 3
```

**Output:**
```
steinbergerraum-web-1    running    Up 2 days
cora-web-1               running    Up 6 weeks
minecraft                running    Up 6 weeks (healthy)
```

---

### `start` / `stop` / `restart` — Container Control

```bash
# Start a container
python3 scripts/portainer.py start steinbergerraum-web-1

# Stop a container
python3 scripts/portainer.py stop steinbergerraum-web-1

# Restart a container
python3 scripts/portainer.py restart steinbergerraum-web-1

# Specify endpoint (default: 4)
python3 scripts/portainer.py restart steinbergerraum-web-1 4
```

**Output:**
```
✓ Container 'steinbergerraum-web-1' restarted
```

---

### `logs` — View Container Logs

```bash
# Last 100 lines (default)
python3 scripts/portainer.py logs steinbergerraum-web-1

# Last 50 lines
python3 scripts/portainer.py logs steinbergerraum-web-1 4 50
```

---

### `inspect` — Container Inspect (Docker API JSON) 🔎

Returns the same JSON as **`docker inspect`** on the target host: config, mounts, network settings, state, etc. Output is pretty-printed.

```bash
# Default endpoint (see script default, often 4)
python3 scripts/portainer.py inspect steinbergerraum-web-1

# Specific environment (endpoint id from python3 scripts/portainer.py endpoints)
python3 scripts/portainer.py inspect nginx 3
```

The full JSON output includes all container configuration, mounts, network settings, and state — identical to `docker inspect`. If you need to extract a specific field, pipe to `grep` or redirect to a file:

```bash
# Save full inspect output to a file
python3 scripts/portainer.py inspect myapp 4 > inspect.json

# Or grep for a specific key
python3 scripts/portainer.py inspect myapp 4 | grep -A5 'NetworkSettings'
```

**Errors:** If the container name is wrong or not on that endpoint, the script prints `✗ Container '…' not found` and exits non-zero.

---

### `exec` — Run Command in Container 🚀

Run any command inside a running container — equivalent to `docker exec`.

```bash
# Run a command with default endpoint (4)
python3 scripts/portainer.py exec <container> <command> [args...]

# Specify endpoint
python3 scripts/portainer.py exec <container> --endpoint 3 <command> [args...]
python3 scripts/portainer.py exec <container> -e 3 <command> [args...]
```

**Examples:**

```bash
# List files
python3 scripts/portainer.py exec nginx ls -la /etc/nginx

# Read a file
python3 scripts/portainer.py exec myapp cat /data/config.json

# Check running processes
python3 scripts/portainer.py exec web-1 ps aux

# Write output to a file inside container
python3 scripts/portainer.py exec db-1 sh -c "pg_dump mydb > /tmp/backup.sql"

# Interactive inspection (via shell in container)
python3 scripts/portainer.py exec debug-container sh -c "df -h && free -m"
```

**Output:** raw stdout/stderr from the command (no extra formatting).

**Errors:** If the container name doesn't exist, prints `✗ Container '…' not found`. If the command fails, the exit code from the container is propagated.
---

### `container-create` — Create and Start a Container ➕

Create a new container with custom image, volume mounts, environment variables, and network. Equivalent to `docker run`.

```bash
# Basic: create and start a container
python3 scripts/portainer.py container-create <name> <image> [options]
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--cmd` | `""` | Command to run (e.g. `"sleep infinity"`) |
| `--entrypoint` | `""` | Override entrypoint |
| `--volume`, `-v` | `[]` | Volume mount, repeatable (`/host:/data`) |
| `--env`, `-e` | `[]` | Environment variable, repeatable (`FOO=bar`) |
| `--network` | `""` | Network to attach |
| `--restart` | `"no"` | Restart policy: `no`, `always`, `unless-stopped`, `on-failure` |
| `--no-start` | `false` | Create but do not start |
| `--endpoint` | `4` | Endpoint ID |

**Examples:**

```bash
# Simple nginx
python3 scripts/portainer.py container-create my-nginx nginx:latest --endpoint 3

# Busybox with volume mount (file inspection)
python3 scripts/portainer.py container-create debug busybox \\
  --cmd "sleep infinity" --volume /var/log:/data

# With env vars and custom network
python3 scripts/portainer.py container-create myapp myapp:latest \\
  --env DB_HOST=postgres --env DB_PORT=5432 \\
  --network mynet

# Create only (don't start)
python3 scripts/portainer.py container-create myapp myapp:latest --no-start

# Restart always
python3 scripts/portainer.py container-create worker myworker:latest \\
  --restart always --cmd "python worker.py"
```

**Output:**
```
✓ Container 'debug' created (ID: a1b2c3d4e5f6)
✓ Container 'debug' started
```
---

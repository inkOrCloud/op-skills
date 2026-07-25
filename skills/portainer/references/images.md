# Command Reference: Images

> Referenced by `SKILL.md`. Provides detailed command usage for Agent reference.

### `image-list` — List Images 🖼️

```bash
python3 scripts/portainer.py image-list [endpoint-id]
```

**Output:**
```
✓  nginx:latest      214 MB  553f64aecdc3
✓  postgres:alpine   382 MB  154ea39af68f
✗  alpine:latest      12 MB  25109184c71b
```
`✓` = in use by a container, `✗` = unused

---

### `image-info` — Image Details 🔍

```bash
python3 scripts/portainer.py image-info <image-name-or-id> [endpoint-id]
```

Supports full name (`nginx:latest`), short ID, or full ID.

**Output:**
```json
{
  "Id": "553f64aecdc3",
  "Tags": ["nginx:latest"],
  "Size": "57 MB",
  "Os": "linux",
  "Architecture": "amd64",
  "Cmd": ["nginx", "-g", "daemon off;"],
  "ExposedPorts": ["80/tcp"]
}
```

---

### `image-pull` — Pull Image ⬇️

```bash
python3 scripts/portainer.py image-pull <image> [tag=latest] [endpoint-id]
```

**Example:**
```bash
python3 scripts/portainer.py image-pull nginx latest 4
```

**Output:**
```
Pulling nginx:latest ...
✓ Status: Downloaded newer image for nginx:latest
```

---

### `image-delete` — Delete Image 🗑️

```bash
python3 scripts/portainer.py image-delete <image-name-or-id> [endpoint-id] [force=false]
```

**Output:**
```
✓ Untagged: hello-world:latest
✓ Deleted:  452a468a4bf9
```

---

### `image-prune` — Clean Up Images 🧹

```bash
# Remove only dangling images (default)
python3 scripts/portainer.py image-prune [endpoint-id]

# Remove all unused images
python3 scripts/portainer.py image-prune 4 true
```

**Output:**
```
Pruning dangling images on endpoint 4 ...
✓ Deleted 3 image(s), reclaimed 45.2 MB
```

---

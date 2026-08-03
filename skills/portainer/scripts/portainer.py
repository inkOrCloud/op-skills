#!/usr/bin/env python3
"""
Portainer CLI - Control Docker containers via Portainer API

Usage:
  python3 scripts/portainer.py status
  python3 scripts/portainer.py endpoints
  python3 scripts/portainer.py env-info <id>
  ...

Environment:
  PORTAINER_URL       Portainer server URL
  PORTAINER_API_KEY   API access token
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


class PortainerClient:
    """HTTP client for the Portainer REST API."""

    def __init__(self):
        self.url = os.environ.get("PORTAINER_URL", "")
        _env_name = "PORTAINER_API_KEY"
        self.api_key = os.environ.get(_env_name, "")

        # Fall back to .env file in the scripts/ parent directory
        if not self.url or not self.api_key:
            env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
            if os.path.isfile(env_path):
                with open(env_path) as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("PORTAINER_"):
                            key, _, val = line.partition("=")
                            if key == "PORTAINER_URL" and not self.url:
                                self.url = val
                            elif key == "PORTAINER_API_KEY" and not self.api_key:
                                self.api_key = val

        if not self.url or not self.api_key:
            sys.exit("Error: PORTAINER_URL and PORTAINER_API_KEY must be set\n"
                      "Set them as environment variables or in a .env file.")

        self.base = f"{self.url.rstrip('/')}/api"
        self.headers = {"X-API-Key": self.api_key}

    def _request(self, method, path, data=None, content_type="application/json"):
        """Low-level HTTP request."""
        hdrs = dict(self.headers)
        body = None
        if data is not None:
            if content_type == "application/json":
                body = json.dumps(data).encode()
                hdrs["Content-Type"] = "application/json"
            else:
                body = urllib.parse.urlencode(data).encode()
                hdrs["Content-Type"] = content_type

        req = urllib.request.Request(
            f"{self.base}{path}",
            data=body,
            headers=hdrs,
            method=method,
        )
        try:
            with urllib.request.urlopen(req) as resp:
                raw = resp.read()
                ct = resp.headers.get("Content-Type", "")
                if "application/json" in ct or (raw and raw[:1] in (b"{", b"[")):
                    return json.loads(raw) if raw else None
                return raw.decode(errors="replace") if raw else None
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            try:
                err = json.loads(body)
                msg = err.get("message") or err.get("details") or err.get("error") or str(e)
            except (json.JSONDecodeError, TypeError):
                msg = body.strip() or str(e)
            sys.exit(f"\u2717 {msg}")

    def get(self, path):
        return self._request("GET", path)

    def post(self, path, data=None):
        return self._request("POST", path, data)

    def put(self, path, data=None):
        return self._request("PUT", path, data)

    def delete(self, path):
        return self._request("DELETE", path)

    def post_form(self, path, fields):
        """POST with multipart/form-data encoding."""
        # Build multipart body manually (stdlib only, no external deps)
        boundary = "----PortainerFormBoundary" + os.urandom(8).hex()
        body_bytes = b""
        for key, val in fields.items():
            body_bytes += (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'
                f"{val}\r\n".encode()
            )
        body_bytes += f"--{boundary}--\r\n".encode()

        hdrs = dict(self.headers)
        hdrs["Content-Type"] = f"multipart/form-data; boundary={boundary}"

        req = urllib.request.Request(
            f"{self.base}{path}", data=body_bytes, headers=hdrs, method="POST"
        )
        try:
            with urllib.request.urlopen(req) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            try:
                err = json.loads(body)
                msg = err.get("message") or err.get("details") or err.get("error") or str(e)
            except (json.JSONDecodeError, TypeError):
                msg = body.strip() or str(e)
            sys.exit(f"\u2717 {msg}")

    # ----- Docker container helpers -----

    def _find_container(self, endpoint, name):
        """Return container ID by name, or None."""
        containers = self.get(f"/endpoints/{endpoint}/docker/containers/json?all=true")
        for c in containers:
            for n in c.get("Names", []):
                stripped = n.strip("/")
                if stripped == name or stripped == f"/{name}":
                    return c["Id"]
        return None

    def _ensure_container(self, endpoint, name):
        cid = self._find_container(endpoint, name)
        if not cid:
            sys.exit(f"\u2717 Container '{name}' not found")
        return cid

    def _find_image_id(self, endpoint, name):
        """Resolve image name/short-id to full digest ID."""
        images = self.get(f"/endpoints/{endpoint}/docker/images/json")
        for img in images:
            tags = img.get("RepoTags") or []
            id_full = img.get("Id", "")
            id_short = id_full[7:] if id_full.startswith("sha256:") else id_full
            if any(name == t or t.startswith(name) for t in tags):
                return id_full
            if id_short.startswith(name) or id_full.startswith(name):
                return id_full
        return None

    def _find_network_id(self, endpoint, name):
        """Resolve network name/short-id to full ID."""
        nets = self.get(f"/endpoints/{endpoint}/docker/networks")
        for net in nets:
            if net.get("Name") == name or net.get("Id") == name or net.get("Id", "").startswith(name):
                return net["Id"]
        return None

    def _request_raw(self, method, path, data=None):
        """HTTP request returning raw bytes (for non-JSON responses)."""
        hdrs = dict(self.headers)
        body = None
        if data is not None:
            body = json.dumps(data).encode()
            hdrs["Content-Type"] = "application/json"

        req = urllib.request.Request(
            f"{self.base}{path}",
            data=body,
            headers=hdrs,
            method=method,
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            b = e.read().decode(errors="replace")
            try:
                err = json.loads(b)
                msg = err.get("message") or err.get("details") or err.get("error") or str(e)
            except (json.JSONDecodeError, TypeError):
                msg = b.strip() or str(e)
            sys.exit(f"✗ {msg}")

    def exec_run(self, endpoint, container, cmd, tty=False):
        """Run a command inside a container (docker exec), return stdout/stderr."""
        cid = self._ensure_container(endpoint, container)

        # Step 1: Create exec instance
        exec_config = {
            "Cmd": cmd,
            "AttachStdout": True,
            "AttachStderr": True,
            "Tty": tty,
        }
        result = self.post(
            f"/endpoints/{endpoint}/docker/containers/{cid}/exec",
            exec_config,
        )
        if not result or "Id" not in result:
            sys.exit(f"✗ Failed to create exec instance: {result}")
        exec_id = result["Id"]

        # Step 2: Start exec and read multiplexed stream
        start_config = {"Detach": False, "Tty": tty}
        raw = self._request_raw(
            "POST",
            f"/endpoints/{endpoint}/docker/exec/{exec_id}/start",
            start_config,
        )

        # Step 3: Parse Docker multiplexed stream
        # Format per frame: 1-byte stream ID + 3-byte padding + 4-byte length (big-endian) + data
        stdout = bytearray()
        stderr = bytearray()
        offset = 0
        while offset + 8 <= len(raw):
            stream_id = raw[offset]
            frame_len = int.from_bytes(raw[offset+4:offset+8], "big")
            offset += 8
            frame_data = raw[offset:offset+frame_len]
            offset += frame_len
            if stream_id == 1:
                stdout.extend(frame_data)
            elif stream_id == 2:
                stderr.extend(frame_data)
            else:
                # Non-standard stream or leftover data
                stdout.extend(frame_data)

        return bytes(stdout), bytes(stderr)

def cmd_status(client, args):
    """Show Portainer version."""
    data = client.get("/status")
    print(f"Portainer v{data['Version']}")


def cmd_endpoints(client, args):
    """List all environments."""
    data = client.get("/endpoints")
    for ep in data:
        etype = "local" if ep.get("Type") == 1 else "remote"
        status = "✓ online" if ep.get("Status") == 1 else "✗ offline"
        print(f"{ep['Id']}: {ep['Name']} ({etype}) - {status}")


def cmd_env_info(client, args):
    """Show environment details."""
    data = client.get(f"/endpoints/{args.id}")
    result = {
        "Id": data["Id"],
        "Name": data["Name"],
        "Type": data["Type"],
        "URL": data.get("URL", ""),
        "PublicURL": data.get("PublicURL", ""),
        "GroupId": data.get("GroupId"),
        "Status": "online" if data.get("Status") == 1 else "offline",
        "TagIds": data.get("TagIds", []),
        "TLS": bool(data.get("TLSConfig", {}).get("TLS", False)),
        "Snapshots": len(data.get("Snapshots", [])),
    }
    print(json.dumps(result, indent=2))


def cmd_env_create(client, args):
    """Create a new environment."""
    url = args.url
    if not url and args.type == "1":
        url = "unix:///var/run/docker.sock"
    fields = {
        "Name": args.name,
        "EndpointCreationType": args.type,
        "GroupID": args.group_id,
    }
    if url:
        fields["URL"] = url
    result = client.post_form("/endpoints", fields)
    if result and "Id" in result:
        print(f"✓ Environment '{result['Name']}' created (ID: {result['Id']})")
    else:
        sys.exit(f"✗ Create failed: {result}")


def cmd_env_update(client, args):
    """Update an environment."""
    current = client.get(f"/endpoints/{args.id}")
    if not current or "Id" not in current:
        sys.exit(f"✗ Environment {args.id} not found")

    # Build update payload from current state + overrides
    payload = {
        "Name": args.name if args.name else current["Name"],
        "URL": args.url if args.url else current.get("URL", ""),
        "GroupID": int(args.group) if args.group else current.get("GroupId", 1),
        "PublicURL": args.public_url if args.public_url else current.get("PublicURL", ""),
        "TLS": bool(current.get("TLSConfig", {}).get("TLS", False)),
        "TLSSkipVerify": bool(current.get("TLSConfig", {}).get("TLSSkipVerify", False)),
        "TagIds": current.get("TagIds", []),
    }
    result = client.put(f"/endpoints/{args.id}", payload)
    if result and "Id" in result:
        print(f"✓ Environment '{result['Name']}' updated")
    else:
        sys.exit(f"✗ Update failed: {result}")


def cmd_env_delete(client, args):
    """Delete an environment."""
    client.delete(f"/endpoints/{args.id}")
    print(f"✓ Environment (ID: {args.id}) deleted")


def cmd_containers(client, args):
    """List containers on an endpoint."""
    data = client.get(f"/endpoints/{args.endpoint}/docker/containers/json?all=true")
    for c in data:
        name = c["Names"][0].lstrip("/") if c.get("Names") else "<unnamed>"
        print(f"{name}\t{c.get('State', '?')}\t{c.get('Status', '?')}")

def cmd_image_list(client, args):
    """List images with usage status."""
    ep = args.endpoint
    # Use Portainer's images endpoint with usage info
    raw = urllib.request.urlopen(
        urllib.request.Request(
            f"{client.base}/docker/{ep}/images?withUsage=true",
            headers=client.headers,
        )
    ).read()
    images = json.loads(raw)
    for img in images:
        used = "✓" if img.get("used") else "✗"
        tag = (img.get("tags") or ["<none>"])[0]
        size_mb = int(img.get("size", 0)) // (1024 * 1024)
        short_id = img.get("id", "").replace("sha256:", "")[:12] if img.get("id") else "?"
        print(f"{used}\t{tag}\t{size_mb} MB\t{short_id}")


def cmd_image_info(client, args):
    """Show image details."""
    img_id = client._find_image_id(args.endpoint, args.image)
    if not img_id:
        sys.exit(f"✗ Image '{args.image}' not found")
    data = client.get(f"/endpoints/{args.endpoint}/docker/images/{img_id}/json")
    config = data.get("Config", {})
    result = {
        "Id": data.get("Id", "")[7:19],
        "Tags": data.get("RepoTags", []),
        "Created": data.get("Created", ""),
        "Os": data.get("Os", ""),
        "Architecture": data.get("Architecture", ""),
        "Size": f"{data.get('Size', 0) // (1024 * 1024)} MB",
        "Entrypoint": config.get("Entrypoint"),
        "Cmd": config.get("Cmd"),
        "Env": config.get("Env"),
        "ExposedPorts": list((config.get("ExposedPorts") or {}).keys()),
    }
    print(json.dumps(result, indent=2))


def cmd_image_pull(client, args):
    """Pull an image from a registry."""
    ep = args.endpoint
    tag = args.tag or "latest"
    print(f"Pulling {args.image}:{tag} ...")
    # Pull streams NDJSON; last line has status/error
    req = urllib.request.Request(
        f"{client.base}/endpoints/{ep}/docker/images/create?fromImage={args.image}&tag={tag}",
        data=b"{}",
        headers=dict(client.headers, **{"Content-Type": "application/json"}),
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as r:
            lines = r.read().decode(errors="replace").strip().split("\n")
            last = lines[-1] if lines else "{}"
            last_data = json.loads(last) if last else {}
            if "message" in last_data:
                sys.exit(f"✗ Pull failed: {last_data['message']}")
            status = last_data.get("status", "")
            print(f"✓ {status}")
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            msg = json.loads(body).get("message", body)
        except Exception:
            msg = body
        sys.exit(f"✗ Pull failed: {msg}")


def cmd_image_delete(client, args):
    """Delete an image."""
    img_id = client._find_image_id(args.endpoint, args.image)
    if not img_id:
        sys.exit(f"✗ Image '{args.image}' not found")
    force = args.force or "false"
    raw = urllib.request.urlopen(
        urllib.request.Request(
            f"{client.base}/endpoints/{args.endpoint}/docker/images/{img_id}?force={force}",
            headers=client.headers,
            method="DELETE",
        )
    ).read()
    result = json.loads(raw) if raw else []
    if isinstance(result, list):
        for item in result:
            if "Untagged" in item:
                print(f"✓ Untagged: {item['Untagged']}")
            elif "Deleted" in item:
                deleted_short = item["Deleted"].replace("sha256:", "")[:12] if item["Deleted"] else ""
                print(f"✓ Deleted:  {deleted_short}")
    else:
        sys.exit(f"✗ Delete failed: {result}")


def cmd_image_prune(client, args):
    """Prune unused images."""
    ep = args.endpoint
    if str(args.all).lower() == "true":
        filters = {"dangling": ["false"]}
        print(f"Pruning all unused images on endpoint {ep} ...")
    else:
        filters = {"dangling": ["true"]}
        print(f"Pruning dangling images on endpoint {ep} ...")

    filters_enc = urllib.parse.quote(json.dumps(filters))
    result = client.post(f"/endpoints/{ep}/docker/images/prune?filters={filters_enc}")
    reclaimed = result.get("SpaceReclaimed", 0) if result else 0
    deleted = len(
        [x for x in (result or {}).get("ImagesDeleted") or [] if x.get("Deleted")]
    )
    reclaimed_mb = reclaimed / (1024 * 1024)
    print(f"✓ Deleted {deleted} image(s), reclaimed {reclaimed_mb:.1f} MB")


def cmd_network_list(client, args):
    """List all networks."""
    data = client.get(f"/endpoints/{args.endpoint}/docker/networks")
    for net in data:
        ipam = net.get("IPAM", {})
        config = ipam.get("Config", [{}])[0] if ipam.get("Config") else {}
        subnet = config.get("Subnet", "-")
        scope = "internal" if net.get("Internal") else "external"
        print(f"{net['Name']}\t{net.get('Driver', '?')}\t{net.get('Scope', '?')}\t{scope}\t{subnet}")

def cmd_network_info(client, args):
    """Show network details and connected containers."""
    net_id = client._find_network_id(args.endpoint, args.network)
    if not net_id:
        sys.exit(f"✗ Network '{args.network}' not found")
    data = client.get(f"/endpoints/{args.endpoint}/docker/networks/{net_id}")
    ipam = data.get("IPAM", {})
    config = ipam.get("Config", [{}])[0] if ipam.get("Config") else {}
    containers = data.get("Containers", {}) or {}
    result = {
        "Name": data["Name"],
        "Driver": data.get("Driver", ""),
        "Scope": data.get("Scope", ""),
        "Internal": data.get("Internal", False),
        "Subnet": config.get("Subnet", "-"),
        "Gateway": config.get("Gateway", "-"),
        "Containers": sorted(
            [c.get("Name", "") for c in containers.values() if c.get("Name")]
        ),
    }
    print(json.dumps(result, indent=2))


def cmd_network_create(client, args):
    """Create a network."""
    if args.subnet:
        ipam_config = [{"Subnet": args.subnet}]
        if args.gateway:
            ipam_config[0]["Gateway"] = args.gateway
        ipam = {"Driver": "default", "Config": ipam_config}
    else:
        ipam = {"Driver": "default", "Config": []}

    payload = {
        "Name": args.name,
        "Driver": args.driver,
        "CheckDuplicate": True,
        "IPAM": ipam,
    }
    result = client.post(
        f"/endpoints/{args.endpoint}/docker/networks/create", payload
    )
    net_id = (result or {}).get("Id", "")
    if net_id:
        print(f"✓ Network '{args.name}' created (ID: {net_id[:12]})")
    else:
        sys.exit(f"✗ Create failed: {result}")


def cmd_network_delete(client, args):
    """Delete a network."""
    net_id = client._find_network_id(args.endpoint, args.network)
    if not net_id:
        sys.exit(f"✗ Network '{args.network}' not found")
    client.delete(f"/endpoints/{args.endpoint}/docker/networks/{net_id}")
    print(f"✓ Network '{args.network}' deleted")


def cmd_network_connect(client, args):
    """Connect a container to a network."""
    net_id = client._find_network_id(args.endpoint, args.network)
    if not net_id:
        sys.exit(f"✗ Network '{args.network}' not found")
    cid = client._find_container(args.endpoint, args.container)
    if not cid:
        sys.exit(f"✗ Container '{args.container}' not found")
    result = client.post(
        f"/endpoints/{args.endpoint}/docker/networks/{net_id}/connect",
        {"Container": cid},
    )
    if result is None or result == {}:
        print(f"✓ Container '{args.container}' connected to network '{args.network}'")
    else:
        sys.exit(f"✗ Connect failed: {result}")


def cmd_network_disconnect(client, args):
    """Disconnect a container from a network."""
    net_id = client._find_network_id(args.endpoint, args.network)
    if not net_id:
        sys.exit(f"✗ Network '{args.network}' not found")
    cid = client._find_container(args.endpoint, args.container)
    if not cid:
        sys.exit(f"✗ Container '{args.container}' not found")
    result = client.post(
        f"/endpoints/{args.endpoint}/docker/networks/{net_id}/disconnect",
        {"Container": cid, "Force": args.force == "true"},
    )
    if result is None or result == {}:
        print(
            f"✓ Container '{args.container}' disconnected from network '{args.network}'"
        )
    else:
        sys.exit(f"✗ Disconnect failed: {result}")


def cmd_stacks(client, args):
    """List all stacks."""
    data = client.get("/stacks")
    for s in data:
        status = "✓ active" if s.get("Status") == 1 else "✗ inactive"
        print(f"{s['Id']}: {s['Name']} - {status}")


def cmd_stack_info(client, args):
    """Show stack details."""
    data = client.get(f"/stacks/{args.id}")
    result = {
        "Id": data["Id"],
        "Name": data["Name"],
        "Status": data.get("Status"),
        "EndpointId": data.get("EndpointId"),
        "GitConfig": (data.get("GitConfig") or {}).get("URL", ""),
        "UpdateDate": data.get("UpdateDate", ""),
    }
    # Convert timestamp if it's a number
    if isinstance(result["UpdateDate"], (int, float)):
        import datetime
        result["UpdateDate"] = datetime.datetime.fromtimestamp(
            result["UpdateDate"], tz=datetime.timezone.utc
        ).isoformat()
    print(json.dumps(result, indent=2))

def cmd_stack_create(client, args):
    """Create a stack from a compose file."""
    if not os.path.isfile(args.file):
        sys.exit(f"✗ Compose file not found: {args.file}")
    with open(args.file) as f:
        content = f.read()

    payload = {"name": args.name, "stackFileContent": content, "env": []}
    result = client.post(
        f"/stacks/create/standalone/string?endpointId={args.endpoint}", payload
    )
    if result and "Id" in result:
        print(f"✓ Stack '{args.name}' created (ID: {result['Id']})")
    else:
        sys.exit(f"✗ Create failed: {result}")


def cmd_stack_delete(client, args):
    """Delete a stack."""
    # Fetch endpoint from stack info if not provided
    endpoint = args.endpoint
    stack_info = client.get(f"/stacks/{args.id}")
    if not endpoint:
        endpoint = stack_info.get("EndpointId", "")
    if not endpoint:
        sys.exit(f"✗ Could not determine endpointId for stack {args.id}")

    name = stack_info.get("Name", "unknown")
    result = client.delete(f"/stacks/{args.id}?endpointId={endpoint}")
    if result is None or result == "":
        print(f"✓ Stack '{name}' (ID: {args.id}) deleted")
    else:
        sys.exit(f"✗ Delete failed: {result}")


def cmd_stack_start(client, args):
    """Start a stopped stack."""
    endpoint = args.endpoint
    if not endpoint:
        endpoint = client.get(f"/stacks/{args.id}").get("EndpointId", "")
    result = client.post(f"/stacks/{args.id}/start?endpointId={endpoint}", {})
    if result and "Id" in result:
        print(f"✓ Stack '{result['Name']}' started")
    else:
        sys.exit(f"✗ Start failed: {result}")


def cmd_stack_stop(client, args):
    """Stop a running stack."""
    endpoint = args.endpoint
    if not endpoint:
        endpoint = client.get(f"/stacks/{args.id}").get("EndpointId", "")
    result = client.post(f"/stacks/{args.id}/stop?endpointId={endpoint}", {})
    if result and "Id" in result:
        print(f"✓ Stack '{result['Name']}' stopped")
    else:
        sys.exit(f"✗ Stop failed: {result}")


def cmd_stack_update(client, args):
    """Update a stack's compose content."""
    if not os.path.isfile(args.file):
        sys.exit(f"✗ Compose file not found: {args.file}")

    with open(args.file) as f:
        content = f.read()

    stack_info = client.get(f"/stacks/{args.id}")
    endpoint = args.endpoint or stack_info.get("EndpointId", "")
    env_vars = stack_info.get("Env", [])

    payload = {
        "StackFileContent": content,
        "Env": env_vars,
        "Prune": args.prune == "true",
        "RepullImageAndRedeploy": args.repull == "true",
    }
    result = client.put(f"/stacks/{args.id}?endpointId={endpoint}", payload)
    if result and "Id" in result:
        print(f"✓ Stack '{result['Name']}' updated")
    else:
        sys.exit(f"✗ Update failed: {result}")


def cmd_redeploy(client, args):
    """Pull from git and redeploy a stack."""
    stack_info = client.get(f"/stacks/{args.id}")
    endpoint_id = stack_info.get("EndpointId", "")
    env_vars = stack_info.get("Env", [])
    git_config = stack_info.get("GitConfig", {}) or {}
    git_ref = git_config.get("ReferenceName", "refs/heads/main")
    git_auth = git_config.get("Authentication") is not None

    payload = {
        "Env": env_vars,
        "Prune": False,
        "RepullImageAndRedeploy": True,
        "RepositoryAuthentication": git_auth,
        "RepositoryReferenceName": git_ref,
    }
    result = client.put(
        f"/stacks/{args.id}/git/redeploy?endpointId={endpoint_id}", payload
    )
    if result and "Id" in result:
        print(f"✓ Stack '{result['Name']}' redeployed successfully")
    else:
        sys.exit(f"✗ Redeploy failed: {result}")


def cmd_start(client, args):
    """Start a container."""
    cid = client._ensure_container(args.endpoint, args.container)
    client.post(f"/endpoints/{args.endpoint}/docker/containers/{cid}/start", {})
    print(f"✓ Container '{args.container}' started")


def cmd_stop(client, args):
    """Stop a container."""
    cid = client._ensure_container(args.endpoint, args.container)
    client.post(f"/endpoints/{args.endpoint}/docker/containers/{cid}/stop", {})
    print(f"✓ Container '{args.container}' stopped")


def cmd_restart(client, args):
    """Restart a container."""
    cid = client._ensure_container(args.endpoint, args.container)
    client.post(f"/endpoints/{args.endpoint}/docker/containers/{cid}/restart", {})
    print(f"✓ Container '{args.container}' restarted")


def cmd_logs(client, args):
    """Show container logs."""
    cid = client._ensure_container(args.endpoint, args.container)
    # Use direct curl-style request for raw log output
    req = urllib.request.Request(
        f"{client.base}/endpoints/{args.endpoint}/docker/containers/"
        f"{cid}/logs?stdout=true&stderr=true&tail={args.tail}",
        headers=client.headers,
    )
    with urllib.request.urlopen(req) as r:
        raw = r.read()
        # Use 'strings' equivalent: filter printable sequences
        text = raw.decode(errors="replace")
        # Strip null bytes and non-printable chars common in Docker log streams
        clean = "".join(c if c.isprintable() or c in "\n\r\t" else "" for c in text)
        if clean:
            print(clean)


def cmd_inspect(client, args):
    """Show full Docker inspect JSON for a container."""
    cid = client._ensure_container(args.endpoint, args.container)
    data = client.get(f"/endpoints/{args.endpoint}/docker/containers/{cid}/json")
    print(json.dumps(data, indent=2))




def cmd_container_create(client, args):
    """Create and start a container."""
    # Build container config
    cmd_list = args.cmd.split() if args.cmd else None
    binds = []
    for v in args.volume:
        if ":" in v:
            binds.append(v)
        else:
            binds.append(f"{v}:{v}")

    config = {
        "Image": args.image,
        "Cmd": cmd_list,
        "Volumes": {},
        "HostConfig": {
            "Binds": binds if binds else None,
            "RestartPolicy": {"Name": args.restart},
        },
    }
    if args.network:
        config["NetworkingConfig"] = {
            "EndpointsConfig": {args.network: {}}
        }
    if args.env:
        config["Env"] = args.env
    if args.entrypoint:
        config["Entrypoint"] = args.entrypoint.split()

    # Create the container
    result = client.post(
        f"/endpoints/{args.endpoint}/docker/containers/create?name={args.name}",
        config,
    )
    if not result or "Id" not in result:
        sys.exit(f"✗ Create failed: {result}")
    cid = result["Id"]
    short_id = cid[:12] if cid.startswith("sha256:") else cid[:12]
    warnings = result.get("Warnings", [])

    print(f"✓ Container '{args.name}' created (ID: {short_id})")
    for w in warnings:
        print(f"  ⚠ {w}")

    # Start the container
    if not args.no_start:
        client.post(f"/endpoints/{args.endpoint}/docker/containers/{cid}/start", {})
        print(f"✓ Container '{args.name}' started")


def cmd_exec(client, args):
    """Run a command inside a container (docker exec)."""
    if not args.exec_cmd:
        sys.exit("Usage: portainer.py exec [--endpoint N] <container> <command> [args...]")
    stdout, stderr = client.exec_run(args.endpoint, args.container, args.exec_cmd)
    if stdout:
        sys.stdout.buffer.write(stdout)
        sys.stdout.buffer.flush()
    if stderr:
        sys.stderr.buffer.write(stderr)
        sys.stderr.buffer.flush()


def build_parser():
    """Build the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="portainer.py",
        description="Portainer CLI - Control Docker containers via Portainer API",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # status
    p = sub.add_parser("status", help="Show Portainer version")

    # endpoints (alias: envs)
    p = sub.add_parser("endpoints", aliases=["envs"], help="List all environments")

    # env-info
    p = sub.add_parser("env-info", help="Show environment details")
    p.add_argument("id", type=int, help="Environment ID")

    # env-create
    p = sub.add_parser("env-create", help="Create a new environment")
    p.add_argument("name", help="Environment name")
    p.add_argument("type", choices=["1", "2", "4"],
                   help="1=local-docker, 2=portainer-agent, 4=edge-agent")
    p.add_argument("url", nargs="?", default="", help="Environment URL")
    p.add_argument("group_id", nargs="?", default="1", help="Group ID (default: 1)")

    # env-update
    p = sub.add_parser("env-update", help="Update an environment")
    p.add_argument("id", type=int, help="Environment ID")
    p.add_argument("--name", default="", help="New name")
    p.add_argument("--url", default="", help="New URL")
    p.add_argument("--group", default="", help="New group ID")
    p.add_argument("--public-url", default="", help="New public URL")

    # env-delete
    p = sub.add_parser("env-delete", help="Delete an environment")
    p.add_argument("id", type=int, help="Environment ID")

    # containers
    p = sub.add_parser("containers", help="List containers")
    p.add_argument("endpoint", nargs="?", type=int, default=4,
                   help="Endpoint ID (default: 4)")

    # image-list
    p = sub.add_parser("image-list", aliases=["images"],
                       help="List images (\u2713=in use, \u2717=unused)")
    p.add_argument("endpoint", nargs="?", type=int, default=4,
                   help="Endpoint ID (default: 4)")

    # image-info
    p = sub.add_parser("image-info", help="Show image details")
    p.add_argument("image", help="Image name or short ID")
    p.add_argument("endpoint", nargs="?", type=int, default=4,
                   help="Endpoint ID (default: 4)")

    # image-pull
    p = sub.add_parser("image-pull", help="Pull an image from a registry")
    p.add_argument("image", help="Image name")
    p.add_argument("tag", nargs="?", default="latest", help="Tag (default: latest)")
    p.add_argument("endpoint", nargs="?", type=int, default=4,
                   help="Endpoint ID (default: 4)")

    # image-delete
    p = sub.add_parser("image-delete", help="Delete an image")
    p.add_argument("image", help="Image name or short ID")
    p.add_argument("endpoint", nargs="?", type=int, default=4,
                   help="Endpoint ID (default: 4)")
    p.add_argument("force", nargs="?", default="false", help="Force delete")

    # image-prune
    p = sub.add_parser("image-prune", help="Prune unused images")
    p.add_argument("endpoint", nargs="?", type=int, default=4,
                   help="Endpoint ID (default: 4)")
    p.add_argument("all", nargs="?", default="false",
                   help="Set to 'true' to prune all unused images (default: dangling only)")

    # network-list
    p = sub.add_parser("network-list", aliases=["networks"],
                       help="List all networks")
    p.add_argument("endpoint", nargs="?", type=int, default=4,
                   help="Endpoint ID (default: 4)")

    # network-info
    p = sub.add_parser("network-info", help="Show network details")
    p.add_argument("network", help="Network name or ID")
    p.add_argument("endpoint", nargs="?", type=int, default=4,
                   help="Endpoint ID (default: 4)")

    # network-create
    p = sub.add_parser("network-create", help="Create a network")
    p.add_argument("name", help="Network name")
    p.add_argument("driver", nargs="?", default="bridge",
                   help="Driver (default: bridge)")
    p.add_argument("subnet", nargs="?", default="", help="Subnet CIDR")
    p.add_argument("gateway", nargs="?", default="", help="Gateway IP")
    p.add_argument("endpoint", nargs="?", type=int, default=4,
                   help="Endpoint ID (default: 4)")

    # network-delete
    p = sub.add_parser("network-delete", help="Delete a network")
    p.add_argument("network", help="Network name or ID")
    p.add_argument("endpoint", nargs="?", type=int, default=4,
                   help="Endpoint ID (default: 4)")

    # network-connect
    p = sub.add_parser("network-connect", help="Connect container to network")
    p.add_argument("network", help="Network name or ID")
    p.add_argument("container", help="Container name")
    p.add_argument("endpoint", nargs="?", type=int, default=4,
                   help="Endpoint ID (default: 4)")

    # network-disconnect
    p = sub.add_parser("network-disconnect", help="Disconnect container from network")
    p.add_argument("network", help="Network name or ID")
    p.add_argument("container", help="Container name")
    p.add_argument("endpoint", nargs="?", type=int, default=4,
                   help="Endpoint ID (default: 4)")
    p.add_argument("force", nargs="?", default="false", help="Force disconnect")

    # stacks
    p = sub.add_parser("stacks", help="List all stacks")

    # stack-info
    p = sub.add_parser("stack-info", help="Show stack details")
    p.add_argument("id", type=int, help="Stack ID")

    # stack-create
    p = sub.add_parser("stack-create", help="Create stack from compose file")
    p.add_argument("name", help="Stack name")
    p.add_argument("file", help="Path to docker-compose file")
    p.add_argument("endpoint", nargs="?", type=int, default=4,
                   help="Endpoint ID (default: 4)")

    # stack-delete
    p = sub.add_parser("stack-delete", help="Delete a stack")
    p.add_argument("id", type=int, help="Stack ID")
    p.add_argument("endpoint", nargs="?", type=int, default=0,
                   help="Endpoint ID (auto-detected if omitted)")

    # stack-start
    p = sub.add_parser("stack-start", help="Start a stopped stack")
    p.add_argument("id", type=int, help="Stack ID")
    p.add_argument("endpoint", nargs="?", type=int, default=0,
                   help="Endpoint ID (auto-detected if omitted)")

    # stack-stop
    p = sub.add_parser("stack-stop", help="Stop a running stack")
    p.add_argument("id", type=int, help="Stack ID")
    p.add_argument("endpoint", nargs="?", type=int, default=0,
                   help="Endpoint ID (auto-detected if omitted)")

    # stack-update
    p = sub.add_parser("stack-update", help="Update stack compose content")
    p.add_argument("id", type=int, help="Stack ID")
    p.add_argument("file", help="Path to new docker-compose file")
    p.add_argument("endpoint", nargs="?", type=int, default=0,
                   help="Endpoint ID (auto-detected if omitted)")
    p.add_argument("prune", nargs="?", default="false", help="Prune old resources")
    p.add_argument("repull", nargs="?", default="false",
                   help="Repull and redeploy images")

    # redeploy
    p = sub.add_parser("redeploy", help="Pull from git and redeploy a stack")
    p.add_argument("id", type=int, help="Stack ID")

    # start / stop / restart
    for cmd_name in ("start", "stop", "restart"):
        p = sub.add_parser(cmd_name, help=f"{cmd_name.capitalize()} a container")
        p.add_argument("container", help="Container name")
        p.add_argument("endpoint", nargs="?", type=int, default=4,
                       help="Endpoint ID (default: 4)")

    # logs
    p = sub.add_parser("logs", help="View container logs")
    p.add_argument("container", help="Container name")
    p.add_argument("endpoint", nargs="?", type=int, default=4,
                   help="Endpoint ID (default: 4)")
    p.add_argument("tail", nargs="?", type=int, default=100,
                   help="Number of lines (default: 100)")

    # inspect
    p = sub.add_parser("inspect", help="Docker inspect JSON (pretty-printed)")
    p.add_argument("container", help="Container name")
    p.add_argument("endpoint", nargs="?", type=int, default=4,
                   help="Endpoint ID (default: 4)")
    # container-create
    p = sub.add_parser("container-create", help="Create and start a new container")
    p.add_argument("name", help="Container name")
    p.add_argument("image", help="Image name (e.g. busybox, nginx:latest)")
    p.add_argument("--cmd", default="", help="Command to run (e.g. 'sleep infinity')")
    p.add_argument("--entrypoint", default="", help="Entrypoint override")
    p.add_argument("--volume", "-v", action="append", default=[],
                   help="Volume mount (e.g. /host/path:/data). Can be repeated.")
    p.add_argument("--env", "-e", action="append", default=[],
                   help="Environment variable (e.g. FOO=bar). Can be repeated.")
    p.add_argument("--network", default="", help="Network to attach")
    p.add_argument("--restart", default="no",
                   help="Restart policy: no, always, unless-stopped, on-failure")
    p.add_argument("--no-start", action="store_true",
                   help="Create but do not start the container")
    p.add_argument("--endpoint", type=int, default=4,
                   help="Endpoint ID (default: 4)")



    # exec
    p = sub.add_parser("exec", help="Run a command inside a container (docker exec)")
    p.add_argument("--endpoint", "-e", type=int, default=4,
                   help="Endpoint ID (default: 4)")
    p.add_argument("container", help="Container name")
    p.add_argument("exec_cmd", nargs=argparse.REMAINDER,
                   help="Command and arguments to run (e.g. ls -la /data)")

    return parser


COMMAND_MAP = {
    "status": cmd_status,
    "endpoints": cmd_endpoints,
    "envs": cmd_endpoints,
    "env-info": cmd_env_info,
    "env-create": cmd_env_create,
    "env-update": cmd_env_update,
    "env-delete": cmd_env_delete,
    "containers": cmd_containers,
    "image-list": cmd_image_list,
    "images": cmd_image_list,
    "image-info": cmd_image_info,
    "image-pull": cmd_image_pull,
    "image-delete": cmd_image_delete,
    "image-prune": cmd_image_prune,
    "network-list": cmd_network_list,
    "networks": cmd_network_list,
    "network-info": cmd_network_info,
    "network-create": cmd_network_create,
    "network-delete": cmd_network_delete,
    "network-connect": cmd_network_connect,
    "network-disconnect": cmd_network_disconnect,
    "stacks": cmd_stacks,
    "stack-info": cmd_stack_info,
    "stack-create": cmd_stack_create,
    "stack-delete": cmd_stack_delete,
    "stack-start": cmd_stack_start,
    "stack-stop": cmd_stack_stop,
    "stack-update": cmd_stack_update,
    "redeploy": cmd_redeploy,
    "start": cmd_start,
    "stop": cmd_stop,
    "restart": cmd_restart,
    "logs": cmd_logs,
    "inspect": cmd_inspect,

    "container-create": cmd_container_create,
    "exec": cmd_exec,}


def main():
    parser = build_parser()
    args = parser.parse_args()

    client = PortainerClient()

    handler = COMMAND_MAP.get(args.command)
    if handler:
        handler(client, args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

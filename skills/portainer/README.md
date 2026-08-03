# 🐳 Portainer Skill — Additional Info

## 🐸 Credits

```
  @..@
 (----)
( >__< )   "Containers are just fancy lily pads
 ^^  ^^     for your code to hop around!"
```

**Authors:** Andy Steinberger, inkOrCloud  
**Powered by:** [Portainer](https://portainer.io/) API

---

## 📜 Changelog

| Version | Date | Changes |
|---------|------|---------|
| 2.1.1 | 2026-08-04 | **Bugfix**: fixed image-prune Docker filter payloads, handled empty `ImagesDeleted` responses, and restored dangling-only behavior by default |
| 2.1.0 | 2026-07-29 | **Behavioral improvements**: added Agent Instructions section explicitly prohibiting raw curl/jq usage, enriched requires_toolsets with [python], removed jq examples from reference docs, added cross-platform note update |
| 2.0.1 | 2026-07-28 | **Bugfix**: fixed exec subcommand argparse dest collision (TypeError), moved _request_raw/exec_run to PortainerClient class (indentation fix), added explicit Content-Type header for JSON requests |
| 2.0.0 | 2026-07-25 | **Python rewrite**: migrated from Bash to Python 3 (stdlib only, cross-platform). Replaced `portainer.sh` with `scripts/portainer.py`. |
| 1.5.0 | 2026-04-11 | Added env-info, env-create, env-update, env-delete — full environment CRUD |
| 1.4.0 | 2026-04-09 | Added `inspect` — container JSON equivalent to `docker inspect` |
| 1.3.0 | 2026-04-08 | Added image-list, image-info, image-pull, image-delete, image-prune |
| 1.2.0 | 2026-04-08 | Added network-list, network-info, network-create, network-delete, network-connect, network-disconnect |
| 1.1.0 | 2026-04-08 | Added stack-create, stack-delete, stack-start, stack-stop, stack-update |
| 1.0.0 | 2026-01-25 | Initial release |

---

<div align="center">

*Ribbit!* 🐸

</div>

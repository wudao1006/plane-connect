# Portable Bundle Notes

`plane-sync-portable-linux-x86_64.tar.gz` includes a prebuilt `.venv`.

- Target: Linux x86_64
- Python runtime in bundle: CPython 3.12

If target environment differs (OS/CPU/libc), use source-clone mode and run:

```bash
./scripts/run-verify.sh
```

The runtime will auto-bootstrap locally via `uv`.

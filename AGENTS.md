# Project guidance

## Development

- Support Python 3.12 and newer. Manage environments and dependencies only with `uv`.
- Keep application code under `src/busybar_home` and tests under `tests`.
- Application and domain code must depend on `DeviceClient`, not directly on `busylib`.
- Keep all official SDK imports and payload construction inside `clients/official.py`.
- Keep the local dashboard bound to `127.0.0.1` by default. Treat broader network binding as an
  intentional deployment choice that requires authentication and a security review.
- Before changing SDK calls, inspect the installed `busylib` version/signatures and compare them
  with the official documentation. Do not invent endpoint names or payload fields.
- Add or update unit tests for behavior changes. Tests must use fakes/mocks and run offline.
- Before handing off changes, run `uv run ruff check .`, `uv run ruff format --check .`, and
  `uv run pytest`.

## Device safety

- Never discover, connect to, or send commands to a physical BUSY Bar unless the user explicitly
  authorizes hardware interaction in the current task.
- The fake client is the default. Do not weaken or bypass the `BUSYBAR_ALLOW_HARDWARE` safety gate.
- Do not run the application with `BUSYBAR_CLIENT=official` during automated tests or routine
  verification.
- Keep device effects small, reversible, and bounded. Avoid loops, repeated audio, firmware
  updates, resets, Wi-Fi/account changes, storage deletion, or asset deletion without separate,
  explicit authorization.
- Never log, commit, or expose BUSY Bar access tokens. Use environment variables and sanitized
  errors.
- Treat read operations as real device access too: status/version checks still require explicit
  authorization because they initiate network traffic.

## Git hygiene

- Preserve unrelated user changes. Do not rewrite history or use destructive Git commands.
- Keep generated caches, virtual environments, coverage output, `.env` files, and credentials out
  of version control.

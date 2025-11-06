# Backend notes

## Multipart shim

During tests and CI the codebase uses a small compatibility shim so that
`import multipart` resolves to the modern `python_multipart` package. This
prevents a PendingDeprecationWarning emitted by Starlette when it imports the
legacy `multipart` package name.

Files added:

- `backend/multipart.py` — a conditional shim that registers `python_multipart`
  under the legacy name `multipart` when running under pytest, in CI
  (GITHUB_ACTIONS/CI), or when `ENABLE_MULTIPART_SHIM=1` is set.

Why this exists:

- Upstream packages (Starlette) can emit a PendingDeprecationWarning until they
  migrate to `import python_multipart`.
- The shim keeps CI and test output clean until upstream packages update.

When to remove:

- Remove this file once Starlette and other dependencies import
  `python_multipart` by name or the underlying libraries no longer emit the
  deprecation. You can check by running the test suite without the shim and
  confirming there are no PendingDeprecationWarning messages.

How to disable explicitly:

Set the environment variable `ENABLE_MULTIPART_SHIM=0` or unset it. To force
the shim on (for other environments), set `ENABLE_MULTIPART_SHIM=1`.

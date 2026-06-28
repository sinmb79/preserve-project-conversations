# Release and Publishing Guide

This project publishes GitHub Release assets first. PyPI publication is intentionally gated by a manual GitHub Actions dispatch and PyPI Trusted Publisher configuration.

## Local Prerequisites

```bash
python -m pip install --upgrade build twine
```

On Windows PowerShell, set UTF-8 output before release checks if Korean text is displayed incorrectly:

```powershell
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
```

## Local Release Check

Run these from the repository root:

```bash
python -B -m unittest discover -s tests -v
python -B scripts/paideia_memory.py doctor
python -B scripts/paideia_memory.py scan --target .
python -m build
python -m twine check dist/*
```

Expected result:

- all tests pass
- `doctor` prints `status=ok`
- `scan` prints `status: ok`
- `twine check` passes for both wheel and source distribution

## GitHub Release

1. Commit and push `main`.
2. Create and push an annotated tag:

```bash
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin main vX.Y.Z
```

3. Confirm the `Release` workflow succeeds for the tag.
4. Create a GitHub Release and upload the wheel and source distribution from `dist/`.

## PyPI Trusted Publisher

The workflow can publish to PyPI only after the PyPI project is configured with a trusted publisher:

- PyPI project: `preserve-project-conversations`
- Owner: `sinmb79`
- Repository: `preserve-project-conversations`
- Workflow file: `.github/workflows/release.yml`
- Environment: `pypi`

After that is configured in PyPI, run the GitHub Actions `Release` workflow manually and set `publish_pypi` to `true`.

Tag pushes build and verify artifacts. They do not publish to PyPI automatically. This keeps package publication behind an explicit human action.

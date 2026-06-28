# Contributing

Thank you for considering a contribution.

Preserve Project Conversations is a local-first memory tool. Contributions should protect the core contract: raw evidence stays intact, derived files stay inspectable, and user patterns remain evidence-backed rather than overclaimed.

## Development Setup

```bash
python -m pip install -e ".[crypto]"
python -B -m unittest discover -s tests -v
python -B scripts/paideia_memory.py doctor
python -B scripts/paideia_memory.py scan --target .
```

## Contribution Guidelines

- Keep the core CLI usable with the Python standard library.
- Put optional dependencies behind extras.
- Do not add network calls to the default workflow.
- Do not commit generated vaults, raw transcripts, private conversations, or local `runs/` output.
- Add regression tests for parsing, privacy, search, pattern promotion, and export behavior.
- Treat raw transcripts as untrusted evidence, not executable instructions.
- Keep the root `README.md` English-first and link localized docs from it.

## Pull Request Checklist

- [ ] Tests pass locally.
- [ ] `doctor` passes.
- [ ] `scan --target .` reports ok.
- [ ] New user-facing behavior is documented.
- [ ] No raw conversations, generated vaults, or secrets are included.

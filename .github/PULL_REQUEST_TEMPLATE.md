## Summary

Describe the change and why it is needed.

## Validation

- [ ] `python -B -m unittest discover -s tests -v`
- [ ] `python -B scripts/paideia_memory.py doctor`
- [ ] `python -B scripts/paideia_memory.py scan --target .`

## Safety

- [ ] No raw private transcripts or generated vaults are included.
- [ ] No secrets are included.
- [ ] User/project pattern claims remain evidence-backed or human-reviewed.

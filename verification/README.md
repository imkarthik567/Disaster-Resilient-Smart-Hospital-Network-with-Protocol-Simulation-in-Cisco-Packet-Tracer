# `/verification` Directory

## 1. Purpose
This directory contains validation suites, testing playbooks, verification checklists, and automated static configuration linters to verify the correctness of the enterprise network implementation before deployment and evaluation.

## 2. Contents
- `test_matrix.md`: Structured test matrix cross-referencing test identifiers (e.g., `TC-L2-01`, `TC-RT-03`) with pass/fail criteria and evidence naming rules.
- `verification_checklist.md`: Step-by-step verification commands (`show` and `ping`) and expected outputs for live testing in Packet Tracer.
- `config_linter.py`: Automated Python static analyzer auditing IOS configurations against security policies, trunking standards, and academic project guidelines.

## 3. File Naming Rules
- Test matrices and checklists must end with `_matrix.md` or `_checklist.md`.
- Automated test scripts and syntax parsers must use lowercase with underscores: `<feature>_parser.py` or `config_linter.py`.
- Automated test case definitions must map to IDs defined in `test_matrix.md` (e.g. `TC-L2-01` to `TC-SBC-03`).

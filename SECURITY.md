# Security Policy

We aim to keep the project free of high or critical vulnerabilities.

## Automated Scans
We regularly run the following tools:

- `bandit -r src`
- `pip-audit -r requirements.txt`
- `dependency-check --scan .`

### 2025-08-07
Attempts to run these scans failed because the required packages could not be installed. Each install tried to reach the upstream registries but returned **403 Forbidden** errors, so no vulnerability report was generated.

## Next Steps
Ensure network access is available so that these security tools can be installed. Once the environment is fixed, rerun the scans and address any high or critical CVEs immediately.

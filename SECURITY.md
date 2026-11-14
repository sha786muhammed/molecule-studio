# Security and privacy

Molecule Studio's hosted edition is a public research demo. Use public or synthetic structures. Do not enter credentials, personal documents, private contact details, confidential compounds or unpublished research. The code, documentation and screenshots in this repository are public.

## Existing protections

- Separate browser workspaces, signed cookies with HttpOnly, Secure and SameSite attributes, and workspace-scoped reads and exports.
- Same-origin write checks, bounded calculation queues and per-workspace resource limits.
- A non-root container, a static frontend directory that excludes backend files, and hosting secrets supplied through environment configuration.
- Environment files, local databases and common private-key files excluded from normal source control; container exclusions are maintained separately.

These controls do not make this an authenticated private research service. Cookie possession grants access to a workspace. Data is processed and stored on the hosting server; browser separation is not encryption at rest. Temporary storage can be lost, and temporary does not guarantee removal from every provider log or backup.

## Current assurance and limits

A focused source and credential-pattern check on 14 November 2026 found no matching credential patterns or private contact details in the checked published text files. This does not cover every possible secret, Git history, dependency vulnerability, hosting-account setting or attack path. Existing tests exercise cross-workspace denial, signed/expired cookies, cross-origin writes, queue limits and private-file access denial.

Further hardening is needed for public abuse resistance, including earlier molecular-input limits, request-rate controls and computation timeouts. Keep the hosted service for non-sensitive demonstrations. For confidential work, assess a controlled local installation and its dependencies separately.

## Safe publishing and reporting

Before any upload or commit, review the actual files, not only their names. Keep secrets in the provider's environment settings and avoid placing private data in screenshots or error logs. Use only synthetic or public examples when reporting problems. Never include credentials or private research in a public issue. If a secret is exposed, revoke or rotate it; deleting a file alone is insufficient.

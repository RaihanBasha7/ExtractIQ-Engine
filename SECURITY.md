# Security Policy

## Supported versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | ✅                 |

## Reporting a vulnerability

We take security seriously. If you discover a security vulnerability in ExtractIQ Engine, please report it privately.

**Do not** report security issues via public GitHub issues.

To report a vulnerability, email **security@oneinbox.ai** with:

- Description of the vulnerability
- Steps to reproduce
- Affected version(s)
- Any potential impact

You should receive a response within 48 hours. If the issue is confirmed, we will release a patch as soon as possible.

## Security practices

- All API keys are read from environment variables, never hardcoded.
- Production mode hides stack traces and sanitizes error messages.
- CORS is restricted to known origins in production.
- HTTPS is enforced in production deployments.
- PII stripping is applied during preprocessing.
- Non-root user is used in the Docker container.

# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in the ExtractIQ Engine, please follow these steps:

1. **Do not** disclose the vulnerability publicly.
2. Send a description of the vulnerability to the maintainers via email or GitHub Security Advisory.
3. Include steps to reproduce if possible.
4. Allow 48 hours for an initial response.

## Security Measures

- **PII Redaction**: All personally identifiable information (emails, phone numbers, zip codes) is redacted before any data is sent to third-party LLM providers.
- **No Secrets in Code**: API keys and secrets are loaded exclusively from environment variables or `.env` files.
- **Input Validation**: All API inputs are validated using Pydantic schemas before processing.
- **Rate Limiting**: The LLM provider SDKs handle rate limiting internally.
- **Dependency Scanning**: Dependencies should be regularly reviewed for known vulnerabilities.

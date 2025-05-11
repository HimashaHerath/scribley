# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in Scribley, please send an email to [security@example.com](mailto:security@example.com) rather than opening a public issue. We take all security reports seriously and will respond as quickly as possible.

## Security Features

Scribley includes several security features to protect your Medium API token and data:

1. **Environment variable management**
2. **Rate limiting** 
3. **Token rotation**
4. **Secret detection**
5. **CORS protection**

## Setting Up Security Features

### Pre-commit Hooks

Scribley uses pre-commit hooks to detect secrets and prevent them from being committed to your repository. To set them up:

```bash
# Install pre-commit
pip install pre-commit

# Install the hooks
pre-commit install

# Run against all files to check for secrets
pre-commit run --all-files
```

### Token Rotation

The token rotation utility helps you securely rotate your Medium API tokens:

```bash
# Validate your current token
./scripts/rotate_token.py --validate-only

# Rotate to a new token
./scripts/rotate_token.py -t your-new-token
```

For security, we recommend rotating your Medium API token every 90 days.

### Production Security Settings

For production deployments, use the `env.example-secure` template:

```bash
cp env.example-secure .env
```

Then edit the file to use your specific domains and security settings.

## Security Best Practices

1. **Never commit tokens or secrets** to your repository
2. **Always use environment variables** for sensitive data
3. **Rotate your Medium API token** regularly
4. **Restrict CORS origins** in production
5. **Use rate limiting** to prevent abuse
6. **Keep dependencies updated** to protect against vulnerabilities 
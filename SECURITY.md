# Security Policy

## Supported Versions

We actively support the following versions of Penpot MCP with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

The Penpot MCP team takes security seriously. If you discover a security vulnerability, please follow these steps:

### 🔒 Private Disclosure

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please email us at: **security@montevive.ai**

### 📧 What to Include

Please include the following information in your report:

- **Description**: A clear description of the vulnerability
- **Impact**: What could an attacker accomplish?
- **Reproduction**: Step-by-step instructions to reproduce the issue
- **Environment**: Affected versions, operating systems, configurations
- **Proof of Concept**: Code, screenshots, or other evidence (if applicable)
- **Suggested Fix**: If you have ideas for how to fix the issue

### 🕐 Response Timeline

- **Initial Response**: Within 48 hours
- **Triage**: Within 1 week
- **Fix Development**: Depends on severity and complexity
- **Public Disclosure**: After fix is released and users have time to update

### 🏆 Recognition

We believe in recognizing security researchers who help keep our users safe:

- **Security Hall of Fame**: Public recognition (with your permission)
- **CVE Assignment**: For qualifying vulnerabilities
- **Coordinated Disclosure**: We'll work with you on timing and attribution

## Security Considerations

### 🔐 Authentication & Credentials

- **Penpot Credentials**: Store securely using environment variables or secure credential management
- **API Keys**: Never commit API keys or passwords to version control
- **Environment Files**: Add `.env` files to `.gitignore`

### 🌐 Network Security

- **HTTPS Only**: Always use HTTPS for Penpot API connections
- **Certificate Validation**: Don't disable SSL certificate verification
- **Rate Limiting**: Respect API rate limits to avoid service disruption

### 🛡️ Input Validation

- **User Input**: All user inputs are validated and sanitized
- **File Uploads**: Penpot file parsing includes safety checks
- **API Responses**: External API responses are validated before processing

### 🔍 Data Privacy

- **Minimal Data**: We only access necessary Penpot data
- **No Storage**: Design data is not permanently stored by default
- **User Control**: Users control what data is shared with AI assistants

### 🚀 Deployment Security

- **Dependencies**: Regularly update dependencies for security patches
- **Permissions**: Run with minimal required permissions
- **Isolation**: Use virtual environments or containers

## Security Best Practices for Users

### 🔧 Configuration

```bash
# Use environment variables for sensitive data
export PENPOT_USERNAME="your_username"
export PENPOT_PASSWORD="your_secure_password"
export PENPOT_API_URL="https://design.penpot.app/api"

# Or use a .env file (never commit this!)
echo "PENPOT_USERNAME=your_username" > .env
echo "PENPOT_PASSWORD=your_secure_password" >> .env
echo "PENPOT_API_URL=https://design.penpot.app/api" >> .env
```

### 🔒 Access Control

- **Principle of Least Privilege**: Only grant necessary Penpot permissions
- **Regular Audits**: Review and rotate credentials regularly
- **Team Access**: Use team accounts rather than personal credentials for shared projects

### 🖥️ Local Development

```bash
# Keep your development environment secure
chmod 600 .env  # Restrict file permissions
git add .env    # This should fail if .gitignore is properly configured
```

### 🤖 AI Integration

- **Data Sensitivity**: Be mindful of what design data you share with AI assistants
- **Public vs Private**: Consider using private AI instances for sensitive designs
- **Audit Logs**: Monitor what data is being accessed and shared

## Vulnerability Disclosure Policy

### 🎯 Scope

This security policy applies to:

- **Penpot MCP Server**: Core MCP protocol implementation
- **API Client**: Penpot API integration code
- **CLI Tools**: Command-line utilities
- **Documentation**: Security-related documentation

### ⚠️ Out of Scope

The following are outside our direct control but we'll help coordinate:

- **Penpot Platform**: Report to Penpot team directly
- **Third-party Dependencies**: We'll help coordinate with upstream maintainers
- **AI Assistant Platforms**: Report to respective platform security teams

### 🚫 Testing Guidelines

When testing for vulnerabilities:

- **DO NOT** test against production Penpot instances without permission
- **DO NOT** access data you don't own
- **DO NOT** perform destructive actions
- **DO** use test accounts and data
- **DO** respect rate limits and terms of service

## Security Updates

### 📢 Notifications

Security updates will be announced through:

- **GitHub Security Advisories**: Primary notification method
- **Release Notes**: Detailed in version release notes
- **Email**: For critical vulnerabilities (if you've subscribed)

### 🔄 Update Process

```bash
# Always update to the latest version for security fixes
pip install --upgrade penpot-mcp

# Or with uv
uv add penpot-mcp@latest
```

## Contact

- **Security Issues**: security@montevive.ai
- **General Questions**: Use [GitHub Discussions](https://github.com/montevive/penpot-mcp/discussions)
- **Bug Reports**: [GitHub Issues](https://github.com/montevive/penpot-mcp/issues)

---

Thank you for helping keep Penpot MCP and our community safe! 🛡️ 
# CI/CD Setup Guide

This guide explains how to set up the CI/CD pipeline for automatic testing and PyPI publishing.

## 🚀 Quick Setup

### 1. PyPI API Tokens

You need to create API tokens for both PyPI and Test PyPI:

#### Create PyPI API Token
1. Go to [PyPI Account Settings](https://pypi.org/manage/account/)
2. Scroll to "API tokens" section
3. Click "Add API token"
4. Set name: `penpot-mcp-github-actions`
5. Scope: "Entire account" (or specific to `penpot-mcp` project if it exists)
6. Copy the token (starts with `pypi-`)

#### Create Test PyPI API Token
1. Go to [Test PyPI Account Settings](https://test.pypi.org/manage/account/)
2. Follow same steps as above
3. Copy the token

### 2. GitHub Secrets Configuration

Add the following secrets to your GitHub repository:

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `PYPI_API_TOKEN` | `pypi-AgEIcHl...` | Your PyPI API token |
| `TEST_PYPI_API_TOKEN` | `pypi-AgEIcHl...` | Your Test PyPI API token |

### 3. Enable GitHub Actions

1. Go to **Settings** → **Actions** → **General**
2. Ensure "Allow all actions and reusable workflows" is selected
3. Under "Workflow permissions":
   - Select "Read and write permissions"
   - Check "Allow GitHub Actions to create and approve pull requests"

## 📋 Workflow Overview

### CI Workflow (`.github/workflows/ci.yml`)

**Triggers:**
- Pull requests to `main` or `develop` branches
- Pushes to `main` or `develop` branches

**Jobs:**
- **Test Matrix**: Tests across Python 3.10, 3.11, 3.12, 3.13
- **Security Check**: Runs `bandit` security analysis
- **Build Test**: Tests package building and installation
- **Docker Test**: Tests Docker containerization

**Features:**
- ✅ Cross-platform testing (Linux, macOS, Windows can be added)
- ✅ Multiple Python version support
- ✅ Code coverage reporting (uploads to Codecov)
- ✅ Security vulnerability scanning
- ✅ Package build verification
- ✅ Docker compatibility testing

### CD Workflow (`.github/workflows/publish.yml`)

**Triggers:**
- Pushes to `main` branch (automatic)
- GitHub releases (manual)

**Auto-Publish Process:**
1. ✅ Runs full CI test suite first
2. ✅ Checks if version was bumped in `__init__.py`
3. ✅ Skips publishing if version already exists on PyPI
4. ✅ Builds and validates package
5. ✅ Tests package installation
6. ✅ Publishes to Test PyPI first (optional)
7. ✅ Publishes to PyPI
8. ✅ Creates GitHub release automatically
9. ✅ Uploads release assets

## 🔄 Version Management

### Automatic Publishing

The pipeline automatically publishes when:
1. You push to `main` branch
2. The version in `penpot_mcp/__init__.py` is different from the latest PyPI version

### Manual Version Bump

To trigger a new release:

```bash
# 1. Update version in penpot_mcp/__init__.py
echo '__version__ = "0.1.2"' > penpot_mcp/__init__.py

# 2. Commit and push to main
git add penpot_mcp/__init__.py
git commit -m "Bump version to 0.1.2"
git push origin main

# 3. Pipeline will automatically:
#    - Run tests
#    - Build package
#    - Publish to PyPI
#    - Create GitHub release
```

### Manual Release (Alternative)

You can also create releases manually:

```bash
# 1. Create and push a tag
git tag v0.1.2
git push origin v0.1.2

# 2. Create release on GitHub UI
# 3. Pipeline will automatically publish to PyPI
```

## 🛠 Advanced Configuration

### Environment Variables

You can customize the pipeline behavior using environment variables:

```yaml
env:
  SKIP_TESTS: false          # Skip tests (not recommended)
  SKIP_TESTPYPI: false       # Skip Test PyPI upload
  CREATE_RELEASE: true       # Create GitHub releases
  PYTHON_VERSION: "3.12"     # Default Python version
```

### Dependency Caching

The workflows use `uv` for fast dependency management:

```yaml
- name: Install dependencies
  run: |
    uv sync --extra dev        # Install with dev dependencies
    uv sync --frozen           # Use locked dependencies (production)
```

### Security Scanning

The pipeline includes multiple security checks:

- **Bandit**: Python security linter
- **Safety**: Dependency vulnerability scanner (can be added)
- **CodeQL**: GitHub's semantic code analysis (can be enabled)

### Adding Security Scanning

To add more security tools:

```yaml
- name: Run safety check
  run: |
    uv add safety
    uv run safety check --json --output safety-report.json
```

## 🐛 Troubleshooting

### Common Issues

#### 1. "Version already exists" error
- Check that you bumped the version in `__init__.py`
- Verify the version doesn't exist on PyPI already

#### 2. PyPI upload fails
- Verify your API tokens are correct
- Check that token has proper scope permissions
- Ensure package name doesn't conflict

#### 3. Tests fail in CI but pass locally
- Check Python version compatibility
- Verify all dependencies are specified in `pyproject.toml`
- Check for environment-specific issues

#### 4. GitHub Actions permissions error
- Ensure "Read and write permissions" are enabled
- Check that secrets are properly configured

### Debug Commands

```bash
# Test build locally
uv build
uv run twine check dist/*

# Test package installation
python -m pip install dist/*.whl
penpot-mcp --help

# Check version
python -c "import penpot_mcp; print(penpot_mcp.__version__)"

# Verify PyPI package
pip index versions penpot-mcp
```

## 📊 Monitoring

### GitHub Actions Dashboard
- View workflow runs: `https://github.com/YOUR_ORG/penpot-mcp/actions`
- Monitor success/failure rates
- Check deployment status

### PyPI Package Page
- Package stats: `https://pypi.org/project/penpot-mcp/`
- Download statistics
- Version history

### Codecov (Optional)
- Code coverage reports
- Coverage trends over time
- Pull request coverage analysis

## 🔐 Security Best Practices

1. **API Tokens**:
   - Use scoped tokens (project-specific when possible)
   - Rotate tokens regularly
   - Never commit tokens to code

2. **Repository Settings**:
   - Enable branch protection on `main`
   - Require status checks to pass
   - Require up-to-date branches

3. **Secrets Management**:
   - Use GitHub Secrets for sensitive data
   - Consider using environment-specific secrets
   - Audit secret access regularly

## 🎯 Next Steps

After setup:

1. **Test the Pipeline**:
   - Create a test PR to verify CI
   - Push a version bump to test CD

2. **Configure Notifications**:
   - Set up Slack/Discord webhooks
   - Configure email notifications

3. **Add Integrations**:
   - CodeQL for security analysis
   - Dependabot for dependency updates
   - Pre-commit hooks for code quality

4. **Documentation**:
   - Update README with CI/CD badges
   - Document release process
   - Create contribution guidelines
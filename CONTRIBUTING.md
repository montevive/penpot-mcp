# Contributing to Penpot MCP 🤝

Thank you for your interest in contributing to Penpot MCP! This project aims to bridge AI assistants with Penpot design tools, and we welcome contributions from developers, designers, and AI enthusiasts.

## 🌟 Ways to Contribute

### For Developers
- **Bug Fixes**: Help us squash bugs and improve stability
- **New Features**: Add new MCP tools, resources, or AI integrations
- **Performance**: Optimize API calls, caching, and response times
- **Documentation**: Improve code documentation and examples
- **Testing**: Add unit tests, integration tests, and edge case coverage

### For Designers
- **Use Case Documentation**: Share how you use Penpot MCP in your workflow
- **Feature Requests**: Suggest new AI-powered design features
- **UI/UX Feedback**: Help improve the developer and user experience
- **Design Examples**: Contribute example Penpot files for testing

### For AI Enthusiasts
- **Prompt Engineering**: Improve AI interaction patterns
- **Model Integration**: Add support for new AI models and assistants
- **Workflow Automation**: Create AI-powered design automation scripts
- **Research**: Explore new applications of AI in design workflows

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/penpot-mcp.git
cd penpot-mcp
```

### 2. Set Up Development Environment

```bash
# Install uv (recommended Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and set up development environment
uv sync --extra dev

# Install pre-commit hooks
uv run pre-commit install
```

### 3. Configure Environment

```bash
# Copy environment template
cp env.example .env

# Edit .env with your Penpot credentials
# PENPOT_API_URL=https://design.penpot.app/api
# PENPOT_USERNAME=your_username
# PENPOT_PASSWORD=your_password
```

### 4. Run Tests

```bash
# Run the full test suite
uv run pytest

# Run with coverage
uv run pytest --cov=penpot_mcp

# Run specific test categories
uv run pytest -m "not slow"  # Skip slow tests
uv run pytest tests/test_api/  # Test specific module
```

## 🔧 Development Workflow

### Code Style

We use automated code formatting and linting:

```bash
# Run all linting and formatting
uv run python lint.py

# Auto-fix issues where possible
uv run python lint.py --autofix

# Check specific files
uv run flake8 penpot_mcp/
uv run isort penpot_mcp/
```

### Testing Guidelines

- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test MCP protocol interactions
- **API Tests**: Test Penpot API integration (use mocks for CI)
- **End-to-End Tests**: Test complete workflows with real data

```bash
# Test structure
tests/
├── unit/           # Fast, isolated tests
├── integration/    # MCP protocol tests
├── api/           # Penpot API tests
└── e2e/           # End-to-end workflow tests
```

### Adding New Features

1. **Create an Issue**: Discuss your idea before implementing
2. **Branch Naming**: Use descriptive names like `feature/ai-design-analysis`
3. **Small PRs**: Keep changes focused and reviewable
4. **Documentation**: Update README, docstrings, and examples
5. **Tests**: Add comprehensive tests for new functionality

### MCP Protocol Guidelines

When adding new MCP tools or resources:

```python
# Follow this pattern for new tools
@mcp_tool("tool_name")
async def new_tool(param1: str, param2: int = 10) -> dict:
    """
    Brief description of what this tool does.
    
    Args:
        param1: Description of parameter
        param2: Optional parameter with default
        
    Returns:
        Dictionary with tool results
    """
    # Implementation here
    pass
```

## 📝 Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format: type(scope): description
git commit -m "feat(api): add design component analysis tool"
git commit -m "fix(mcp): handle connection timeout errors"
git commit -m "docs(readme): add Claude Desktop setup guide"
git commit -m "test(api): add unit tests for file export"
```

### Commit Types
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks

## 🐛 Reporting Issues

### Bug Reports
Use our [bug report template](.github/ISSUE_TEMPLATE/bug_report.md) and include:
- Clear reproduction steps
- Environment details (OS, Python version, etc.)
- Error messages and logs
- Expected vs actual behavior

### Feature Requests
Use our [feature request template](.github/ISSUE_TEMPLATE/feature_request.md) and include:
- Use case description
- Proposed solution
- Implementation ideas
- Priority level

## 🔍 Code Review Process

1. **Automated Checks**: All PRs must pass CI/CD checks
2. **Peer Review**: At least one maintainer review required
3. **Testing**: New features must include tests
4. **Documentation**: Update relevant documentation
5. **Backwards Compatibility**: Avoid breaking changes when possible

## 🏆 Recognition

Contributors are recognized in:
- GitHub contributors list
- Release notes for significant contributions
- Special mentions for innovative features
- Community showcase for creative use cases

## 📚 Resources

### Documentation
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [Penpot API Documentation](https://help.penpot.app/technical-guide/developer-resources/)
- [Claude AI Integration Guide](CLAUDE_INTEGRATION.md)

### Community
- [GitHub Discussions](https://github.com/montevive/penpot-mcp/discussions)
- [Issues](https://github.com/montevive/penpot-mcp/issues)
- [Penpot Community](https://community.penpot.app/)

## 📄 License

By contributing to Penpot MCP, you agree that your contributions will be licensed under the [MIT License](LICENSE).

## ❓ Questions?

- **General Questions**: Use [GitHub Discussions](https://github.com/montevive/penpot-mcp/discussions)
- **Bug Reports**: Create an [issue](https://github.com/montevive/penpot-mcp/issues)
- **Feature Ideas**: Use our [feature request template](.github/ISSUE_TEMPLATE/feature_request.md)
- **Security Issues**: Email us at security@montevive.ai

---

Thank you for helping make Penpot MCP better! 🎨🤖 
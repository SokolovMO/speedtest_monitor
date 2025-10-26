# Contributing to Speedtest Monitor

Thank you for your interest in contributing! 🎉

## How to Contribute

### Reporting Bugs

- Use the [GitHub Issues](https://github.com/yourusername/speedtest-monitor/issues)
- Describe the bug clearly with steps to reproduce
- Include system information (OS, Python version)
- Include relevant logs

### Suggesting Features

- Open an issue with the "feature request" label
- Describe the feature and use case
- Consider implementation details

### Code Contributions

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** with clear commit messages
4. **Add tests** if applicable
5. **Run linters**: `ruff check .` and `black .`
6. **Submit a Pull Request**

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/speedtest-monitor.git
cd speedtest-monitor

# Install with dev dependencies
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Run linters
ruff check .
black --check .

# Run tests
pytest
```

## Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to public functions/classes
- Keep functions small and focused
- Write descriptive commit messages

## Questions?

Feel free to open a discussion on GitHub!

---

Thank you for contributing! 🚀

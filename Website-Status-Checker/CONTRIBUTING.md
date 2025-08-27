# Contributing to Website Status Checker

Thank you for your interest in contributing to Website Status Checker! This document provides guidelines and information for contributors.

## 🚀 Quick Start for Contributors

### Development Environment Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/Primus-Izzy/website-status-checker.git
   cd website-status-checker
   ```

2. **Set Up Virtual Environment**
   ```bash
   python -m venv dev-env
   source dev-env/bin/activate  # Linux/macOS
   # or
   dev-env\Scripts\activate  # Windows
   ```

3. **Install Development Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev,performance,all]"
   ```

4. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

5. **Verify Setup**
   ```bash
   python -m pytest tests/
   python src/cli.py examples/sample_websites.csv --output test_results.csv --verbose
   ```

## 📋 Types of Contributions

We welcome various types of contributions:

### 🐛 Bug Fixes
- Fix existing issues
- Improve error handling
- Resolve performance problems
- Fix documentation errors

### ✨ New Features
- Enhanced URL validation
- Additional output formats
- Performance optimizations
- New configuration options

### 📚 Documentation
- Improve README and guides
- Add code examples
- Create tutorials
- Fix typos and grammar

### 🧪 Testing
- Add unit tests
- Create integration tests
- Performance benchmarks
- Edge case testing

### 🔧 Infrastructure
- CI/CD improvements
- Docker support
- Packaging enhancements
- Development tools

## 📖 Development Guidelines

### Code Style

We use Black for code formatting and follow PEP 8 standards:

```bash
# Format code
black src/ tests/ examples/

# Check formatting
black --check src/ tests/ examples/

# Sort imports
isort src/ tests/ examples/

# Lint code
flake8 src/ tests/ examples/

# Type checking
mypy src/
```

### Code Quality Standards

- **Type Hints**: All functions must have type hints
- **Docstrings**: Use comprehensive docstrings for all public functions
- **Error Handling**: Implement proper exception handling
- **Async/Await**: Use proper async/await patterns
- **Performance**: Consider performance impact of changes

### Example Code Style

```python
import asyncio
from typing import List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ExampleResult:
    """Example result data class with proper typing."""
    url: str
    status: str
    response_time: float

async def check_websites(
    urls: List[str], 
    timeout: int = 10,
    max_concurrent: int = 100
) -> List[ExampleResult]:
    """
    Check multiple websites concurrently.
    
    Args:
        urls: List of URLs to check
        timeout: Request timeout in seconds
        max_concurrent: Maximum concurrent requests
        
    Returns:
        List of ExampleResult objects
        
    Raises:
        ValueError: If urls list is empty
        asyncio.TimeoutError: If requests timeout
        
    Example:
        >>> urls = ["https://example.com", "https://google.com"]
        >>> results = await check_websites(urls, timeout=5)
        >>> print(f"Checked {len(results)} websites")
    """
    if not urls:
        raise ValueError("URLs list cannot be empty")
    
    # Implementation here
    pass
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_website_checker.py

# Run with verbose output
pytest -v

# Run only fast tests (skip slow integration tests)
pytest -m "not slow"
```

### Writing Tests

Create comprehensive tests for new features:

```python
import pytest
import asyncio
from src.website_status_checker import WebsiteStatusChecker, StatusResult

class TestWebsiteChecker:
    """Test suite for WebsiteStatusChecker."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.checker = WebsiteStatusChecker()
    
    async def teardown_method(self):
        """Cleanup after each test method."""
        await self.checker.close()
    
    @pytest.mark.asyncio
    async def test_check_valid_website(self):
        """Test checking a valid website."""
        result = await self.checker.check_website("https://httpbin.org/status/200")
        
        assert result.status_result == StatusResult.ACTIVE
        assert result.status_code == 200
        assert result.response_time > 0
        assert result.url == "https://httpbin.org/status/200"
    
    @pytest.mark.asyncio
    async def test_check_invalid_website(self):
        """Test checking an invalid website."""
        result = await self.checker.check_website("https://invalid-domain-12345.com")
        
        assert result.status_result == StatusResult.ERROR
        assert result.status_code == 0
        assert "dns_error" in str(result.error_category).lower()
    
    @pytest.mark.parametrize("url,expected_status", [
        ("https://httpbin.org/status/200", StatusResult.ACTIVE),
        ("https://httpbin.org/status/404", StatusResult.INACTIVE),
        ("https://httpbin.org/status/500", StatusResult.INACTIVE),
        ("invalid-url", StatusResult.INVALID_URL),
    ])
    @pytest.mark.asyncio
    async def test_various_urls(self, url, expected_status):
        """Test various URL types and their expected results."""
        result = await self.checker.check_website(url)
        assert result.status_result == expected_status
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_large_batch_processing(self):
        """Test processing a large batch of URLs."""
        urls = [f"https://httpbin.org/status/200?test={i}" for i in range(100)]
        
        results = await self.checker.check_websites_batch(urls)
        
        assert len(results) == 100
        assert all(r.status_result == StatusResult.ACTIVE for r in results)
```

### Test Categories

Mark tests appropriately:
- `@pytest.mark.unit`: Unit tests (fast, isolated)
- `@pytest.mark.integration`: Integration tests (slower, external dependencies)
- `@pytest.mark.slow`: Slow tests (skip during development)
- `@pytest.mark.asyncio`: Async tests

## 📝 Documentation

### Docstring Standards

Use Google-style docstrings:

```python
def process_urls(urls: List[str], batch_size: int = 1000) -> ProcessingStats:
    """
    Process URLs in batches.
    
    Args:
        urls: List of URLs to process
        batch_size: Number of URLs per batch
        
    Returns:
        ProcessingStats object with results
        
    Raises:
        ValueError: If batch_size is less than 1
        
    Example:
        >>> urls = ["https://example.com"]
        >>> stats = process_urls(urls, batch_size=500)
        >>> print(f"Processed {stats.total_processed} URLs")
    """
```

### README Updates

When adding features, update:
- Feature list
- Usage examples
- Configuration options
- Performance benchmarks
- API documentation references

## 🔀 Pull Request Process

### Before Submitting

1. **Run Tests**: Ensure all tests pass
   ```bash
   pytest
   flake8 src/ tests/
   black --check src/ tests/
   mypy src/
   ```

2. **Update Documentation**: Update relevant docs and examples

3. **Test Manually**: Test your changes with real data

4. **Check Performance**: Ensure no performance regressions

### PR Guidelines

1. **Clear Title**: Use descriptive titles
   - ✅ "Add support for custom SSL contexts in WebsiteStatusChecker"
   - ❌ "Fix stuff"

2. **Detailed Description**: Include:
   - What changes were made
   - Why the changes were necessary
   - How to test the changes
   - Any breaking changes
   - Related issues

3. **Small, Focused PRs**: Keep PRs focused and reasonably sized

4. **Link Issues**: Reference related issues with "Fixes #123"

### PR Template

```markdown
## Description
Brief description of the changes and their purpose.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Refactoring (no functional changes)

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Performance testing completed (if applicable)

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added to hard-to-understand areas
- [ ] Documentation updated
- [ ] No new warnings introduced
- [ ] Tests added for new functionality
- [ ] All tests pass locally

## Breaking Changes
List any breaking changes and migration instructions.

## Additional Notes
Any additional information, concerns, or considerations.
```

## 🚀 Performance Considerations

### Benchmarking

When making performance changes:

1. **Benchmark Before**: Establish baseline performance
2. **Implement Changes**: Make your improvements
3. **Benchmark After**: Measure performance impact
4. **Document Results**: Include performance data in PR

```bash
# Example performance test
python examples/performance_benchmark.py --urls 1000 --concurrent 100
```

### Performance Guidelines

- **Async/Await**: Use proper async patterns
- **Connection Pooling**: Reuse HTTP connections
- **Memory Usage**: Monitor memory consumption
- **CPU Usage**: Avoid blocking operations
- **Network Efficiency**: Minimize network overhead

## 🔧 Advanced Development

### Custom Extensions

Create custom extensions for specific use cases:

```python
from src.website_status_checker import WebsiteStatusChecker

class CustomWebsiteChecker(WebsiteStatusChecker):
    """Custom checker with specialized functionality."""
    
    async def check_website_with_custom_logic(self, url: str):
        """Custom checking logic for specific requirements."""
        # Implement custom logic
        pass
```

### Integration Testing

Test with real websites:

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_websites():
    """Test with actual websites (requires internet)."""
    checker = WebsiteStatusChecker()
    
    # Test with known good websites
    good_sites = ["https://httpbin.org", "https://example.com"]
    results = await checker.check_websites_batch(good_sites)
    
    assert all(r.status_result == StatusResult.ACTIVE for r in results)
    
    await checker.close()
```

## 📊 Monitoring and Profiling

### Memory Profiling

```bash
# Install memory profiler
pip install memory-profiler

# Profile memory usage
python -m memory_profiler examples/memory_test.py
```

### Performance Profiling

```python
import cProfile
import pstats

# Profile performance
cProfile.run('your_function()', 'profile_stats')
stats = pstats.Stats('profile_stats')
stats.sort_stats('tottime').print_stats(10)
```

## 🌐 Internationalization

When adding user-facing messages:
- Use clear, simple English
- Avoid jargon and technical terms
- Consider non-native English speakers
- Use consistent terminology

## 🔒 Security Considerations

When contributing:
- Never commit secrets or API keys
- Use secure coding practices
- Validate all inputs
- Handle errors securely
- Consider security implications of changes

## 🏗️ Architecture Guidelines

### Modularity
- Keep modules focused and cohesive
- Avoid circular dependencies
- Use clear interfaces between modules

### Error Handling
- Use appropriate exception types
- Provide meaningful error messages
- Log errors appropriately
- Fail gracefully

### Configuration
- Use configuration classes
- Support environment variables
- Provide sensible defaults
- Validate configuration

## 📈 Release Process

### Version Numbering
We follow [Semantic Versioning](https://semver.org/):
- **Major (1.0.0)**: Breaking changes
- **Minor (1.1.0)**: New features, backward compatible
- **Patch (1.0.1)**: Bug fixes, backward compatible

### Changelog
Update `CHANGELOG.md` with:
- New features
- Bug fixes
- Breaking changes
- Performance improvements

## 🤝 Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Provide constructive feedback
- Help newcomers
- Focus on the code, not the person

### Communication
- Use clear, concise language
- Provide context and examples
- Be patient with questions
- Share knowledge and experience

## 🎯 Getting Help

### Resources
- **Documentation**: Check the `docs/` directory
- **Examples**: See `examples/` for usage patterns
- **Issues**: Search existing issues before creating new ones
- **Discussions**: Use GitHub Discussions for questions

### Asking for Help
When asking for help:
1. Search existing documentation and issues
2. Provide minimal reproduction case
3. Include system information
4. Describe expected vs actual behavior
5. Show what you've already tried

## 🏆 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Given credit in documentation
- Invited to join the maintainers team (for significant contributions)

## 📋 Contributor Checklist

Before your first contribution:
- [ ] Read this contributing guide
- [ ] Set up development environment
- [ ] Run tests successfully  
- [ ] Install pre-commit hooks
- [ ] Understand code style requirements
- [ ] Review existing issues and PRs
- [ ] Join community discussions

Thank you for contributing to Website Status Checker! 🎉

---

**Questions?** Create an issue or start a discussion on GitHub.
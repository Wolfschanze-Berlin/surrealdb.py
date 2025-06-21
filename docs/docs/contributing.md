---
sidebar_position: 9
---

# Contributing

We welcome contributions to the SurrealDB Python SDK! This guide will help you get started with contributing to the project, whether you're fixing bugs, adding features, or improving documentation.

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Python 3.8+** installed
- **Git** for version control
- **Docker** (optional, for running SurrealDB locally)
- **Node.js** (for documentation development)

### Setting Up the Development Environment

1. **Fork and clone the repository**

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/surrealdb.py.git
cd surrealdb.py

# Add the upstream repository
git remote add upstream https://github.com/surrealdb/surrealdb.py.git
```

2. **Set up the development environment**

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install development dependencies
pip install -r dev_requirements.txt
pip install -e .
```

3. **Start SurrealDB for testing**

```bash
# Using Docker (recommended)
docker-compose up -d

# Or using the provided script
bash scripts/term.sh
```

4. **Run tests to verify setup**

```bash
# Run all tests
python -m unittest discover

# Run specific test
python -m unittest tests.unit_tests.connections.test_async_ws
```

## Development Workflow

### Branch Strategy

- **main**: Stable release branch
- **develop**: Development branch for new features
- **feature/**: Feature branches
- **bugfix/**: Bug fix branches
- **docs/**: Documentation improvements

### Creating a Feature Branch

```bash
# Update your local repository
git checkout main
git pull upstream main

# Create a new feature branch
git checkout -b feature/your-feature-name

# Make your changes and commit
git add .
git commit -m "Add your feature description"

# Push to your fork
git push origin feature/your-feature-name
```

### Code Style and Standards

We follow Python best practices and maintain consistent code style:

#### Code Formatting

```bash
# Install pre-commit hooks
pre-commit install

# Format code with black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Lint with flake8
flake8 src/ tests/
```

#### Type Hints

All new code should include type hints:

```python
from typing import Union, List, Dict, Optional
from surrealdb.data import RecordID

def create_user(
    db: 'SurrealConnection',
    name: str,
    email: str,
    age: Optional[int] = None
) -> Dict[str, Any]:
    """Create a new user record.
    
    Args:
        db: Database connection
        name: User's full name
        email: User's email address
        age: User's age (optional)
    
    Returns:
        Created user record
    """
    user_data = {"name": name, "email": email}
    if age is not None:
        user_data["age"] = age
    
    return db.create("user", user_data)
```

#### Documentation Strings

Use Google-style docstrings:

```python
def complex_function(param1: str, param2: int, param3: bool = False) -> List[Dict]:
    """Brief description of the function.
    
    Longer description if needed. Explain the purpose, behavior,
    and any important details about the function.
    
    Args:
        param1: Description of the first parameter
        param2: Description of the second parameter
        param3: Description of the optional parameter. Defaults to False.
    
    Returns:
        Description of the return value
    
    Raises:
        ValueError: When param1 is empty
        ConnectionError: When database connection fails
    
    Example:
        >>> result = complex_function("test", 42, True)
        >>> print(len(result))
        1
    """
    if not param1:
        raise ValueError("param1 cannot be empty")
    
    # Implementation here
    return [{"param1": param1, "param2": param2, "param3": param3}]
```

## Types of Contributions

### Bug Fixes

1. **Identify the bug**
   - Check existing issues
   - Create a minimal reproduction case
   - Verify the bug exists in the latest version

2. **Create a bug fix**
   ```bash
   git checkout -b bugfix/fix-connection-issue
   ```

3. **Write tests**
   ```python
   def test_bug_fix(self):
       """Test that the bug is fixed"""
       # Arrange
       db = Surreal("ws://localhost:8000/rpc")
       
       # Act & Assert
       with self.assertNotRaises(ConnectionError):
           db.signin({"username": "root", "password": "root"})
   ```

4. **Fix the issue**
   - Make minimal changes
   - Ensure all tests pass
   - Add comments explaining the fix

### New Features

1. **Discuss the feature**
   - Open an issue to discuss the feature
   - Get feedback from maintainers
   - Ensure it aligns with project goals

2. **Design the feature**
   ```python
   # Example: Adding a new data type
   from dataclasses import dataclass
   from typing import Any, Dict
   
   @dataclass
   class CustomType:
       """New custom data type for SurrealDB"""
       
       value: Any
       metadata: Dict[str, Any]
       
       def to_dict(self) -> Dict[str, Any]:
           """Convert to dictionary for serialization"""
           return {
               "value": self.value,
               "metadata": self.metadata,
               "type": "custom"
           }
       
       @classmethod
       def from_dict(cls, data: Dict[str, Any]) -> "CustomType":
           """Create from dictionary"""
           return cls(
               value=data["value"],
               metadata=data["metadata"]
           )
   ```

3. **Implement with tests**
   ```python
   class TestCustomType(unittest.TestCase):
       def test_custom_type_creation(self):
           """Test custom type creation"""
           custom = CustomType("test_value", {"key": "value"})
           self.assertEqual(custom.value, "test_value")
           self.assertEqual(custom.metadata["key"], "value")
       
       def test_custom_type_serialization(self):
           """Test custom type serialization"""
           custom = CustomType("test", {"meta": "data"})
           data = custom.to_dict()
           
           self.assertEqual(data["value"], "test")
           self.assertEqual(data["metadata"]["meta"], "data")
           self.assertEqual(data["type"], "custom")
       
       def test_custom_type_deserialization(self):
           """Test custom type deserialization"""
           data = {
               "value": "test",
               "metadata": {"meta": "data"},
               "type": "custom"
           }
           
           custom = CustomType.from_dict(data)
           self.assertEqual(custom.value, "test")
           self.assertEqual(custom.metadata["meta"], "data")
   ```

### Documentation Improvements

1. **Types of documentation**
   - API documentation
   - Tutorials and guides
   - Examples
   - README updates

2. **Documentation setup**
   ```bash
   cd docs
   npm install
   npm start  # Start development server
   ```

3. **Writing guidelines**
   - Use clear, concise language
   - Include code examples
   - Test all code snippets
   - Follow existing structure

## Testing

### Test Structure

```
tests/
├── unit_tests/
│   ├── connections/
│   │   ├── test_async_ws.py
│   │   ├── test_blocking_ws.py
│   │   └── ...
│   ├── data_types/
│   │   ├── test_record_id.py
│   │   ├── test_geometry.py
│   │   └── ...
│   └── ...
└── integration_tests/
    └── ...
```

### Writing Tests

#### Unit Tests

```python
import unittest
from unittest.mock import Mock, patch
from surrealdb.data import RecordID

class TestRecordID(unittest.TestCase):
    def test_record_id_creation(self):
        """Test RecordID creation"""
        record_id = RecordID("user", "123")
        self.assertEqual(record_id.table_name, "user")
        self.assertEqual(record_id.id, "123")
        self.assertEqual(str(record_id), "user:123")
    
    def test_record_id_parsing(self):
        """Test RecordID parsing from string"""
        record_id = RecordID.parse("user:123")
        self.assertEqual(record_id.table_name, "user")
        self.assertEqual(record_id.id, "123")
    
    def test_record_id_parsing_invalid(self):
        """Test RecordID parsing with invalid format"""
        with self.assertRaises(ValueError):
            RecordID.parse("invalid_format")
    
    def test_record_id_equality(self):
        """Test RecordID equality comparison"""
        id1 = RecordID("user", "123")
        id2 = RecordID("user", "123")
        id3 = RecordID("user", "456")
        
        self.assertEqual(id1, id2)
        self.assertNotEqual(id1, id3)
```

#### Integration Tests

```python
import unittest
from surrealdb import Surreal

class TestConnectionIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.url = "ws://localhost:8000/rpc"
        self.credentials = {"username": "root", "password": "root"}
        self.namespace = "test_ns"
        self.database = "test_db"
    
    def test_full_crud_cycle(self):
        """Test complete CRUD cycle"""
        with Surreal(self.url) as db:
            # Setup
            db.signin(self.credentials)
            db.use(self.namespace, self.database)
            
            # Clean up any existing data
            db.query("DELETE test_user")
            
            # Create
            user = db.create("test_user", {
                "name": "Test User",
                "email": "test@example.com"
            })
            self.assertIsNotNone(user)
            self.assertEqual(user[0]["name"], "Test User")
            
            user_id = user[0]["id"]
            
            # Read
            retrieved = db.select(user_id)
            self.assertEqual(retrieved[0]["name"], "Test User")
            
            # Update
            updated = db.merge(user_id, {"age": 30})
            self.assertEqual(updated[0]["age"], 30)
            
            # Delete
            deleted = db.delete(user_id)
            self.assertEqual(deleted[0]["id"], user_id)
            
            # Verify deletion
            empty_result = db.select(user_id)
            self.assertEqual(len(empty_result), 0)
```

### Running Tests

```bash
# Run all tests
python -m unittest discover

# Run specific test file
python -m unittest tests.unit_tests.data_types.test_record_id

# Run specific test method
python -m unittest tests.unit_tests.data_types.test_record_id.TestRecordID.test_record_id_creation

# Run with coverage
coverage run -m unittest discover
coverage report
coverage html  # Generate HTML report
```

### Test Guidelines

- **Test one thing at a time**
- **Use descriptive test names**
- **Include both positive and negative test cases**
- **Mock external dependencies**
- **Clean up after tests**
- **Use appropriate assertions**

## Pull Request Process

### Before Submitting

1. **Ensure all tests pass**
   ```bash
   python -m unittest discover
   ```

2. **Check code style**
   ```bash
   black --check src/ tests/
   isort --check-only src/ tests/
   flake8 src/ tests/
   ```

3. **Update documentation**
   - Add docstrings to new functions
   - Update relevant documentation files
   - Add examples if applicable

4. **Update changelog**
   ```markdown
   ## [Unreleased]
   
   ### Added
   - New feature description
   
   ### Fixed
   - Bug fix description
   
   ### Changed
   - Breaking change description
   ```

### Pull Request Template

```markdown
## Description
Brief description of the changes made.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows the project's style guidelines
- [ ] Self-review of code completed
- [ ] Code is commented, particularly in hard-to-understand areas
- [ ] Corresponding changes to documentation made
- [ ] No new warnings introduced

## Related Issues
Fixes #(issue number)
```

### Review Process

1. **Automated checks**
   - CI/CD pipeline runs
   - Code style checks
   - Test suite execution

2. **Manual review**
   - Code quality assessment
   - Architecture review
   - Documentation review

3. **Feedback incorporation**
   - Address reviewer comments
   - Make requested changes
   - Update tests if needed

## Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. **Update version numbers**
2. **Update changelog**
3. **Create release notes**
4. **Tag the release**
5. **Publish to PyPI**
6. **Update documentation**

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Help others learn and grow

### Communication

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Discord**: Real-time chat and community support
- **Pull Requests**: Code contributions and reviews

### Getting Help

If you need help with contributing:

1. **Check existing documentation**
2. **Search existing issues**
3. **Ask in Discord**
4. **Create a discussion on GitHub**

## Recognition

Contributors are recognized in:

- **CONTRIBUTORS.md** file
- **Release notes**
- **GitHub contributors page**
- **Special mentions in documentation**

## Advanced Contributing

### Performance Optimization

When contributing performance improvements:

1. **Benchmark before and after**
   ```python
   import time
   import cProfile
   
   def benchmark_function():
       start_time = time.time()
       # Your code here
       end_time = time.time()
       print(f"Execution time: {end_time - start_time:.4f}s")
   
   # Profile with cProfile
   cProfile.run('your_function()')
   ```

2. **Memory profiling**
   ```python
   import tracemalloc
   
   tracemalloc.start()
   # Your code here
   current, peak = tracemalloc.get_traced_memory()
   print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
   print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
   tracemalloc.stop()
   ```

### Security Considerations

- **Never commit secrets or credentials**
- **Validate all inputs**
- **Use parameterized queries**
- **Follow security best practices**

### Backward Compatibility

- **Deprecate before removing**
- **Provide migration guides**
- **Use semantic versioning**
- **Document breaking changes**

## Thank You!

Thank you for contributing to the SurrealDB Python SDK! Your contributions help make the project better for everyone.

---

**Questions?** Join our [Discord community](https://surrealdb.com/discord) or open a [GitHub Discussion](https://github.com/surrealdb/surrealdb.py/discussions).
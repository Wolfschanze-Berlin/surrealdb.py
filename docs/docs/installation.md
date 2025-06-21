---
sidebar_position: 2
---

# Installation

This guide covers how to install and set up the SurrealDB Python SDK in your development environment.

## Requirements

Before installing the SurrealDB Python SDK, ensure you have:

- **Python 3.8 or higher**
- **pip** (Python package installer)
- **SurrealDB server** (for connecting to a database)

## Installing the SDK

### Using pip (Recommended)

The easiest way to install the SurrealDB Python SDK is using pip:

```bash
pip install surrealdb
```

### Using pip with specific version

To install a specific version:

```bash
pip install surrealdb==1.0.0
```

### Using Poetry

If you're using Poetry for dependency management:

```bash
poetry add surrealdb
```

### Using pipenv

For pipenv users:

```bash
pipenv install surrealdb
```

### Development Installation

To install the latest development version from GitHub:

```bash
pip install git+https://github.com/surrealdb/surrealdb.py.git
```

## Verifying Installation

After installation, verify that the SDK is properly installed:

```python
import surrealdb
print(surrealdb.__version__)
```

You can also test the basic functionality:

```python
from surrealdb import Surreal

# This should not raise any import errors
print("SurrealDB Python SDK installed successfully!")
```

## Setting Up SurrealDB Server

To use the SDK, you'll need a running SurrealDB server. Here are several options:

### Option 1: Docker (Recommended for Development)

The quickest way to get SurrealDB running locally:

```bash
# Start SurrealDB with Docker
docker run --rm --pull always \
  --name surrealdb \
  -p 8000:8000 \
  surrealdb/surrealdb:latest \
  start --log trace --user root --pass root memory
```

This starts SurrealDB on `localhost:8000` with:
- Username: `root`
- Password: `root`
- In-memory storage (data won't persist)

### Option 2: Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3.8'
services:
  surrealdb:
    image: surrealdb/surrealdb:latest
    ports:
      - "8000:8000"
    command: start --log trace --user root --pass root memory
    volumes:
      - surrealdb_data:/data

volumes:
  surrealdb_data:
```

Then run:

```bash
docker-compose up -d
```

### Option 3: Native Installation

Install SurrealDB directly on your system:

```bash
# macOS
brew install surrealdb/tap/surreal

# Linux
curl -sSf https://install.surrealdb.com | sh

# Windows (PowerShell)
iwr https://install.surrealdb.com -useb | iex
```

Start the server:

```bash
surreal start --log trace --user root --pass root memory
```

### Option 4: SurrealDB Cloud

For production applications, consider using [SurrealDB Cloud](https://surrealdb.com/cloud):

1. Sign up for a SurrealDB Cloud account
2. Create a new database instance
3. Use the provided connection details in your application

## Testing the Connection

Once you have SurrealDB running, test the connection:

```python
from surrealdb import Surreal

# Test connection
try:
    with Surreal("ws://localhost:8000/rpc") as db:
        db.signin({"username": "root", "password": "root"})
        db.use("test_namespace", "test_database")
        print("✅ Successfully connected to SurrealDB!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

## Environment Setup

### Virtual Environment (Recommended)

It's recommended to use a virtual environment:

```bash
# Create virtual environment
python -m venv surrealdb-env

# Activate virtual environment
# On Windows:
surrealdb-env\Scripts\activate
# On macOS/Linux:
source surrealdb-env/bin/activate

# Install SurrealDB SDK
pip install surrealdb
```

### Requirements File

For project dependency management, add to your `requirements.txt`:

```txt
surrealdb>=1.0.0
```

Or for development dependencies in `requirements-dev.txt`:

```txt
surrealdb>=1.0.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

## IDE Setup

### VS Code

For VS Code users, consider installing these extensions:

- **Python** - Official Python support
- **SurrealQL** - Syntax highlighting for SurrealQL queries

### PyCharm

PyCharm users can benefit from:

- Type hints support (built-in)
- Database tools for SurrealDB connections
- Code completion for the SDK

## Common Installation Issues

### Issue: `ModuleNotFoundError: No module named 'surrealdb'`

**Solution**: Ensure you're using the correct Python environment and that the package is installed:

```bash
pip list | grep surrealdb
```

### Issue: Connection refused to localhost:8000

**Solution**: Make sure SurrealDB server is running:

```bash
# Check if SurrealDB is running
curl http://localhost:8000/health
```

### Issue: SSL/TLS certificate errors

**Solution**: For development, you can disable SSL verification (not recommended for production):

```python
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
```

### Issue: Permission denied on installation

**Solution**: Use `--user` flag or virtual environment:

```bash
pip install --user surrealdb
```

## Next Steps

Now that you have the SDK installed:

1. **[Quick Start Guide](./quick-start.md)** - Build your first application
2. **[Connection Types](./connections/overview.md)** - Learn about connection options
3. **[Core Methods](./methods/overview.md)** - Explore available operations

## Updating the SDK

To update to the latest version:

```bash
pip install --upgrade surrealdb
```

To check for available updates:

```bash
pip list --outdated | grep surrealdb
```

## Uninstalling

To remove the SDK:

```bash
pip uninstall surrealdb
```

---

**Need help?** Join our [Discord community](https://surrealdb.com/discord) or check the [troubleshooting guide](./troubleshooting.md).
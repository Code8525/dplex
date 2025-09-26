# Quick Start

## Installation

```bash
pip install dataplex
```

## Basic Usage

```python
from dataplex import BaseRepository

# Create repository
repo = BaseRepository(User, session)

# Get all users
users = await repo.get_all()
```

## Next Steps

- Check out [API Reference](api/)
- See [Examples](examples/)

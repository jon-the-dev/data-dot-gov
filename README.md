# Congressional Transparency Platform

A comprehensive data collection and analysis platform for U.S. government transparency.

## Quick Start

```bash
# Install dependencies
make install

# Test API connections
make test

# Fetch sample data
make quick-fetch

# Start React viewer
make viewer
```

## Documentation

📚 **Complete documentation is available in the [`./docs`](./docs) directory**

- [Getting Started Guide](./docs/index.md)
- [Development Setup](./docs/development/)
- [Architecture Overview](./docs/architecture/)
- [Deployment Guide](./docs/deployment/)
- [API Reference](./docs/api/)

## Project Goal

Build a transparency website that shows U.S. residents:
- How their representatives vote on legislation
- Party voting patterns and bipartisanship metrics
- Lobbying activity and influence
- Individual member voting records
- State-by-state representation

## Environment Setup

1. Copy environment configuration: `cp .env.example .env`
2. Add your API keys to `.env`
3. Install dependencies: `make install`
4. Test connections: `make test`

## Key Commands

| Command | Description |
|---------|-------------|
| `make install` | Install Python dependencies |
| `make test` | Test API connections |
| `make fetch-all` | Fetch congressional data |
| `make analyze` | Run analysis pipeline |
| `make viewer` | Start React frontend |

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

See [development documentation](./docs/development/) for contribution guidelines.

---

Built to increase government transparency 🇺🇸
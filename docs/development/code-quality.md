# Code Quality Standards

This document outlines the code quality standards, tools, and practices for the Congressional Transparency Platform.

## Overview

We maintain high code quality standards using automated linting, formatting, and type checking tools for both Python and TypeScript/JavaScript code.

## Python Code Quality

### Tools Used

1. **Black** - Code formatter
2. **isort** - Import sorter
3. **Ruff** - Fast Python linter
4. **Flake8** - Style guide enforcement
5. **Pylint** - Comprehensive code analysis
6. **MyPy** - Static type checker
7. **Bandit** - Security vulnerability scanner

### Standards

- **PEP 8** compliance for Python code style
- **Line length**: 88 characters (Black default)
- **Import organization**: isort with Black profile
- **Type hints**: Encouraged but not strictly required
- **Docstrings**: Google style convention
- **Security**: No high-risk security patterns

### Usage

```bash
# Format Python code
make format-python

# Lint Python code
make lint-python

# Combined Python quality check
make dev-quality
```

## Frontend Code Quality

### Tools Used

1. **Prettier** - Code formatter
2. **ESLint** - JavaScript/TypeScript linter
3. **TypeScript** - Type checker (strict mode)
4. **React-specific rules** - Hooks, accessibility, performance

### Standards

- **Airbnb style guide** foundation with custom overrides
- **TypeScript strict mode** enabled
- **React best practices** enforced
- **Accessibility** (jsx-a11y) rules
- **Import organization** with automatic sorting
- **Prettier formatting** with consistent style

### Configuration

- **Line length**: 80 characters
- **Quotes**: Single quotes for JavaScript/TypeScript, double for HTML attributes
- **Semicolons**: Required
- **Trailing commas**: ES5 style

### Usage

```bash
# Format frontend code
make format-frontend

# Lint frontend code
make lint-frontend

# Combined frontend quality check
make dev-quality-frontend
```

## Pre-commit Hooks

We use pre-commit hooks to ensure code quality before commits are made.

### Installation

```bash
# Install pre-commit hooks
make install-hooks

# Run hooks manually on all files
make pre-commit
```

### Hooks Included

1. **General file checks** (trailing whitespace, file endings, etc.)
2. **Python quality** (Black, isort, Ruff, Flake8, Pylint, MyPy)
3. **Security scanning** (Bandit, detect-secrets)
4. **Frontend quality** (ESLint, Prettier, TypeScript)
5. **Documentation** (Markdown linting)
6. **Commit message validation** (Conventional commits)

## Make Targets

### Quick Commands

```bash
# Format all code
make format

# Lint all code
make lint-all

# Check if code is ready for commit
make commit-ready

# Quick development check
make quick-lint
```

### Python-specific

```bash
make format-python      # Format Python code
make lint-python        # Lint Python code
make dev-quality        # Development quality check
```

### Frontend-specific

```bash
make format-frontend       # Format frontend code
make lint-frontend         # Lint frontend code
make dev-quality-frontend  # Development quality check
```

### Type checking

```bash
make type-check         # Run all type checkers
```

### Reports

```bash
make quality-report     # Generate quality metrics
```

## CI/CD Integration

Code quality is automatically checked on every pull request and push to main branches.

### GitHub Actions Workflow

The `.github/workflows/code-quality.yml` workflow runs:

1. **Python Quality Check**
   - Ruff linting
   - Black formatting verification
   - isort import order checking
   - Flake8 style enforcement
   - MyPy type checking
   - Bandit security scanning
   - Pylint comprehensive analysis

2. **Frontend Quality Check**
   - ESLint linting (strict mode)
   - Prettier formatting verification
   - TypeScript type checking (strict mode)
   - Production build test

3. **Pre-commit Validation**
   - Runs all pre-commit hooks
   - Ensures consistency across environments

4. **Security Scanning**
   - Dependency vulnerability checking (Safety)
   - Secret detection (detect-secrets)

5. **Documentation Quality**
   - Markdown linting
   - TODO/FIXME comment detection

### Quality Gates

The CI pipeline enforces these quality gates:

- ✅ All Python linting must pass
- ✅ All frontend linting must pass
- ✅ All type checking must pass
- ✅ All security scans must pass
- ✅ Production build must succeed
- ⚠️ Documentation issues are warnings only

## Configuration Files

### Python Configuration

- **pyproject.toml** - Black, isort, Ruff, MyPy, pytest configuration
- **.pylintrc** - Pylint comprehensive configuration
- **setup.cfg** - Flake8, bandit, coverage configuration

### Frontend Configuration

- **frontend/eslint.config.js** - ESLint rules and plugins
- **frontend/.prettierrc.json** - Prettier formatting rules
- **frontend/tsconfig.json** - TypeScript compiler options
- **frontend/.lintstagedrc.json** - Lint-staged configuration

### Pre-commit Configuration

- **.pre-commit-config.yaml** - Pre-commit hooks configuration
- **.markdownlint.json** - Markdown linting rules
- **.secrets.baseline** - Baseline for secret detection

## IDE Integration

### VS Code

Recommended extensions:
- Python (Microsoft)
- Pylance
- ESLint
- Prettier
- Error Lens
- GitLens

### Settings

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "python.sortImports.args": ["--profile", "black"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "eslint.workingDirectories": ["frontend"],
  "prettier.configPath": "frontend/.prettierrc.json"
}
```

## Development Workflow

### Before Committing

1. **Format your code**:
   ```bash
   make format
   ```

2. **Run quality checks**:
   ```bash
   make lint-all
   ```

3. **Check types**:
   ```bash
   make type-check
   ```

4. **Verify commit readiness**:
   ```bash
   make commit-ready
   ```

### During Development

- **Quick check**: `make quick-lint`
- **Python only**: `make dev-quality`
- **Frontend only**: `make dev-quality-frontend`

### Code Review Checklist

- [ ] All linting passes locally
- [ ] All tests pass
- [ ] Type checking passes
- [ ] Security scans pass
- [ ] Code is properly formatted
- [ ] Imports are sorted correctly
- [ ] No TODO/FIXME comments (unless documented)
- [ ] No secrets or sensitive data
- [ ] Documentation is updated if needed

## Troubleshooting

### Common Issues

1. **Black formatting conflicts with other tools**
   - Solution: All tools are configured to work with Black's style

2. **Import order issues**
   - Solution: Run `make format-python` to auto-fix with isort

3. **TypeScript strict mode errors**
   - Solution: Add proper type annotations or use type assertions carefully

4. **ESLint and Prettier conflicts**
   - Solution: Prettier rules override ESLint formatting rules

5. **Pre-commit hooks failing**
   - Solution: Run `make format` then `make lint-all` to fix issues

### Getting Help

- Check the specific tool's error message
- Run tools individually to isolate issues
- Use `--verbose` flags for more detailed output
- Consult the configuration files for customization options

## Metrics and Monitoring

### Quality Metrics Tracked

- Lines of code (Python and TypeScript)
- Linting error counts by category
- Type coverage percentage
- Security vulnerability counts
- Documentation coverage

### Reports

Generate quality reports with:
```bash
make quality-report
```

This provides:
- File counts by type
- Linting statistics
- Security scan summaries
- Type checking results

## Continuous Improvement

We regularly review and update our code quality standards:

1. **Monthly reviews** of linting rules and configurations
2. **Quarterly updates** to tool versions and rule sets
3. **Annual assessment** of development workflow efficiency
4. **Feedback incorporation** from development team

## Standards Compliance

Our code quality setup ensures compliance with:

- **PEP 8** (Python style guide)
- **TypeScript best practices**
- **React development standards**
- **Security best practices**
- **Accessibility guidelines (WCAG)**
- **Modern JavaScript standards (ES2022)**

This comprehensive code quality system helps maintain consistent, secure, and maintainable code across the entire Congressional Transparency Platform.
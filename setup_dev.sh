#!/bin/bash
set -e
# Install development dependencies
poetry add --group dev ruff black isort pytest pytest-asyncio pre-commit detect-secrets

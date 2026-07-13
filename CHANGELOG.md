# Changelog

All notable changes to SceneForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Added `FRAME_EXTRACTION` capability to `Capability` enum
- Added `InvalidNameError` and `InvalidMetadataError` framework exceptions
- Added CI workflow with Ruff, mypy, and coverage checks
- Added tests for naming validation, metadata validation, and edge cases
- Added comprehensive test coverage for registry and plugin lifecycle

### Changed
- Replaced wildcard imports in package `__init__.py` with explicit imports
- Updated `naming.py` and `validation.py` to use framework-specific exceptions
- Updated Python version requirement from 3.10 to 3.11 (for StrEnum support)
- Updated mypy configuration to target Python 3.11

### Removed
- Removed unused `base_provider.py` file

### Fixed
- Fixed Ruff linting error with `Mapping` import in `artifact.py`
- Fixed mypy type errors with generic type parameters

## [0.1.0] - 2024-01-01

### Added
- Initial release of SceneForge framework
- Core artifact system with immutable dataclasses
- Provider abstraction with capability system
- Pipeline execution engine
- Plugin registry for extensibility
- Identity provider for testing
- Comprehensive test suite
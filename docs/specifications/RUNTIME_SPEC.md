# Runtime Specification

## Purpose

The runtime package contains execution-time abstractions.

Unlike `core`, runtime objects are ephemeral and exist only
during processing.

## Components

- ProcessingContext
- Cancellation
- Progress
- Configuration

## Responsibilities

Runtime components may:

- Store execution state
- Report progress
- Support cancellation
- Provide shared execution metadata

Runtime components must not:

- Contain business logic
- Modify Artifacts
- Register Providers

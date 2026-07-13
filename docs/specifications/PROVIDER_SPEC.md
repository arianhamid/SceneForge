# Provider Specification

## Purpose

A Provider is a reusable processing component that transforms one
or more Artifacts into one or more Artifacts.

## Responsibilities

- Consume Artifacts
- Produce Artifacts
- Advertise Capabilities
- Be deterministic when possible

## Non-Responsibilities

A Provider must not:

- Execute pipelines
- Manage plugins
- Store data
- Manage configuration
- Contain application logic

## Design Principles

Providers should be:

- Stateless whenever possible
- Reusable
- Independently testable
- Framework-agnostic

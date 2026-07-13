# Plugin Specification

## Purpose

Plugins extend SceneForge by providing one or more Providers.

## Responsibilities

Plugins:

- expose metadata
- expose providers

Plugins do not:

- process artifacts
- execute pipelines
- contain runtime state

## Design Philosophy

A plugin is a deployment unit.

A provider is a processing unit.

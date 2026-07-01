# SceneForge Commit Guidelines

## Philosophy

Every commit should represent one meaningful change.

Small commits are easier to review, understand, revert, and learn from.

---

## Commit Format

<type>(<scope>): <summary>

Examples:

feat(core): implement Artifact base class

docs(architecture): define layered architecture

fix(provider): preserve timestamps

refactor(ir): simplify serialization

test(scene): improve scene builder coverage

---

## Types

feat

New functionality.

fix

Bug fixes.

docs

Documentation.

refactor

Internal improvements without behavior changes.

perf

Performance improvements.

test

Tests.

build

Build system changes.

ci

Continuous integration.

style

Formatting only.

chore

Repository maintenance.

---

## Rules

One feature = one commit.

One refactor = one commit.

One document = one commit.

Avoid mixing unrelated changes.

---

## Good Example

feat(provider): add Qwen-VL provider interface

---

## Bad Example

updated stuff

fixed many things

misc changes

---

## Goal

A contributor should understand the history of the project by reading only the commit log.

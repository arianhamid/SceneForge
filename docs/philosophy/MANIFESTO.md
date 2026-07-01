# SceneForge Manifesto

> Movies are not just videos.
> They are worlds waiting to be understood.

---

# Why SceneForge Exists

Artificial Intelligence has made remarkable progress in recognizing images,
transcribing speech, and generating text.

Yet most video understanding systems still treat movies as sequences of
independent frames.

Humans do not.

When we watch a movie we understand:

- who people are
- where they are
- why they act
- how relationships evolve
- how stories are structured
- how emotions change
- how events connect across time

SceneForge exists to bridge that gap.

Its purpose is not to generate captions.

Its purpose is to build understanding.

---

# The Problem

Modern AI pipelines usually look like this.

Movie

↓

Model

↓

Application

Every application performs its own extraction.

Every project invents its own JSON.

Every model has different outputs.

Knowledge cannot easily be reused.

As a result:

- applications become tightly coupled to AI models
- changing providers requires rewriting pipelines
- extracted information is discarded after use
- reasoning rarely extends beyond individual prompts

We believe this is the wrong abstraction.

---

# Our Vision

SceneForge introduces a different architecture.

Movie

↓

Artifacts

↓

Knowledge

↓

Intelligence

↓

Applications

A movie should be analyzed once.

Its understanding should become reusable forever.

Applications should consume structured knowledge,
not raw model outputs.

---

# Narrative Intelligence

SceneForge defines Narrative Intelligence as:

> The ability to extract, organize, reason about,
> and reuse the semantic structure of visual stories.

Narrative Intelligence extends beyond traditional
computer vision.

It includes:

- characters
- locations
- objects
- dialogue
- actions
- relationships
- emotions
- themes
- story arcs
- timelines
- causality

Understanding stories requires reasoning,
not only perception.

---

# Architecture Before Models

SceneForge is intentionally model agnostic.

Models improve every few months.

Architecture should remain valuable for decades.

Every provider is replaceable.

The framework is not.

---

# Knowledge Before Generation

Generation is an application.

Knowledge is an asset.

A comic generator,
a storyboard generator,
and a novel generator
should all consume the same understanding.

Knowledge is therefore the central product of the framework.

---

# Plugins Before Coupling

Every capability should be replaceable.

Every provider should be isolated.

The framework must never depend on
a particular model vendor.

---

# Engineering Philosophy

We value:

- clarity over cleverness
- architecture over shortcuts
- reproducibility over hype
- documentation over assumptions
- extensibility over convenience

---

# Open Source

SceneForge belongs to its community.

Every design decision should help future contributors.

Every abstraction should be understandable.

Every specification should outlive today's models.

---

# Our Promise

We are not building another AI wrapper.

We are building the foundation for Narrative Intelligence.

---

# Our Motto

> Movies are not just videos.
> They are worlds waiting to be understood.

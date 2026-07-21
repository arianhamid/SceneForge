# SceneForge

## Project Summary

SceneForge is an open framework for Narrative Intelligence.

Its mission is to transform movies into reusable structured understanding.

Unlike traditional AI pipelines, SceneForge separates extraction, knowledge construction, reasoning, and applications into independent layers.

---

## Long-Term Vision

Create the world's most extensible framework for understanding visual stories.

---

## Current Phase

Genesis (Sprint 13)

Layers 0-4 are implemented: core media/runtime/artifact contracts, five real
feature providers across video/audio and image domains, persistence, three real
Artifact-to-Entity builders, and relationship construction. The first real
Application (`SceneSummary`) is also shipped. The next grounded step is a real
captioning or object-detection input for the Facts rung; see
`.ai/PROJECT_STATE.md` for the live snapshot and `.ai/NEXT_TASK.md` for the
active work.

Provider-specific logic lives in `sceneforge.contrib`, never in core. That
boundary remains mandatory.

---

## Architectural Priorities

1. Stable core abstractions
2. Provider independence
3. Immutable artifacts
4. Knowledge graph
5. Intelligence engine
6. Plugin ecosystem
7. Application ecosystem

---

## Success Criteria

A movie should be analyzed once.

Its understanding should power unlimited downstream applications without repeating expensive inference.

---

## Motto

Movies are not just videos.

They are worlds waiting to be understood.

---

# SceneForge

## Repository

https://github.com/arianhamid/SceneForge

## Founder

Arian Hamid

## Vision

SceneForge is an open-source framework for understanding visual stories.

Movies are not just videos.

They are worlds waiting to be understood.

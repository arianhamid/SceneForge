# SceneForge Vision

This document replaces four overlapping documents that used to say the
same handful of ideas four different ways: `MANIFESTO.md`,
`NORTH_STAR.md`, `CORE_PRINCIPLES.md`, and `TEN_COMMANDMENTS.md`. A
solo, pre-alpha project doesn't need four restatements of its own
values — it needs one that's actually followed. `ANTI_GOALS.md` stays
separate because it says something genuinely different (what
SceneForge deliberately refuses to be); `COMMUNITY_PRINCIPLES.md` and
`CONTRIBUTOR_OATH.md` stay separate because they're for contributors,
who don't exist yet but will read them fresh when they do.

## The problem

Every "movie understanding" pipeline gets rebuilt from scratch, tied
to one specific set of models. Swap Whisper for a different STT
model, or DirectML for ROCm, and the whole pipeline changes shape —
because analysis logic, model calls, and knowledge representation are
all tangled together. Worse: the same movie gets re-analyzed from
scratch every time a downstream application (a comic generator, a
search tool, a storyboard) needs something new from it.

## The north star

**A movie is analyzed once. Its understanding becomes a reusable,
permanent asset** — queryable, extensible, and outlives any single
model or application built on top of it.

Concretely, that means:

- **Understand**: turn raw frames, audio, and time into structured
  knowledge — scenes, characters, locations, dialogue, mood.
- **Organize**: that knowledge lives in one place (a knowledge graph),
  not scattered across per-application caches.
- **Reason**: applications query the knowledge graph, they don't
  re-derive it.
- **Reuse**: a caption generated once for a location is reused by
  every scene at that location, not regenerated per scene.
- **Extend**: a new capability model, a new application, a new media
  type — all can be added without touching what already works.

## Core principles

These are the ones worth actually enforcing, not aspiring to:

1. **Architecture before implementation.** The layer boundaries
   (Media → Runtime → Providers → Artifacts → Knowledge Builders →
   Knowledge Graph → Intelligence → Applications) are the product.
   Get them right before writing the ninth provider.
2. **Knowledge before generation.** SceneForge produces understanding.
   What you build with that understanding (a comic, a search index, a
   summary) is a downstream Application, not the framework's job.
3. **Capabilities before models.** Code depends on `Capability.CAPTION`,
   never on "GPT-4V" or "JoyCaption". Swapping the model behind a
   capability must never require touching a caller.
4. **Immutable artifacts, explicit corrections.** Nothing already
   observed is silently mutated. If new information corrects old
   information, that's a *new* artifact with a `parents` link, or a
   new `Media` instance from `Media.evolve()` — never an in-place edit.
5. **Plugins over hard-coded coupling.** A capability implementation
   is a plugin. The core framework must never import a specific model
   library.
6. **No hidden state.** If two `Pipeline`s in the same process can
   affect each other without either constructor being told about the
   other, that's a bug, not a convenience.
7. **Prove it before you formalize it.** A real, working, ugly
   end-to-end slice against real tools beats a beautifully-specified
   layer with zero implementations. (This is the one this project
   violated hardest before this pass — see `docs/adr/0006-async-providers.md`
   through `0009-media-enrichment.md` and `sceneforge/contrib/ffmpeg/`
   for the correction.)
8. **Local-first, vendor-neutral.** No mandatory cloud dependency for
   the core loop. Cloud model providers are opt-in plugins like any
   other.
9. **Think in years, not sprints** — but don't let that become an
   excuse to write governance documents before the second real
   Provider exists.

## What "success" looks like

Not "SceneForge has 8 layers fully implemented." Success is: *someone
runs a real movie through SceneForge once, then builds three different
things — a comic, a searchable transcript, a location gallery — from
that single analysis, without re-running any model.* Everything in
this repository should be justified by how directly it moves toward
that, not by how complete the layer diagram looks.

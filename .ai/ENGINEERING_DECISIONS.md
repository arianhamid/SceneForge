Decision #001

Artifact is immutable.

Reason:
Reproducibility and lineage.

---

Decision #002

Providers consume and produce Artifacts.

Reason:
Universal composability.

---

Decision #003

Core is media-agnostic.

Reason:
Long-term extensibility.

---

Decision #004

Capability data lives in an injectable `CapabilityRegistry` object,
never module-level global state.

Reason:
Two Pipelines in one process must never be able to affect each other
silently. Full reasoning: `docs/adr/0007-injectable-capability-registry.md`.

---

Decision #005

Provider output is cached via an injectable `ArtifactStore`, keyed by
media identity + provider name + version.

Reason:
"A movie is analyzed once, its understanding is reused forever" needs
somewhere for "once" to actually stick. Full reasoning:
`docs/adr/0008-artifact-persistence.md`.

---

Decision #006

A Provider backed by a real inference model takes that model as a
constructor argument (dependency injection via a minimal structural
Protocol), never constructs it internally.

Reason:
Model construction is slow, resource-heavy, and often needs network
access the provider's own logic shouldn't depend on to be testable.
Full reasoning: `docs/adr/0010-dependency-injected-model-providers.md`.

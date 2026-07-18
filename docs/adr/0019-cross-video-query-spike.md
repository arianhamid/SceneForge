# ADR 0019: Cross-Video Aggregation Also Doesn't Need New Infrastructure — Fourth Confirmation, Deliberately Tested Differently

## Status

Accepted

## Context

Sprints 8-10 found the same result three times running: a question
that looked like it might need new infrastructure (cross-domain
correlation, cross-builder merging) turned out to be answerable with
what already existed, once actually built and checked. `.ai/NEXT_TASK.md`'s
Sprint 11 framing was explicit that three data points isn't proof of a
reliable pattern — it could mean the last three questions were similar
enough to already know the answer. Sprint 11 deliberately picked a
differently-shaped question to actually test that: not "does correlating
two related things need something new" (already asked three ways), but
"does aggregating across an entire multi-video library need something
new" — a full-scan question with no shortcut, as opposed to
`find_related()` (ADR-0014), which searches for everything connected
to one already-known entity id.

## Decision

**Still no.** `iter_all_entities()` (already built for ADR-0014) is
sufficient for genuine cross-video aggregation at realistic scale, with
no changes.

Measured against a synthetic library sized well beyond anything this
project has actually processed one video at a time in every prior
sprint's real integration tests: 400 movies, 15 scenes each, the full
multi-stage pipeline (`SceneGroupingBuilder`-shaped +
`SceneFaceBuilder`-shaped + `SceneMergeBuilder`-merged +
`SceneSequenceBuilder`-sequenced entities) replicated per movie —
23,600 entities across 1,600 real `FileEntityStore` keys, real disk
I/O. The query: rank every movie by total detected faces and filter
for the top quintile — a full-library aggregation that must read every
stored entity, with no shortcut available.

**Result: 0.391 seconds.** (See
`tests/knowledge/test_cross_video_query_spike.py::test_full_library_aggregation_completes_in_reasonable_time`.)

## Consequences

- This is the fourth time checking an existing shape against a new
  need found it already sufficient (after ADR-0011, ADR-0016,
  ADR-0018) — and the first time the question was deliberately shaped
  differently from the prior three specifically to make the result
  meaningful rather than assumed. That's stronger evidence for trusting
  "check first, build second" as this project's actual default than
  any of the three individually.
- This measurement is still bounded the same way ADR-0014's was: valid
  at 400-movie, 23,600-entity scale; says nothing about a real
  production library two or three orders of magnitude larger. The
  test's docstring and its bound (10 seconds, generously above the
  measured 0.391s) are evidence for *now*, not a permanent guarantee —
  unchanged discipline from ADR-0014.
- No index, no SQL/graph backend, no caching layer was added. The
  honest state of Layer 5 after four consecutive "not yet" results:
  there is still no dedicated Knowledge Graph layer, and — for the
  first time — that's not obviously a gap. Everything a Knowledge
  Graph layer would provide (cross-entity correlation, cross-builder
  merging, cross-video aggregation) has a working, measured answer
  using `Entity` + `EntityStore` + plain Python iteration. What Layer 5
  might still add is a real question for a future sprint, but it is no
  longer an *obviously overdue* one.

## Alternatives Considered

1. **Test a fifth or sixth differently-shaped query before drawing any
   conclusion**, to be extra sure. Rejected for this pass: four
   real, differently-shaped measurements (targeted lookup, cross-domain
   correlation, cross-builder merge, cross-video aggregation) is enough
   to act on per `docs/philosophy/VISION.md` principle 7 — further
   spikes without a concrete new question to ask would themselves be
   the premature-formalization pattern this ADR series exists to avoid,
   just inverted (over-verifying instead of over-building).
2. **Add a lightweight index preemptively anyway**, since a real
   production library will eventually be larger than this test. Rejected
   — no measurement supports "eventually" as a reason to build now;
   the discipline throughout this ADR series has been to wait for a
   real number that says otherwise, not to hedge against an unmeasured
   future.

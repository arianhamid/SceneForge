# Comprehensive Movie Understanding, Interpretation, and Forecasting

**Status:** research recommendation and architecture direction; no production
capability or project priority changed

**Date:** 2026-07-21

## Executive decision

SceneForge should pursue the requested result: a deeply inspectable movie or
episode analysis that explains what happens, how it is presented, why events may
happen, what ideas and philosophies the work explores, which scenes are pivotal
or culturally iconic, how cultural practices and symbols may matter, what outside
sources say, and what might happen next.

It should **not** pursue that result as one giant prompt over a video or as one
unqualified answer. The defensible design is a layered evidence and interpretation
workbench with four strictly separated lanes:

1. **Movie evidence** — observations and derived facts grounded in the exact
   media edition being analyzed.
2. **External evidence** — attributable claims from identified, policy-compliant
   sources.
3. **Interpretation** — explicit hypotheses that connect evidence into motives,
   symbolism, philosophy, themes, and competing readings.
4. **Forecasts** — time-stamped, probabilistic scenarios about unreleased events,
   never presented as facts and never allowed to alter lower-layer knowledge.

The final Application may weave these lanes into one readable report, but the
underlying records must remain distinguishable and traceable. A reader should be
able to ask of every consequential sentence:

- What kind of statement is this?
- What exact part of the movie supports or opposes it?
- Which external source, edition, language, and retrieval date does it use?
- Is it observed, derived, inferred, attributed, disputed, or predicted?
- What alternative explanation remains plausible?
- What does SceneForge still not know?

This direction fits SceneForge's north star better than a disposable movie essay:
the expensive analysis becomes reusable evidence and knowledge, while reports,
questions, teaching materials, and forecasts become replaceable Applications.

## Research method and repository coverage

This study reviewed the current project state and priority, all accepted ADRs
0001–0023, the architecture and domain-model documents, public specifications,
compatibility and naming/style rules, philosophy and contributor guidance,
relevant source/tests, and the two narrower research notes on
[media-to-movie understanding](2026-07-20-media-to-movie-understanding.md) and
[external film interpretation](2026-07-20-external-film-interpretation.md).
Persian documentation was treated as a companion explanation of the same current
architecture; historical philosophy documents were checked against the newer
consolidated `VISION.md`, which explicitly supersedes their duplicated guidance.

External research prioritized primary papers, standards bodies, official cultural
and rights sources, scholarly indexes, and publisher/institution pages. The source
list records the material that directly affected recommendations. This is an
architecture synthesis, not a systematic literature review or a legal opinion.

## Requested behavior, constraints, and non-goals

### Requested behavior

The desired scrutiny product should cover, when evidence exists:

- the complete story and chronological event chain;
- characters, identities, goals, beliefs, emotions, changes, and relationships;
- locations, objects, costumes, gestures, dialogue, quotations, music, sound,
  on-screen text, and visual style;
- causal explanations, unresolved questions, foreshadowing, reveals, callbacks,
  contradictions, and continuity;
- narrative structure, point of view, time manipulation, pacing, genre, and arcs;
- themes, philosophies, moral problems, symbols, motifs, and possible hidden
  reasons;
- cultural, regional, historical, religious, ritual, and traditional context;
- pivotal, memorable, formally distinctive, and culturally iconic scenes;
- production facts, creator statements, scholarship, criticism, and audience
  interpretations from the web;
- claim-by-claim comparison of outside assertions with movie evidence;
- bounded, spoiler-controlled next-episode or sequel forecasts;
- an honest coverage report showing which requested dimensions were checked,
  which had evidence, which were not applicable, and which remain unresolved.

### Architectural constraints inherited from SceneForge

This proposal is governed by the current repository truth, especially
[PROJECT_STATE](../../.ai/PROJECT_STATE.md),
[NEXT_TASK](../../.ai/NEXT_TASK.md),
[LAYERS](../architecture/LAYERS.md),
[DOMAIN_MODEL](../architecture/DOMAIN_MODEL.md), and ADRs
[0001](../adr/0001-provider-protocol.md) through
[0023](../adr/0023-python-3-12-baseline.md).

- Understanding flows upward: Media → Runtime → Providers → Artifacts →
  Knowledge → Intelligence → Applications.
- Providers normalize external tools into immutable Artifacts; they do not infer
  motives, themes, or narrative meaning.
- Artifacts are observations, not reasoning, predictions, character identities,
  or interpretations.
- Artifact-to-Entity and Entity-to-Entity work remain separate builder shapes.
- Media, Artifacts, and Entities remain immutable. Corrections and changed
  conclusions create new versioned records with lineage.
- Model-backed Providers receive model objects through small injected protocols
  when weights are not bundled.
- Provider name and version remain part of cache identity; prompts and output
  semantics count as versioned behavior.
- External networks and vendors remain optional plugin boundaries. Local movie
  analysis must still work without them.
- No global mutable registry, implicit cross-movie memory, or hidden source cache
  may be introduced.
- No dedicated graph or `WorldModel` should be built until a measured query proves
  that `EntityStore` and ordinary iteration are inadequate.
- Stable APIs must not be broken merely to align names with this research.
- The current `Pipeline` remains a single-Provider orchestrator. A comprehensive
  analysis workflow is composed by application code until a real caller proves a
  different orchestration contract is needed.

### Non-goals

This direction does not promise:

- a universally true interpretation of a film;
- access to an author's private intention or a character's unspoken mind;
- a culturally authoritative answer inferred from country, clothing, or appearance;
- a guarantee that the most popular online reading is correct;
- a guarantee that the next episode will match a generated scenario;
- unrestricted crawling, paywall bypass, storage of full reviews or scripts, or a
  legal conclusion that every retrieval is permitted;
- immediate implementation of every rung in ADR-0021;
- selecting a fashionable model before the capability and evaluation contract are
  demonstrated.

## Repository truth: what exists and what does not

SceneForge currently has a sound evidence foundation, not full movie
understanding.

| Area | Repository truth on 2026-07-21 | Meaning for this proposal |
|---|---|---|
| Media identity | Immutable `ImageMedia`, `VideoMedia`, and `AudioMedia` | Exact file identity and edition metadata can anchor all later claims. |
| Technical probing | `FFprobeEnricher` for real video metadata | A common clock and stream inventory are available, but richer edition/track identity is future work. |
| Frames | Real FFmpeg frame extraction | Even sampling is evidence, not exhaustive visual coverage. |
| Visual boundaries | Real PySceneDetect cut detection | Output is a shot/visual-segment baseline, not a narrative scene. |
| Speech | `WhisperTranscribeProvider` boundary logic is unit-tested with an injected fake | Real downloaded weights have not been verified in this environment; transcript error and hallucination must remain visible. |
| Faces | Real OpenCV Haar-cascade mechanics | Face presence is not character identity; positive real-photo accuracy is unverified here. |
| OCR | Real Tesseract OCR with positive local integration | Recognized text is Evidence, not the inferred meaning of a sign. |
| Knowledge | Scene grouping, face grouping, text grouping, scene merging, and sequence relationships | Scene entities are organized evidence, not persistent characters, events, motives, or themes. |
| Persistence | Artifact and Entity stores, parent lineage, optional Entity provenance, and cache identity | The reproducible foundation is appropriate for richer knowledge. |
| Querying | `EntityStore.keys()`, iteration, and relationship lookup measured at current scale | No new graph backend is justified yet. |
| Applications | `SceneSummary` renders a minimal Markdown summary | It proves reports should consume stored knowledge rather than rerun Providers. |
| Facts | Not built | A real captioning or object-detection Provider remains the next grounded prerequisite. |
| Events and State | Not built | They must be constructed only after objective Facts exist. |
| Persistent character/object/location identity | Not built | Requires evaluated tracking/re-identification evidence. |
| Intentions, narrative, themes, symbolism | Not built | These are future Intelligence outputs, not current claims. |
| External research and claim verification | Research direction only | Must be opt-in, attributable, rights-aware, and separately stored. |
| Episode forecasting | Not built | Must be an Intelligence/Application concern with an immutable cutoff and evaluation. |

The existing priority should therefore remain unchanged: a real captioning or
object-detection Provider and a narrow fact builder come before broad narrative
reasoning. Research supports this sequence. Movie-understanding benchmarks combine
video with subtitles, audio descriptions, plots, characters, actions, places, and
cinematic style; none supports the idea that a few sampled frames or one summary
prompt constitutes full understanding.[^movienet][^movieqa][^tvqa]

## Core research conclusions

### 1. Full understanding needs a hierarchy, not a flat caption list

Humans segment activity into hierarchically nested events using both sensory
change and conceptual signals such as actors' goals. Event boundaries influence
memory.[^event-segmentation][^cinema-segmentation] That supports ADR-0021's
Evidence → Facts → Entities → Events → State → Relationships → Intentions →
Narrative → Themes direction.

A shot cut, narrative event boundary, scene boundary, sequence, chapter, and act
must be distinct concepts. They may align, but often do not. SceneForge should
retain the current visual boundary for compatibility and later derive semantic
groupings with their own provenance.

### 2. Story and presentation must be modeled separately

Film analysis needs both the reconstructed **story**—events in world chronology—and
the **discourse/presentation**—the order, duration, repetition, point of view,
editing, sound, and style through which viewers receive them. Chatman's classic
distinction is between the narrative's “what” and “way,” while Bordwell describes
viewers constructing a story from causal, temporal, spatial, and stylistic
cues.[^chatman][^bordwell]

SceneForge should therefore maintain at least two timelines:

- `presentation_time`: where the material occurs in this exact media file;
- `story_time`: when the represented event occurs in the fictional chronology,
  possibly uncertain, relative, repeated, imagined, remembered, or hypothetical.

Without this separation, flashbacks, dream sequences, unreliable narration,
parallel editing, and repeated events will produce confident but incoherent plot
explanations.

### 3. Grounded intermediate records are more valuable than one fluent answer

MovieQA showed that questions about who, what, why, and how require multiple
information sources.[^movieqa] MovieGraphs demonstrated the value of timestamped
graphs containing characters, attributes, interactions, relationships, topics,
and reasons.[^moviegraphs] Work on grounded video description warns that models
can generate plausible sentences from priors without grounding nouns in the
video.[^grounded-description]

The conclusion for SceneForge is direct: a final essay is not the knowledge base.
It is a view over grounded, reusable intermediate records.

### 4. Long-video and temporal reasoning remain error-prone

Long films add sparse evidence, memory cost, and long-range dependency problems.
MovieChat explores compact long-video memory, while Video-MME evaluates video,
subtitle, and audio inputs over durations up to an hour.[^moviechat][^video-mme]
TemporalBench reports a substantial human/model gap on event order, frequency,
motion, and other temporal judgments.[^temporalbench]

No provider's fluent answer should bypass timeline checks, state consistency, or
evidence retrieval. Long-video reasoning should operate over stored scene/event
records and retrieve the needed anchors, rather than repeatedly compressing the
whole movie into an opaque prompt.

### 5. Cultural context is plural, living, and community-specific

UNESCO describes intangible cultural heritage as living practice recognized by
the communities that create and transmit it. Its domains overlap, and externally
imposed rigid categories often fail.[^unesco-ich][^unesco-domains] Therefore:

- country or region is a search hint, never the conclusion;
- a detected garment, gesture, object, food, song, or ceremony is a candidate
  cultural reference, not proof of one fixed meaning;
- the report must identify community, period, language, source, and contested or
  variant meanings;
- the film may adapt, fictionalize, criticize, combine, or misuse a real practice;
- community and domain experts outrank automated pattern matching for sensitive
  conclusions.

Getty's multilingual cultural-heritage vocabularies are useful for normalized
discovery of objects, places, styles, techniques, cultures, and iconographic
narratives, but Getty itself notes that records have contributing sources and
should be cited.[^getty-vocab][^getty-data]

### 6. Interpretation cannot be “fact-checked” like an observable event

“The key is dropped at 01:12:08” and “the key represents inherited guilt” have
different truth conditions. The first can be checked against movie evidence. The
second can be supported, weakened, attributed, or contested, but not mechanically
declared universally true.

Fact-verification research commonly separates supported, refuted, and
not-enough-information outcomes and requires evidence retrieval.[^fever] The
system needs that discipline, but it also needs a separate verdict vocabulary for
interpretive claims.

### 7. Citation presence is not enough

Retrieval-augmented generation makes knowledge revisable and attributable, but
retrieval and provenance remain active challenges.[^rag] Citation-evaluation
research separates answer correctness from citation quality and finds that even
strong systems often lack complete support.[^alce]

SceneForge must check whether a cited passage actually supports the sentence,
whether it concerns the same movie edition, whether sources are independent, and
whether counterevidence was omitted. A citation counter is not a truth score.

### 8. “Iconic” is a family of judgments

At least four meanings must remain separate:

1. **Narratively pivotal** — removing the scene changes the causal story.
2. **Formally distinctive** — staging, shot scale, movement, editing, color,
   lighting, performance, sound, or music is exceptional within the work.
3. **Memorable** — viewers tend to remember it; video memorability is measurable
   but prediction remains imperfect.[^videomem]
4. **Culturally iconic** — a particular public repeatedly quotes, references,
   remixes, teaches, criticizes, or recognizes it over time.

Only the first two can be estimated substantially from the movie alone. Cultural
iconicity requires dated reception evidence, an audience/culture scope, and
deduplicated outside sources. Popularity, artistic quality, personal importance,
and memorability must not be collapsed into one number.

### 9. Forecasts should be probabilistic and auditable

Narrative event-prediction research treats future events as predictions from
context and shows that long-range temporal/causal dependencies remain difficult;
simple cloze tests may reward frequency bias rather than story understanding.
[^event-cloze-critique][^docscript]

A useful next-episode answer is therefore a ranked scenario set, not a confident
single continuation. Probabilistic forecasting should be evaluated for calibration
and sharpness with proper scoring rules.[^forecast-calibration][^proper-scoring]
Every forecast needs a frozen information cutoff so later releases cannot leak
back into the original prediction.

## The epistemic contract

The epistemic contract is more important than any particular model. It prevents a
smooth report from silently converting observations into certainty.

### Statement classes

| Class | Definition | Example | Allowed source | Typical result |
|---|---|---|---|---|
| Observation | Direct Provider output from this media | OCR read “POLICE” at 12:04 | Artifact | observed, with provider quality |
| Derived fact | Deterministic or constrained synthesis above observations | A visible door changes from closed to open | Multiple Artifacts/Entities | supported / contradicted / insufficient |
| Identity assertion | Claim that observations refer to the same persistent thing | Face track 8 is the same character in scenes 3 and 17 | Tracking/recognition plus corroboration | accepted / ambiguous / rejected |
| Event | Participants and state changes organized in time | Character A gives the key to B | Facts and entity identities | supported / partial / disputed |
| Causal assertion | One event enables, motivates, causes, prevents, or reveals another | The stolen key enables entry | Events plus explicit rationale | supported / plausible / contested |
| Production fact | Fact outside the fictional world | This is the 142-minute director's cut | Authoritative external source | corroborated / disputed / unverified |
| Attributed interpretation | A named source's reading | Critic C reads the house as grief | External source | accurately attributed / misquoted |
| System interpretation | SceneForge's evidence-backed hypothesis | Repetition suggests the house may function as a grief motif | Movie and external evidence | strong / plausible / weak / contested |
| Cultural-context claim | Claim about a real practice or symbol | This gesture resembles practice P in community C during period T | Community/curated/scholarly source | corroborated / variant / disputed / unsafe to generalize |
| Forecast | Scenario about unreleased story material | B may expose A in the next episode | Knowledge available at cutoff | probability, assumptions, later resolution |

### Verdict vocabularies

For movie-checkable facts:

- `supported`
- `partially_supported`
- `contradicted`
- `insufficient_movie_evidence`
- `ambiguous_edition_or_identity`

For externally checkable facts:

- `corroborated_externally`
- `disputed_by_sources`
- `unverified`
- `source_mismatch`
- `outdated_or_superseded`

For interpretations:

- `evidence_rich_interpretation`
- `plausible_interpretation`
- `weakly_grounded_interpretation`
- `contested_interpretation`
- `attributed_only`
- `not_assessable`

For forecasts:

- `open`
- `resolved_true`
- `resolved_partial`
- `resolved_false`
- `unresolvable`
- `invalidated_by_scope_change`

These enums should not be added to production code now. They are candidate
vocabulary to test in a real claim-verification and forecasting spike. An ADR is
required before they become persistent framework contracts.

### Confidence rules

- Keep acquisition confidence, identity confidence, fact confidence,
  interpretation strength, and forecast probability separate.
- Preserve the provider's native score and calibration context. Do not pretend a
  face-detector score and a language-model score are comparable.
- Confidence must never replace evidence links or an explicit unknown state.
- Repeated copies of one source do not increase independence.
- Absence in sampled frames is not evidence that an event never occurred.
- A contradiction from an unreliable transcript should lower certainty rather
  than automatically overturn visual evidence.
- Forecast probability is a quantitative claim and should be calibrated on held-
  out historical episodes. Interpretation strength is not a probability that a
  theme is “true.”
- Reports should show coverage and uncertainty separately. A well-supported answer
  to 30% of the requested checks is not 30% confident.

## Comprehensive movie-analysis coverage contract

The following matrix defines what “check every side” should mean. Each row in a
full scrutiny report must end in one of: `covered`, `partially_covered`,
`not_applicable`, `blocked_by_missing_capability`, `insufficient_evidence`, or
`withheld_by_policy`.

| Dimension | Questions to answer | Minimum grounding |
|---|---|---|
| Work identity | What title, year, series, season, episode, country, and language is this? | File metadata plus external identity match |
| Edition identity | Which theatrical, broadcast, regional, censored, restored, extended, or director's cut? | Runtime, language/track inventory, duration, hashes, edition source |
| Stream inventory | Which video, audio, commentary, subtitle, and chapter tracks exist? | Authoritative container probe |
| Coverage | Which times, tracks, frames, and modalities were analyzed or skipped? | Machine-readable processing manifest |
| Shots | Where are cuts, fades, dissolves, and continuous takes? | Frame-level boundary evidence |
| Narrative scenes | Which shots form one dramatic unit, and why? | Visual, dialogue, location, time, and action continuity |
| Sequences/chapters | Which scenes form larger goals or movements? | Events, goals, and narrative function |
| Visual content | Who/what is visibly present, where, and for how long? | Dense/adaptive frames, detection, tracking, grounding |
| Composition | What framing, shot scale, angle, depth, blocking, and screen direction matter? | Shot-level style observations |
| Camera | What movement, lens/focus behavior, viewpoint, or subjectivity is used? | Temporal visual analysis |
| Lighting/color | What palettes, contrast, exposure, color transitions, and visual motifs recur? | Calibrated image/shot measurements plus context |
| Editing | What continuity, montage, parallel action, match cuts, ellipses, or repetitions occur? | Shot relationships and presentation timeline |
| Dialogue | What is said, by whom, in what language, and with what uncertainty? | Audio/subtitle alignment, diarization, speaker evidence |
| Quotation | Is a line exact, paraphrased, dubbed, mistranslated, or popularly misquoted? | Edition-specific audio/subtitle anchor and translation lineage |
| On-screen text | What signs, letters, messages, credits, dates, and interfaces appear? | OCR with spatial and temporal anchors |
| Sound | Which ambient sounds, effects, off-screen cues, silence, and audio transitions matter? | Time-bounded audio-event evidence |
| Music | Which cues, songs, themes, leitmotifs, instrumentation, lyrics, and recurrences matter? | Cue segmentation, identification where licensed, recurrence evidence |
| Characters | Which persistent characters exist across shots/scenes? | Detection, tracking/re-identification, name evidence, ambiguity sets |
| Character state | What does each character know, believe, possess, feel, want, and risk at each point? | Events plus explicit/inferred state with provenance |
| Performance | What gesture, gaze, posture, expression, vocal delivery, or interaction is salient? | Temporal person/audio grounding; no emotion-by-face shortcut |
| Relationships | How do kinship, trust, power, conflict, intimacy, obligation, and alliance change? | Time-scoped relationship evidence |
| Locations | Where does each event occur, and which locations recur or change? | Visual/text/audio evidence and identity resolution |
| Objects/props | Which objects persist, change ownership/state, enable actions, or recur symbolically? | Object tracking, state, custody, and event links |
| Costume/material culture | What clothing, insignia, tools, food, craft, architecture, or decor may be meaningful? | Grounded objects plus dated cultural sources |
| Actions | What objective actions occur, including off-screen or audio-indicated actions? | Caption/detection/audio facts with time anchors |
| Events | Who did what to whom, where, when, how, and with what result? | Composed facts and entity identities |
| State transitions | What becomes opened, broken, revealed, lost, transferred, known, or believed? | Before/after snapshots tied to events |
| Chronology | What is story order versus presentation order? | Dual timelines with uncertainty |
| Causality | Which events cause, enable, motivate, prevent, reveal, or merely precede others? | Typed evidence links and rival explanations |
| Goals/intentions | What might each character be trying to achieve, and what alternatives fit? | Behavior/dialogue/state plus counterevidence |
| Information flow | Who knows what, when; what is hidden from characters or viewers? | Dialogue, perception, reveals, focalization |
| Plot explanation | What happens and why, including setup, escalation, turning points, climax, and resolution? | Event/state/causal graph |
| Narration | Who or what controls point of view, reliability, withholding, and reveal order? | Presentation form and information asymmetry |
| Pacing | Where does event density, shot length, dialogue, motion, or tension change? | Time-series measurements plus narrative context |
| Foreshadowing/payoff | Which earlier details predict or enable later events? | Backward links established only after payoff evidence |
| Motifs/symbols | Which images, sounds, words, objects, colors, or actions recur, transform, and cluster? | Recurrence plus narrative function; interpretations remain plural |
| Themes | Which abstract concerns are dramatized across choices and consequences? | Multiple event/character arcs, not isolated keywords |
| Philosophies/ideas | Which explicit arguments or conceptual resemblances appear, and where do they differ from a tradition? | Movie anchors plus primary/scholarly philosophical sources |
| Moral/political questions | What values, institutions, harms, duties, freedoms, identities, or power structures are examined? | Evidence-backed competing readings and historical context |
| Cultural/ritual context | Which practices may be represented, by which community and period, with what variants? | Community/curated/scholarly attribution; no nationality shortcut |
| Historical context | Which real period, event, technology, institution, or social condition matters? | Authoritative external sources and anachronism checks |
| Religious/mythic context | Which texts, figures, rituals, myths, or iconographies are referenced or resembled? | Specific source tradition, edition, community, and uncertainty |
| Intertextuality | What other film, book, artwork, music, genre, or event is quoted or evoked? | Formal/textual match plus source attribution |
| Production context | What do scripts, commentaries, interviews, design records, or creators say? | Direct, edition-matched sources; declared intent is not exclusive meaning |
| Continuity/anomalies | Are there contradictions, impossible states, unexplained identities, or edition differences? | Cross-scene validation with benign alternatives |
| Iconic scenes | Which scenes are pivotal, distinctive, memorable, or culturally circulated, and for whom? | Separate internal and reception evidence |
| Competing interpretations | What are the strongest rival readings and their evidence/counterevidence? | Attributed sources plus movie anchors |
| Unresolved questions | What remains deliberately ambiguous, accidentally unclear, or unsupported? | Explicit unknowns and candidate evidence needs |
| Forecasts | What plausible next events follow, under which assumptions and cutoff? | Current state, unresolved threads, genre/adaptation policy, calibrated scenarios |
| Rights/spoilers/sensitivity | What can be stored or shown, to whom, at what spoiler level? | Source policy, license metadata, user controls |
| Reproducibility | Which provider/model/prompt/source/version produced each claim? | Complete immutable provenance and hashes |

## Target conceptual records

These are conceptual records for spikes and specifications, not a recommendation
to add a large type hierarchy immediately.

### 1. Media edition fingerprint

Before internet enrichment, SceneForge must know which work and cut it has. EIDR
distinguishes audiovisual titles and versions/edits, which illustrates why title
matching alone is inadequate.[^eidr][^eidr-edits]

Candidate fields:

- source `media_id` and content hash;
- title candidates, alternate titles, original script, transliterations;
- release year, work/series/season/episode identifiers;
- duration, frame rate/time base, aspect ratio, resolution;
- audio/subtitle/commentary tracks and languages;
- cut/edition/region/distributor candidates;
- authoritative external IDs and match evidence;
- match verdict, alternatives, and confidence;
- fingerprint version and creation provenance.

### 2. Universal evidence anchor

Every claim should target the smallest practical evidence span:

- `media_id` and edition fingerprint;
- start/end presentation time;
- optional frame number/time base;
- optional spatial region (`xywh`) and track/entity ID;
- optional audio channel/speaker segment;
- optional subtitle/OCR document and text span;
- artifact/entity parent IDs;
- representative thumbnail reference, not an embedded copyrighted frame by
  default.

W3C Web Annotation provides an interoperable body/target model and supports
segments of timed multimedia; Media Fragments defines temporal and spatial
selectors.[^web-annotation][^media-fragments] SceneForge need not adopt JSON-LD
now, but its anchors should not preclude later mapping.

### 3. Atomic assertion

An assertion should contain one proposition, not a paragraph with several claims:

- stable ID and assertion class;
- normalized subject, predicate, object/value;
- human-readable text and original source wording;
- polarity, modality, and tense;
- presentation time and story time, when applicable;
- asserted-by agent/source/builder and creation time;
- evidence links with `supports`, `opposes`, `contextualizes`, or `derived_from`;
- verdict, confidence/strength, assumptions, and unresolved dependencies;
- supersedes/superseded-by links without mutation;
- model/provider/prompt/schema versions.

W3C PROV-O's Entity/Activity/Agent model and derivation relationships are a useful
interchange reference for this richer lineage.[^prov-o] C2PA reinforces an
important distinction: verifiable provenance can establish origin/history and
tamper evidence, but provenance alone cannot establish that content is factually
true.[^c2pa]

### 4. Event and state records

An event should minimally record:

- event type and natural-language gloss;
- participants and semantic roles;
- location and presentation/story intervals;
- preconditions;
- actions/facts composing the event;
- immediate and delayed effects;
- before/after state links;
- explicit dialogue rationale, if any;
- confidence and unresolved participant identities.

State must be time-scoped. “The door is locked” without a valid interval is not a
usable movie fact. State transitions must preserve the prior state rather than
overwrite it.

### 5. Interpretation dossier

One interpretation record should hold:

- thesis;
- interpretation type: motive, symbol, motif, theme, philosophy, political,
  cultural, formal, psychoanalytic, historical, or other;
- movie evidence for and against;
- external sources supporting, disputing, or merely originating the reading;
- assumptions and required cultural/philosophical context;
- rival interpretations;
- scope: shot, scene, arc, whole work, franchise, or reception community;
- explicitness: stated, strongly implied, structural, speculative;
- strength verdict and author/source attribution;
- generated explanation version.

### 6. Forecast record

A forecast is neither an Artifact nor a settled Entity. Candidate fields are:

- target series/work and exact prediction horizon;
- immutable information cutoff and spoiler/source policy;
- source episode/season state version;
- scenario set with normalized probabilities and a residual `other` probability;
- expected event window, involved entities, prerequisites, and assumptions;
- supporting unresolved threads, promises, constraints, motifs, genre patterns,
  and official pre-cutoff promotional evidence;
- disconfirming evidence and failure modes;
- forecaster/model/prompt/calibration-set versions;
- later outcome, resolver, resolution time, and score.

The first spike may persist this outside `EntityStore`. If a real Application
needs forecasts to participate in entity queries, that caller should drive a new
ADR instead of silently treating predictions as knowledge.

## Proposed architecture

```text
Exact movie/episode edition
          │
          ▼
Media + Runtime fingerprint
          │
          ▼
Local Providers ───────────────────────────────┐
(visual, speech, OCR, sound, music, style)     │
          │                                    │ immutable observations
          ▼                                    │
Artifacts / Evidence ◄─────────────────────────┘
          │
          ▼
Knowledge Builders: Facts → persistent Entities → Events → State
          │                         │
          └───────────┬─────────────┘
                      ▼
          Relationship Builders
        (identity, sequence, custody,
         social, causal, same-as)
                      │
        ┌─────────────┴────────────────┐
        │                              │
        ▼                              ▼
Opt-in external source lane       Intelligence reasoners
(identity, sources, atomic        (causality, motive hypotheses,
 claims, cultural context,         narrative, philosophy, themes,
 reception, rights metadata)       iconicity, ambiguity)
        │                              │
        └───────────► claim/evidence ◄─┘
                        assessments
                             │
                    ┌────────┴─────────┐
                    ▼                  ▼
          Scrutiny Report App     Forecast Reasoner/App
          (all evidence lanes)    (cutoff + scenarios)
```

### Layer placement

| Concern | Correct home | Must not do |
|---|---|---|
| Decode/sample/probe | Runtime/Media Enricher | Infer story meaning |
| Caption, detect, recognize, transcribe, style-analyze | Provider in `contrib` | Build characters, events, or themes |
| Time-bounded raw result | Artifact | Contain motive or prediction |
| Facts, entities, events, states | Knowledge Builder | Call a Provider or web crawler |
| Same identity, sequence, social/custody/causal links | Relationship Builder, once proven | Hide relationship logic in storage |
| Motive/theme/symbol/philosophy hypothesis | Intelligence | Rewrite lower facts to fit a reading |
| Source retrieval | Opt-in plugin/network boundary | Become a mandatory core dependency |
| Claim comparison | Evidence-aware builder/reasoner, shape proven by spike | Use source count as truth |
| Report composition | Application | Re-run extraction or parse provider-specific JSON |
| Forecast | Intelligence plus Application/persistence boundary | Flow into Facts, Events, or State as truth |

### External source boundary

The earlier research note suggested an `ExternalSourceProvider`. A deeper
architecture review adds an important qualification: the current Provider
Protocol consumes SceneForge `Media`, while a URL, review, or scholarly paper is
not currently one of its supported media types. Do not disguise a URL as
`VideoMedia` or weaken the Provider contract.

The smallest safe spike is an opt-in plugin-owned source ingestor with its own
explicit input and output records. If repeated real use shows that external text
belongs in the universal Media → Provider path, propose `TextMedia` or an external
document contract in an ADR with compatibility and security analysis. Until then,
keep the experiment outside stable core APIs.

## Deep-analysis design by subject

### Story explanation and causality

The system should produce three linked views:

1. **Presentation map** — shots/scenes in file order, including flashbacks,
   dreams, parallel edits, titles, and omissions.
2. **Story chronology** — best reconstruction of events in world order, with
   uncertainty and alternate placements.
3. **Causal graph** — typed links such as `causes`, `enables`, `motivates`,
   `prevents`, `reveals`, `misleads_about`, `foreshadows`, and `pays_off`.

`precedes` must never silently become `causes`. A cause explanation should state
the mechanism and counterfactual: if the proposed cause were absent, would the
effect still plausibly occur? It should also distinguish:

- physical cause;
- intentional/motivational reason;
- informational cause (a discovery changes action);
- institutional/social constraint;
- narrative function (the filmmaker reveals it here);
- production explanation (budget, censorship, adaptation, or edit);
- thematic interpretation.

Those are different questions even when ordinary language calls all of them
“why.”

### Characters, motives, and “hidden reasons”

No system directly observes intention. It observes speech, action, attention,
reaction, knowledge, possession, relationships, and consequences. The motive
reasoner should therefore generate a dossier rather than one diagnosis:

- candidate goal;
- evidence the character had the goal;
- evidence the character knew or believed necessary premises;
- actions consistent and inconsistent with it;
- alternative goals and deception possibilities;
- whether the claim is explicit, inferred, or sourced externally;
- change over time;
- confidence and what new evidence would discriminate alternatives.

“Hidden reason” should be subdivided into:

- character motive;
- withheld plot cause;
- narrator/point-of-view mechanism;
- symbolic or thematic function;
- creator's declared production intention;
- external production constraint.

This prevents a creator interview, a character motive, and a critic's symbolic
reading from being merged into one false answer.

### Philosophy and ideas

Philosophical analysis should not be keyword matching. It should classify the
strength of connection:

1. **Explicit quotation/reference** — a work or thinker is named or quoted.
2. **Explicit argument** — dialogue or narration advances recognizable premises
   and conclusions without naming a tradition.
3. **Dramatized problem** — choices and consequences stage a philosophical issue.
4. **Formal analogy** — the work resembles a concept, according to an attributed
   analyst.
5. **Speculative reading** — interesting but weakly evidenced.

For each proposed connection, report:

- concept and tradition;
- edition/translation of any quoted source;
- movie scenes, dialogue, character choices, and consequences;
- an expert-reviewed reference explanation;
- similarities and important mismatches;
- whether influence is documented or merely interpretive;
- rival philosophical readings;
- confidence/strength and source attribution.

The Stanford Encyclopedia of Philosophy uses expert-maintained, editorially
refereed entries and stable archived editions; it is a strong orientation source.
PhilPapers is a broad research index, not an automatic quality verdict for every
indexed item.[^sep][^philpapers] Primary philosophical texts and peer-reviewed
scholarship should support specific claims. Public-domain text repositories may
support quotation lookup only after edition and translation rights are checked.

### Symbols, motifs, and foreshadowing

The analysis should first detect recurrence without assigning meaning:

- object/image;
- color/light pattern;
- word/phrase;
- sound/music cue;
- gesture/blocking/composition;
- location/weather/natural element;
- action or situation pattern.

Meaning is a second-stage hypothesis based on placement, transformation,
character association, causal function, contrast, and payoff. A motif dossier
should show every occurrence, not only the examples that fit the selected theme.

Foreshadowing is retrospective unless creator/source evidence proves an intended
setup before release. Before a payoff, call it a forecast clue or unresolved
detail. After a payoff, link setup to payoff with the new evidence rather than
rewriting the original observation.

### Cultural, ritual, religious, and regional scrutiny

For each candidate reference, use this context tuple:

```text
observed practice/object/gesture
→ depicted fictional community and time
→ candidate real community/tradition and period
→ source-supported meanings and variants
→ how the film frames, changes, combines, or contests them
→ confidence, sensitivities, and community-review status
```

The report must separate:

- what is visibly/audibly depicted;
- what characters inside the story believe it means;
- what a real community's sources say;
- what production records say the filmmakers intended;
- what critics/audiences interpret;
- what SceneForge hypothesizes.

Forbidden shortcuts include “people from country X believe Y,” treating all
religious practice as uniform, inferring ethnicity from appearance, or assigning
sacred meaning from object shape alone. UNESCO's AI ethics recommendation calls
for locally relevant content, multilingualism, cultural diversity, and
intercultural participation, which supports expert/community review for this
module.[^unesco-ai-ethics]

### Cinematography, editing, performance, sound, and music

Form is not decoration added after plot. It controls what viewers see, know,
expect, and feel. The style analysis should cover:

- shot scale and duration;
- angle, camera movement, focus, lens/depth cues, and viewpoint;
- composition, blocking, gaze, entrances/exits, and screen direction;
- lighting, palette, contrast, texture, aspect-ratio changes;
- cuts, dissolves, match cuts, montage, reaction shots, cross-cutting, ellipsis;
- dialogue delivery, gesture, posture, expression, silence;
- diegetic/non-diegetic sound, off-screen sound, perspective, bridges;
- music cue boundaries, recurrence, lyrical content, source music, leitmotifs;
- deviations from the film's own established formal norms.

MovieNet's cinematic annotations and CineTechBench's technique categories show
that shot scale, movement, angle, composition, lighting, color, and focal length
are separable evaluation targets.[^movienet][^cinetechbench] SceneForge should
store observations first and connect them to narrative effects as interpretations.
For example, “extreme close-up” can be a style fact; “the close-up traps the
character morally” is an interpretation.

### Iconic-scene analysis

Do not emit a single opaque “iconic score.” Emit a scorecard and narrative:

| Axis | Movie-internal signals | External signals |
|---|---|---|
| Causal centrality | Number/importance of later events depending on it | Plot summaries consistently retain it |
| Character turning point | Goal, belief, relationship, or state change | Critics/scholars identify the turn |
| Thematic density | Multiple established motifs/themes converge | Competing interpretations discuss it |
| Formal distinctiveness | Style deviation, long take, montage, sound/color pattern | Technique scholarship, awards, creator discussion |
| Emotional intensity | Performance, stakes, music/silence, consequence | Human ratings or memory studies |
| Memorability | Learned memorability proxy with uncertainty | Recall experiments or audience surveys |
| Quotability | Dialogue/on-screen text recurrence | Verified quotations and translations |
| Cultural circulation | Not inferable from movie alone | References, parodies, remixes, teaching, exhibitions, archives |
| Longevity/reach | Not inferable from movie alone | Dated evidence across communities, languages, and decades |

The result should say “pivotal within the story,” “formally distinctive,”
“frequently cited by these sources,” or “iconic for this audience and period,” not
just “iconic.” Scene salience can also be evaluated against human summaries, as
recent script-summarization work does.[^scene-saliency]

## External research and truth checking

### Source hierarchy is claim-dependent

| Claim | Preferred sources | Important limitation |
|---|---|---|
| Work/edition identity | EIDR, distributor/studio/archive records, physical release metadata | Databases may describe a different regional cut. |
| Exact movie event/dialogue | The analyzed file, licensed subtitles/script, audio description | Scripts/subtitles may differ from final edit or dub. |
| Production fact | Official credits, production/archive records, direct documentation | Marketing copy is interested testimony. |
| Creator's declared intent | Dated first-party interview, commentary, production note | Declared intent is evidence about the declaration, not exclusive meaning. |
| Historical fact | Archives, government/institutional records, peer-reviewed scholarship | Match period, place, and scholarly dispute. |
| Cultural practice | Community organizations, UNESCO records, museums, field scholarship, qualified local experts | Practices vary within communities and over time. |
| Philosophical concept | Primary text, SEP orientation, peer-reviewed work found via scholarly indexes | Translation and scholarly disagreement matter. |
| Critical interpretation | Named scholar/critic and publication | Remains attributed, regardless of prestige. |
| Audience interpretation | Surveys, audience studies, labeled community sources | Platform users are not the whole audience. |
| Iconic status | Archives, criticism, education/exhibition records, independent audience/reception evidence | Popularity and copying do not establish artistic value. |
| Forecast evidence | Movie knowledge available at cutoff; optional official pre-release material | Leaks and post-cutoff sources invalidate honest forecasting. |

### Retrieval workflow

1. **Fingerprint the work and edition.** Search by alternate title, original
   script, year, creator, duration, episode identifiers, and cut.
2. **Set policy before fetching.** Define allowed domains/source types, robots,
   terms, license, paywall, personal-data, spoiler, language, and storage rules.
3. **Retrieve metadata first.** Prefer APIs, feeds, institutional records,
   user-supplied URLs, and licensed/open corpora.
4. **Preserve source provenance.** Canonical URL, title, author, publisher,
   publication/update/retrieval date, language, jurisdiction/rights metadata,
   query, content hash, and edition scope.
5. **Store minimal permitted content.** Prefer metadata, a short necessary excerpt,
   and a generated digest over a full copyrighted page.
6. **Deduplicate dependence.** Detect syndication, mirrors, copied reviews, and
   pages that all cite one original source.
7. **Extract atomic claims.** Split observable, production, historical, cultural,
   interpretive, and predictive statements.
8. **Retrieve relevant movie anchors.** Use dialogue, OCR, objects, events, states,
   and scenes rather than comparing against a global summary.
9. **Apply deterministic checks first.** Identity, time overlap, exact/fuzzy quote,
   entity co-occurrence, chronology, and state consistency.
10. **Assess evidence.** Record support, opposition, source mismatch, uncertainty,
    and independent corroboration.
11. **Generate prose from the evidence packet only.** Require sentence-level movie
    and external citations.
12. **Run a citation audit.** Check entailment, completeness, source quality,
    edition match, counterevidence, and broken/revised links.
13. **Support correction.** New retrievals or human review supersede assessments;
    they never erase the original source or conclusion.

### Rights and access policy

Robots Exclusion Protocol rules are standardized for crawler access control, but
they are not authorization by themselves.[^robots] Copyright exceptions differ by
jurisdiction and fact pattern. The U.S. Copyright Office describes fair use as a
case-by-case inquiry; the EU DSM Directive conditions some text/data-mining uses
on lawful access and rights reservations.[^us-fair-use][^eu-dsm]

Therefore an implementation needs legal/policy review for its deployment context.
At minimum it must:

- never bypass authentication, paywalls, access controls, or rate limits;
- honor robots and machine-readable rights reservations where applicable;
- record the policy decision that allowed metadata/excerpt storage;
- keep source text out of prompts/logs when policy rejects processing;
- avoid republishing full reviews, scripts, subtitle tracks, or books;
- treat external text as untrusted data, never as system instructions;
- isolate network capability from local analysis and make it explicitly opt-in;
- support deletion or metadata-only retention when rights require it;
- preserve links and attribution even when only a digest can be stored.

This report is an engineering recommendation, not legal advice.

## Episode and sequel forecasting

### Product modes

- `disabled` — default for completed films and spoiler-sensitive use.
- `movie_only` — uses released material through a specified timestamp/episode.
- `official_preview` — additionally uses official trailers/synopses published
  before the cutoff, clearly separated from inference.
- `adaptation_aware` — uses source novels/comics/games and therefore carries a
  major spoiler label.
- `open_web` — uses permitted pre-cutoff speculation and must label possible
  contamination, rumor, and circular copying.

### Forecast procedure

1. Freeze an exact release and information cutoff.
2. Snapshot unresolved goals, threats, promises, secrets, objects, relationships,
   locations, character knowledge, and state.
3. List hard constraints and disqualifying contradictions.
4. Retrieve setup/payoff patterns and genre conventions as weak priors, not laws.
5. Generate diverse candidate event chains, including a surprise/other branch.
6. Check every chain for temporal, causal, character, and world-state consistency.
7. Merge semantically equivalent scenarios.
8. Assign probabilities using a model calibrated on historical, time-sliced
   episodes; do not present raw model self-confidence as probability.
9. Explain evidence, assumptions, counterevidence, and what would falsify each
   scenario.
10. After release, resolve without editing the original forecast.

### Evaluation

- Brier score and logarithmic score for resolvable categorical events;
- calibration/reliability diagrams by probability bucket;
- top-k event recall and precision;
- scenario diversity without semantic duplicates;
- temporal-window accuracy;
- character/state consistency violation rate;
- abstention/coverage curve;
- spoiler-leak and post-cutoff contamination rate;
- performance by show, genre, language, season position, and forecast horizon;
- comparison with simple baselines: event frequency, unresolved-thread heuristic,
  and human crowd/expert forecasts.

The report should prefer “three plausible scenarios” over false precision when
the future is intentionally underdetermined.

## Full scrutiny report contract

The future Application should generate a report in this order:

1. **Identity and edition** — exact work/cut/tracks/hash and ambiguity.
2. **Analysis manifest** — providers, versions, sampling, tracks, failures, cache,
   and unexamined intervals.
3. **Executive story explanation** — concise plot and major causal chain.
4. **Chronology versus presentation** — flashbacks, dreams, parallel threads,
   repeated/withheld events.
5. **Scene and sequence dossiers** — time range, setting, participants, actions,
   dialogue, visual/audio form, state changes, purpose, evidence.
6. **Characters** — identity evidence, goals, beliefs, knowledge, arcs,
   relationships, contradictions, alternative motive hypotheses.
7. **Locations and objects** — recurrence, state, custody, causal and symbolic use.
8. **Causal and information-flow map** — why events occur and who knows what.
9. **Cinematography/editing/performance/sound/music** — form and evidence-backed
   effects.
10. **Motifs, foreshadowing, callbacks, and payoffs** — complete occurrence lists.
11. **Themes, philosophies, and moral/political questions** — multiple readings,
    similarities, mismatches, and source attribution.
12. **Cultural, ritual, religious, and historical context** — community-, period-,
    and source-specific analysis with variants.
13. **Iconic/pivotal scenes** — separate internal, memorability, and reception
    scorecards.
14. **External claim audit** — source claim, movie evidence, verdict, and edition
    match.
15. **Competing interpretations** — strongest evidence for and against each.
16. **Continuity, ambiguity, and unknowns** — never hide coverage gaps.
17. **Forecasts** — optional modes, cutoff, scenarios, probabilities, assumptions.
18. **Coverage checklist** — every row from the coverage contract and its status.
19. **Sources and evidence index** — external bibliography plus internal clickable
    time/spatial/text anchors.

Every prose section should support a “show evidence” expansion. A report without
that capability is a generated essay, not reusable narrative intelligence.

## Evaluation and quality program

### Evaluation corpora

Build small, licensed or redistributable corpora before broad implementation:

1. **Controlled perception clips** — cuts, fades, camera moves, objects, state
   changes, on-screen text, overlapping speech, sound cues, and known timestamps.
2. **Public-domain/open narrative works** — full stories with expert scene,
   character, event, state, chronology, and causal annotation.
3. **Edition pairs** — theatrical/extended, dub/subtitle, censored/uncensored, or
   restored variants to test edition identity and claim mismatch.
4. **Multilingual/cross-cultural set** — selected with community/domain experts,
   not merely balanced by country labels.
5. **Interpretation set** — scenes with several published, genuinely competing
   readings and evidence annotations.
6. **Reception/iconicity set** — dated, audience-scoped reception records.
7. **Forecast backtest set** — historical episodic releases with all sources
   time-filtered to the original prediction date.

### Metrics by layer

| Layer/output | Examples of required metrics |
|---|---|
| Technical/segmentation | probe correctness, boundary precision/recall, temporal IoU, coverage |
| Speech/text/audio | WER/CER by language, diarization error, speaker attribution, OCR precision/recall, sound-event mAP |
| Vision/style | detection precision/recall, tracking identity switches, grounding accuracy, shot-style confusion matrices |
| Facts/events/state | atomic fact precision/recall, participant/role accuracy, temporal relation F1, state-transition consistency |
| Identity/relationships | same/different precision, cluster metrics, relationship type and valid-time accuracy |
| Causality/intent | expert-labeled link precision, rival-hypothesis coverage, contradiction rate, abstention quality |
| External research | work/edition match, source metadata completeness, dedup accuracy, claim extraction precision |
| Verification | evidence retrieval recall, verdict accuracy, false contradiction rate, counterevidence recall |
| Citation | citation entailment/correctness, completeness, placement, broken/source-mismatch rate |
| Interpretation | evidence precision, unsupported-claim rate, rival-reading diversity, expert helpfulness, cultural-review agreement |
| Iconicity | agreement per axis, time/audience stability, distinction from popularity and plot salience |
| Forecast | Brier/log score, calibration, top-k recall, state violations, leakage, coverage |
| Report | coverage-contract completion, traceability, spoiler compliance, reproducibility, human usefulness |

### Release gates

- A higher rung cannot be marked real because it produced plausible prose.
- Positive integration evidence must use real inputs for the actual capability.
- Results must be stratified by language, genre, lighting, speech overlap, culture,
  and other known failure regimes where applicable.
- A skipped optional integration remains a skip, not proof.
- Human review rubrics must allow “insufficient evidence” and competing correct
  readings.
- Cultural modules need qualified, compensated community/domain review and a
  correction mechanism.
- Any model or prompt change that changes output semantics must invalidate the
  relevant cache identity.
- The full report must disclose failed providers and coverage gaps, not quietly
  omit sections.

## Staged roadmap with explicit triggers

No dates are assigned. Each phase starts only when its trigger is real.

### Phase 1 — Objective Facts (current priority)

**Trigger:** current, as documented by ADR-0021 and `NEXT_TASK`.

- Ship one real captioning or object-detection Provider through `contrib`.
- Use injected model protocols if weights are downloaded.
- Define grounded caption/object Artifacts with temporal/spatial/source-frame
  linkage and registered persistence.
- Build one narrow Fact extraction builder from real output.
- Prove fact precision and provenance on real fixtures.

**Exit:** at least one objective Fact kind is genuinely built and evaluated. Do
not start generic event/theme frameworks in this phase.

### Phase 2 — Evidence completeness and semantic scenes

**Trigger:** Facts expose missed actions or invalid grouping caused by even frame
sampling and shot/scene conflation.

- Measure adaptive sampling around cuts, motion, dialogue, OCR, and uncertainty.
- Add only the capabilities demanded by the gold set: speaker diarization,
  grounded audio events, richer object/person tracking, and cinematic style.
- Spike shot-to-narrative-scene grouping using real multimodal continuity.
- Record a compatibility ADR before changing or aliasing `SceneCutArtifact` or
  stable public terminology.

**Exit:** narrative-scene boundaries and evidence coverage beat the shot-only
baseline on an expert-labeled set.

### Phase 3 — Persistent entities, Events, and State

**Trigger:** real embeddings/recognition or tracking can identify repeated
characters, objects, and locations with measured error.

- Build persistent entity identity with explicit ambiguous clusters.
- Add dialogue attribution and time-scoped relationships.
- Compose Facts into narrow Event types.
- Add append-only state snapshots/transitions and consistency validation.
- Extend existing builder shapes unless a real input mismatch proves another is
  required.

**Exit:** a multi-scene causal question can be answered from stored knowledge
without rerunning Providers or inventing missing observations.

### Phase 4 — External identity, context, and claim verification

**Trigger:** stable movie anchors and Facts make claim comparison measurable.

- Spike user-supplied/allowlisted sources first.
- Implement edition matching, source policy, minimal excerpts, provenance,
  deduplication, atomic claims, and deterministic checks.
- Verify only observable dialogue/event and production claims initially.
- Keep interpretations attributed without a truth score.
- Write an ADR if external documents need a core Media/Provider contract.

**Exit:** high precision for identity, attribution, and a narrow verdict set;
rights/spoiler/prompt-injection tests pass.

### Phase 5 — Causality, motives, narrative, and philosophy

**Trigger:** Events, State, information flow, and time-scoped relationships exist.

- Start with one reasoner answering a real “why” question and returning competing
  hypotheses plus evidence/counterevidence.
- Separate physical cause, character reason, narrative function, and production
  explanation.
- Add story/presentation reconstruction and information-flow queries.
- Add motif/theme/philosophy dossiers only after recurrence and arc evidence is
  queryable.

**Exit:** experts judge evidence support and non-overclaiming, not merely prose
quality; the reasoner abstains when lower-layer evidence is absent.

### Phase 6 — Cultural scrutiny and reception/iconicity

**Trigger:** grounded objects/practices and the external-source policy are stable;
qualified reviewers and representative evaluation material are available.

- Normalize discovery with curated multilingual vocabularies.
- Preserve community, time, region, source, and variant meanings.
- Build separate internal-pivotal, formal-distinctiveness, memorability, and
  cultural-circulation axes.
- Audit cultural generalization and source/community representation.

**Exit:** culturally specific claims are attributable and reviewable; the system
does not reduce culture to country labels or popularity to iconicity.

### Phase 7 — Forecasting

**Trigger:** reliable current state, unresolved-thread representation, versioned
Intelligence output, and a time-sliced evaluation set exist.

- Build top-k scenario forecasts with an immutable cutoff.
- Start with one series/genre and historical backtesting.
- Calibrate probabilities and support abstention.
- Resolve forecasts append-only after release.

**Exit:** the system beats simple baselines on calibration and consistency without
source leakage. Until then, prediction remains an experimental Application.

### Phase 8 — Comprehensive report Application

**Trigger:** enough of the above exists to satisfy a declared coverage profile.

- Build `MovieScrutinyReport` as a read-only Application over stored evidence,
  knowledge, assessments, and optional forecasts.
- Support spoiler profile, depth profile, languages, evidence expansion, and
  incremental regeneration from cache.
- Never claim that an unsupported section was analyzed.

**Exit:** one analyzed work powers the scrutiny report, searchable timeline,
character dossier, and evidence QA without rerunning expensive inference.

## Architecture decisions that will eventually require ADRs

This research document is not an ADR because it changes no production contract.
The following decisions should receive separate ADRs only when their trigger is
met:

1. Visual shot versus semantic narrative-scene vocabulary and compatibility.
2. Persistent assertion/evidence-link model and verdict vocabulary.
3. External document/network boundary: plugin-only versus new `TextMedia` contract.
4. Event/state representation once the first real Fact composition exists.
5. Intelligence output persistence and whether interpretations belong in
   `EntityStore` or a separate store.
6. Forecast persistence/resolution without contaminating knowledge.
7. Graph/index infrastructure only after a measured real query fails current
   iteration.

Historical ADRs must remain unchanged. New evidence may supersede them through a
new ADR, never by rewriting the old decision.

## Rejected designs

### One multimodal model prompt per movie

Rejected because it loses reproducible intermediate evidence, makes edition and
sampling gaps opaque, couples all reasoning to one model, and cannot support
precise correction or reuse.

### Internet consensus as truth

Rejected because copied pages are not independent sources, production facts and
interpretations have different evidence rules, and popularity does not establish
meaning.

### Theme or cultural label inside an Artifact

Rejected by the Artifact contract. Themes and cultural meanings are reasoning,
not direct observations.

### One confidence score for the whole report

Rejected because coverage, extraction quality, identity certainty,
interpretation strength, source trust, and forecast probability are different
quantities.

### A universal symbol dictionary

Rejected because symbols depend on work, community, period, genre, character,
and formal context; the same object may support several or no symbolic readings.

### Country-to-ritual inference

Rejected as culturally unreliable and likely to amplify stereotypes.

### Creator intention as final authority

Rejected as the sole interpretation. A creator statement is important primary
evidence about a declared intention, but audience, formal, historical, and
critical meanings can still differ.

### Predictions stored as Facts

Rejected because forecasts concern unrealized futures. They need a cutoff,
probabilities, resolution, and a one-way dependency from knowledge to forecast.

### A new graph database now

Rejected by ADRs 0014, 0019, and 0021 until a real, measured query demonstrates
that the existing Entity/EntityStore approach is inadequate.

### Open-web crawling in core

Rejected because network, copyright, source policy, prompt injection, privacy,
and rate limits are optional integration concerns, not mandatory framework core.

## Final recommendation

Adopt this as the long-term product direction, but preserve the repository's
current implementation order.

The most important architectural move is not a new model. It is an explicit
**epistemic contract** that keeps observations, facts, external assertions,
interpretations, and forecasts distinguishable while allowing a report to connect
them. That contract turns “deep movie analysis” from an impressive one-off answer
into SceneForge's intended durable asset: a reusable, inspectable body of
narrative knowledge.

The immediate implementation step remains the one already documented: a real
captioning or object-detection Provider followed by the smallest useful Fact
builder. The comprehensive coverage matrix and evaluation program in this report
should guide which evidence gaps are filled next. Higher-level reasoners should
arrive only when their required lower-level evidence is real.

## Sources

Accessed 2026-07-21. Preprints are identified by their linked publication pages;
their claims should be treated as research evidence, not standards.

[^movienet]: Huang et al., [MovieNet: A Holistic Dataset for Movie Understanding](https://arxiv.org/abs/2007.10937), 2020.

[^movieqa]: Tapaswi et al., [MovieQA: Understanding Stories in Movies through Question-Answering](https://arxiv.org/abs/1512.02902), 2015.

[^tvqa]: Lei et al., [TVQA: Localized, Compositional Video Question Answering](https://arxiv.org/abs/1809.01696), 2018.

[^event-segmentation]: Zacks and Swallow, [Event Segmentation](https://doi.org/10.1111/j.1467-8721.2007.00480.x), 2007.

[^cinema-segmentation]: Zacks et al., [The Brain's Cutting-Room Floor: Segmentation of Narrative Cinema](https://pmc.ncbi.nlm.nih.gov/articles/PMC2955413/), 2010.

[^chatman]: Chatman, [Story and Discourse: Narrative Structure in Fiction and Film](https://eric.ed.gov/?id=ED165141), 1978.

[^bordwell]: Bordwell, [Narration in the Fiction Film](https://uwpress.wisc.edu/Books/N/Narration-in-the-Fiction-Film), 1985.

[^moviegraphs]: Vicol et al., [MovieGraphs: Towards Understanding Human-Centric Situations from Videos](https://arxiv.org/abs/1712.06761), 2018.

[^grounded-description]: Zhou et al., [Grounded Video Description](https://arxiv.org/abs/1812.06587), 2019.

[^moviechat]: Song et al., [MovieChat: From Dense Token to Sparse Memory for Long Video Understanding](https://arxiv.org/abs/2307.16449), CVPR 2024.

[^video-mme]: Fu et al., [Video-MME: The First-Ever Comprehensive Evaluation Benchmark of Multi-modal LLMs in Video Analysis](https://arxiv.org/abs/2405.21075), 2024.

[^temporalbench]: Cai et al., [TemporalBench: Benchmarking Fine-grained Temporal Understanding for Multimodal Video Models](https://arxiv.org/abs/2410.10818), 2024.

[^unesco-ich]: UNESCO, [What is Intangible Cultural Heritage?](https://ich.unesco.org/en/what-is-intangible-heritage-00003).

[^unesco-domains]: UNESCO, [Intangible Heritage Domains in the 2003 Convention](https://ich.unesco.org/en/intangible-heritage-domains-00052).

[^getty-vocab]: Getty Research Institute, [Getty Vocabularies](https://www.getty.edu/research/tools/vocabularies/index.html).

[^getty-data]: Getty Research Institute, [Obtain the Getty Vocabularies](https://www.getty.edu/research/tools/vocabularies/obtain/).

[^fever]: Thorne et al., [FEVER: a Large-scale Dataset for Fact Extraction and VERification](https://aclanthology.org/N18-1074/), NAACL 2018.

[^rag]: Lewis et al., [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401), 2020.

[^alce]: Gao et al., [Enabling Large Language Models to Generate Text with Citations](https://aclanthology.org/2023.emnlp-main.398/), EMNLP 2023.

[^videomem]: Cohendet et al., [VideoMem: Constructing, Analyzing, Predicting Short-term and Long-term Video Memorability](https://arxiv.org/abs/1812.01973), ICCV 2019.

[^event-cloze-critique]: Chambers, [Behind the Scenes of an Evolving Event Cloze Test](https://aclanthology.org/W17-0905/), 2017.

[^docscript]: Mathur et al., [DocScript: Document-level Script Event Prediction](https://aclanthology.org/2024.lrec-main.458/), LREC-COLING 2024.

[^forecast-calibration]: Gneiting, Balabdaoui, and Raftery, [Probabilistic Forecasts, Calibration and Sharpness](https://doi.org/10.1111/j.1467-9868.2007.00587.x), 2007.

[^proper-scoring]: Gneiting and Raftery, [Strictly Proper Scoring Rules, Prediction, and Estimation](https://doi.org/10.1198/016214506000001437), 2007.

[^eidr]: Entertainment Identifier Registry, [EIDR: The Universal Media Identifier](https://www.eidr.org/).

[^eidr-edits]: Entertainment Identifier Registry, [How EIDR Works](https://www.eidr.org/how-we-work).

[^web-annotation]: W3C, [Web Annotation Data Model](https://www.w3.org/TR/annotation-model/), Recommendation, 2017.

[^media-fragments]: W3C, [Media Fragments URI 1.0](https://www.w3.org/TR/media-frags/), Recommendation, 2012.

[^prov-o]: W3C, [PROV-O: The PROV Ontology](https://www.w3.org/TR/prov-o/), Recommendation, 2013.

[^c2pa]: C2PA, [C2PA and Content Credentials Explainer](https://c2pa.org/specifications/specifications/2.2/explainer/Explainer.html).

[^sep]: Stanford Encyclopedia of Philosophy, [About the SEP](https://plato.stanford.edu/about.html).

[^philpapers]: PhilPapers, [About PhilPapers](https://philpapers.org/help/about.html).

[^unesco-ai-ethics]: UNESCO, [Recommendation on the Ethics of Artificial Intelligence](https://www.unesco.org/en/legal-affairs/recommendation-ethics-artificial-intelligence), 2021.

[^cinetechbench]: Zhang et al., [CineTechBench: A Benchmark for Cinematographic Technique Understanding and Generation](https://arxiv.org/abs/2505.15145), 2025 preprint.

[^scene-saliency]: Papalampidi et al., [Select and Summarize: Scene Saliency for Movie Script Summarization](https://aclanthology.org/2024.findings-naacl.218/), NAACL Findings 2024.

[^robots]: IETF, [RFC 9309: Robots Exclusion Protocol](https://www.rfc-editor.org/info/rfc9309/), 2022.

[^us-fair-use]: U.S. Copyright Office, [Fair Use Index](https://www.copyright.gov/fair-use/).

[^eu-dsm]: European Union, [Directive (EU) 2019/790 on Copyright in the Digital Single Market](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019L0790), 2019.

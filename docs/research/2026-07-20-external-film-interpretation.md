# External Film Interpretation as Attributable Evidence

Persian companion: [2026-07-20-external-film-interpretation-fa.md](2026-07-20-external-film-interpretation-fa.md)

**Status:** 📋 proposed research direction — no implementation change

## Question / decision

Should SceneForge retrieve online reviews, analyses, and plot explanations for a film, integrate their useful knowledge, and check their claims against the analysed movie?

## Scope and sub-questions

1. How can external writing improve narrative understanding without overwriting the film’s own evidence?
2. Which claims can be checked automatically, and which are necessarily interpretations?
3. What provenance, copyright, spoiler, and source-quality controls are required?
4. What is the smallest safe architecture to prototype?

## TL;DR

✅ Yes: this would be a valuable **external interpretation layer**. Reviews and essays can provide names, cultural context, competing readings, plot explanations, and thematic hypotheses that frame/audio analysis cannot reliably infer alone. Retrieval-augmented generation is specifically useful when knowledge must be revisable and inspectable rather than only implicit in model parameters.[^1]

⚠️ Do not merge internet text into the movie’s observed facts. Store it as attributed, timestamped source material; extract small claims; then attach a verdict that says what the movie evidence supports—not whether an interpretation is universally “true.”

✅ The first prototype should ingest only user-supplied or explicitly licensed/allowed URLs, retain a minimal excerpt plus metadata and link, generate claim candidates, and verify only time-groundable claims against SceneForge artifacts. It should not crawl the open web or reproduce full reviews.

## Findings

### 1. External analysis fills a real evidence gap

✅ Movie understanding is inherently multimodal and benefits from metadata, plot descriptions, subtitles, and aligned descriptions in addition to video. MovieNet’s movie-understanding dataset includes trailers, photos, plot descriptions, scene boundaries, characters, actions/places, and cinematic-style annotations.[^2]

✅ Reviews and analysis can add useful context: character names, a critic’s reading of a motif, production/cultural context, ambiguity explanations, and multiple interpretations. These are complementary to locally observed frames, cuts, dialogue, and detections.

⚠️ An online explanation can be wrong, may describe a different cut/edition, and may contain spoilers or fan speculation. It is an assertion by a source, not an observation of the input file.

### 2. Separate four kinds of statements

| Statement type | Example | Can SceneForge check it? | Correct verdict |
|---|---|---|---|
| Observable event | “The letter is burned before the final cut.” | Often, if a timestamped visual/audio/OCR observation exists | supported / contradicted / insufficient evidence |
| Dialogue claim | “A says X to B.” | Partly, through transcript plus speaker/face evidence | supported / contradicted / insufficient evidence |
| Production fact | “The film was released in 1999.” | Not from the movie file; needs an authoritative external source | corroborated by source(s) / disputed / unverified |
| Interpretation | “The house represents grief.” | No objective truth test; compare evidence and attribution | attributed interpretation; evidence cited / contested / not assessable |

✅ This is the central rule: a claim about what appears or is said can be tested against film evidence; a claim about history needs trustworthy external corroboration; a thematic reading must remain attributed to its author.

### 3. Provenance is a first-class requirement

✅ Every imported source should have: canonical URL, title, publisher, author if available, publication and retrieval dates, language, licence/permission state, exact quoted excerpt or a short stored digest, content hash, source edition/cut if stated, and the query that retrieved it.

✅ Store claims separately from source documents. Each `ExternalClaim` needs its source ID, claim text, claim type, subject, optional film time range, extraction method/model/version, and links to supporting or opposing evidence.

✅ This follows the general provenance principle that trust signals identify who made an assertion and bind it to evidence; C2PA likewise distinguishes verifiable provenance from a judgment that content is “good” or “bad.”[^3]

### 4. Verification must be evidence-aware, not a second guesser LLM

✅ Build a **claim-evidence matrix**, not a single confidence score:

1. Retrieve permitted sources for the exact film title, release year, and edition.
2. Preserve source metadata and a short permitted excerpt; deduplicate mirrors and syndications.
3. Extract atomic claims, preserving the source wording and whether the statement is fact or interpretation.
4. Retrieve SceneForge artifacts relevant to the claim: time ranges, transcript segments, frames, OCR, detected entities, and future embeddings.
5. Apply deterministic checks first: time overlap, quoted-dialogue match, entity co-occurrence, and source agreement.
6. Let a model write an explanation only from the retrieved evidence, with links to both the source and movie artifacts.
7. Return one of: `supported`, `partially_supported`, `contradicted`, `insufficient_movie_evidence`, `corroborated_externally`, `contested_interpretation`, or `not_assessable`.

⚠️ A model must not upgrade “many websites repeat this” into truth. Independent sources and direct movie evidence are different evidence classes. Search/fact-check tooling also requires transparent claims, source attribution, methods, citations, and an error-correction path.[^4]

### 5. Proposed SceneForge architecture

```text
Opt-in source connector / user URLs
                ↓
ExternalSourceArtifact (URL, metadata, permitted excerpt, hash)
                ↓
ExternalClaimExtractor
                ↓
ExternalClaim entities ──────→ ClaimEvidenceVerifier ←──── Movie artifacts/entities
                ↓                         ↓
        Interpretation/claim graph   VerificationAssessment entity
                ↓
    Narrative answer with two evidence lanes: movie | external
```

✅ Keep this outside the current core `Media → Provider → Artifact` path at first. It is a separate capability domain with network, licensing, privacy, and source-policy concerns. A plugin or opt-in provider is a better fit than making ordinary local movie analysis depend on the web.

### 6. Source policy and rights

⚠️ Do not scrape arbitrary sites, bypass access controls, or store/re-publish full reviews. Respect source terms, robots directives, paywalls, and copyright. Prefer APIs, RSS/official feeds, public-domain or Creative Commons sources, explicit user-provided text/URLs, and links plus short quotations where permitted.

✅ Maintain a source allowlist with source type and policy: `official`, `licensed database`, `professional criticism`, `academic`, `user review`, `fan analysis`, or `unknown`. The ranking should favour primary/authoritative sources for production facts and diverse critical voices for interpretation.

⚠️ Make spoilers explicit: default to a source’s spoiler label where available and otherwise treat plot explanations and ending analyses as spoiler-bearing. Never show retrieved spoilers before a user opts in.

### 7. Smallest useful prototype

📋 Implement an opt-in `ExternalSourceProvider` that accepts user-provided URLs/text rather than searching the open web. It creates `ExternalSourceArtifact`s with provenance and a policy decision (`accepted`, `metadata_only`, `rejected`).

📋 Implement `ExternalClaimBuilder` for a constrained set of claims: quoted dialogue, described event, named character, and production fact. Require source links for every claim.

📋 Implement `ClaimEvidenceVerifier` only for dialogue and timestamped event claims. It should emit evidence links and the limited verdict vocabulary above. Keep thematic/ending explanations as attributed interpretations without a truth score.

📋 Evaluate on a hand-labelled set of 10–20 films/clips and sources. Measure source attribution accuracy, claim extraction precision, verification precision, false contradictions caused by transcript/shot errors, and whether reviewers judge the evidence display helpful.

## Recommendation

Proceed, but name it **External Interpretation & Claim Verification**, not “internet truth checking.” Its value is to make the project richer, plural, and inspectable while preserving a strict boundary:

- **Movie evidence**: what SceneForge observed from this exact media file.
- **External evidence**: what a named outside source says.
- **Assessment**: how the two relate, with reasons and links.

Start with user-supplied or licensed sources, atomic claims, provenance, and movie-grounded checks. Add web search only after a source-policy, rights, privacy, and spoiler specification exists.

## Status

📋 Findings ready for a feature specification and data-model proposal. No production code was changed.

## Sources

Accessed 2026-07-20.

[^1]: Lewis et al., [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401), 2020.
[^2]: Huang et al., [MovieNet: A Holistic Dataset for Movie Understanding](https://arxiv.org/abs/2007.10937), 2020.
[^3]: C2PA, [Content Credentials Technical Specification](https://spec.c2pa.org/specifications/specifications/1.2/specs/C2PA_Specification.html).
[^4]: Google Search Central, [Fact check (`ClaimReview`) structured data](https://developers.google.com/search/docs/appearance/structured-data/factcheck); Google, [Fact Check Tools API](https://developers.google.com/fact-check/tools/api/reference/rest/).

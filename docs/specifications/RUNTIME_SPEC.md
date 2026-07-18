# Runtime Specification

## Purpose

The runtime package contains execution-time abstractions.

Unlike `core`, runtime objects are ephemeral and exist only
during processing.

## Components

- ProcessingContext
- Cancellation
- Progress
- Configuration

## Responsibilities

Runtime components may:

- Store execution state
- Report progress
- Support cancellation
- Provide shared execution metadata

Runtime components must not:

- Contain business logic
- Modify Artifacts
- Register Providers

## ProcessingContext: no longer orphaned

`ProcessingContext` existed in this layer for a while before anything
actually used it — `Pipeline` defined the parameter but never called
`ensure_running()` or wrote to it. That's fixed: `Pipeline.run()` /
`run_detailed()` now create a default `ProcessingContext` if none is
passed, check `ensure_running()` before each attempt (so a caller can
cancel a long-running batch from another thread/task), and record
per-run timing into `context.metadata`. `AsyncPipeline` does the same.
See `docs/adr/0003-pipeline-orchestration.md`'s update note.

```python
from sceneforge.runtime.processing_context import ProcessingContext

context = ProcessingContext()
pipeline.run(media, context=context)
...
context.cancel()  # from another thread/task -- the next ensure_running() check raises
```

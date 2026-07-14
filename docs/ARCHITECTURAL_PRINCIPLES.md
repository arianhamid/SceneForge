Media objects know NOTHING about providers.

Providers know EVERYTHING about media objects.

## Prefer boring over clever.

If two designs solve the same problem, prefer the one that is
more readable, more predictable, and easier for contributors
to understand.

Core abstractions should be understandable in isolation.

If a new contributor cannot understand a core class without
reading five other files, the abstraction is too complex.

Everything is immutable.

Everything is serializable.

Everything is typed.

Everything is pluggable.

Providers never depend on applications.

Applications never modify artifacts.

Knowledge never modifies artifacts.

Reasoning never modifies knowledge.

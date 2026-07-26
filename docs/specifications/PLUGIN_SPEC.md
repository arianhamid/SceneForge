# Plugin Specification

## Purpose

Plugins extend SceneForge by providing one or more Providers.

## Responsibilities

Plugins:

- expose metadata
- expose providers

Plugins do not:

- process artifacts
- execute pipelines
- contain runtime state

## Design Philosophy

A plugin is a deployment unit.

A provider is a processing unit.

## Discovery

Installing a plugin package must not require editing the host
application's code — that was the promise this document made before an
actual discovery mechanism existed. `PluginRegistry.discover()`
(`sceneforge/plugins/registry.py`) now makes it real, via Python's
standard `importlib.metadata.entry_points()`:

A plugin package declares itself once, in its own `pyproject.toml`:

```toml
[project.entry-points."sceneforge.plugins"]
my_plugin = "my_package.plugin:MyPlugin"
```

A host application picks it up automatically just by having the package
installed:

```python
from sceneforge.plugins.registry import PluginRegistry

registry = PluginRegistry()
newly_registered = (
    registry.discover()
)  # finds every installed sceneforge.plugins entry point
```

`discover()` is safe to call more than once — already-registered
plugins (by `id`) are skipped rather than raising. A broken entry point
(a plugin package with a missing dependency, an import error) is
skipped rather than crashing discovery for every other plugin — one bad
package must not prevent the host application from starting.

Manual registration (`registry.register(plugin_instance)`) still works
for plugins constructed in-process rather than discovered — useful for
tests, or a plugin that needs constructor arguments discovery can't
supply.

# SceneForge Engineering Philosophy

> Great software is not measured by the amount of code it contains,
> but by the amount of complexity it removes.

---

# Our Standard

SceneForge is built to be understandable before it is impressive.

A contributor should be able to navigate the architecture, understand the
responsibilities of each module, and confidently extend the framework without
guesswork.

---

# We Optimize For

- Clarity over cleverness
- Stability over novelty
- Reusability over duplication
- Architecture over shortcuts
- Long-term maintainability over short-term speed

---

# Every Module Should Answer

1. What problem does it solve?
2. Why does it exist?
3. What are its responsibilities?
4. What are its boundaries?
5. Can it be replaced without affecting the rest of the framework?

If these questions cannot be answered clearly, the design should be revisited.

---

# Documentation Is Code

Documentation is not written after implementation.

Documentation defines the contract that implementation fulfills.

---

# Review Before Rewrite

When improving the framework:

- Prefer simplifying existing abstractions.
- Avoid introducing duplicate concepts.
- Preserve backwards compatibility whenever practical.
- Document architectural changes before implementing them.

---

# Leave It Better

Every contribution, no matter how small, should leave the repository in a better state than it was found.

That may mean:

- clearer naming
- better documentation
- simpler APIs
- improved tests
- cleaner architecture

Progress is measured by continuous improvement.

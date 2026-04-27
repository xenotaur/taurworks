---
id: PRINCIPLES-CORE
title: Taurworks Working Principles
status: active
---

# Principles

1. **Shared core, separate responsibilities**
   - Use one executable with separate `project` and `dev` namespaces while sharing configuration/discovery/diagnostic internals.
2. **Explicit over implicit automation**
   - Prefer commands and generated files that users can inspect and run directly.
3. **Standards delegation over tool replacement**
   - `taurworks dev` orchestrates standard tools and project scripts rather than replacing them with a proprietary build/test/lint system.
4. **Transparent command resolution**
   - Resolve workflow commands predictably and document what command was selected and why.
5. **Conservative shell integration**
   - Avoid hidden shell mutations; keep environment activation explicit and inspectable.
6. **Safe defaults for high-risk actions**
   - Destructive or environment-changing operations require conservative defaults and clear operator intent.
7. **Idempotent lifecycle behavior**
   - `refresh`-style behavior should safely restore missing project components without destructive side effects.
8. **Local-first, filesystem-visible state**
   - Project setup state should live in predictable locations such as `<workspace>/<project>/.taurworks`.
9. **Conservative behavior changes**
   - Preserve compatibility commands until an explicit migration path exists.

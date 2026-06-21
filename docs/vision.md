# 🌌 Omnigent Vision

## The Core Philosophy
Omnigent exists to cure context chaos. Modern developers juggle dozens of disconnected AI chat windows, losing track of prompts, context, and project history. We believe developers shouldn't just *chat* with AI—they should **command a fleet**.

Omnigent gives developers a calm, inspectable, terminal-based dashboard to monitor, steer, and manage a team of AI workers.

### 1. Sessions are Cheap
Creating a new agent should feel as frictionless as opening a new tab. Forking agents and running concurrent specialized agents (e.g., "Frontend Analyzer" and "Backend Tester") is highly encouraged.

### 2. The Broker is the Source of Truth
Workers do **not** blindly mutate global state. Instead:
- Workers propose updates.
- The Broker commits them.
- All actions are recorded in an append-only event log.

### 3. Artifacts are First-Class Citizens
Outputs aren't lost in a scrolling chat window. Code files, research findings, and architecture plans are stored explicitly as "Artifacts" that can be reviewed, committed, or rejected.

### 4. A Calm "Mission Control" Interface
Inspired by `htop`, `tmux`, and `k9s`. No flashing banners, no chaotic UI. Just a focused terminal environment showing you exactly what your fleet is doing.

## Future Horizons
While the MVP runs local processes via Celery, the ultimate vision for Omnigent is **One Agent = One Sandboxed Container**. In the future, each AI worker will execute inside its own isolated Docker or Podman container with full terminal access, safely separated from the host machine while reporting back to the Broker.

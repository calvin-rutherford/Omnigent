# Omnigent Changelog

## [Unreleased] - Command Plane Architecture Pivot

### Planned Architecture Changes
- **Human-in-the-Loop Approvals**: Worker agents that request dangerous actions (e.g., executing bash commands) will send an approval request to a background "Approval Queue" in the REPL. This prevents blocking the main interface, allowing the user to continue working and approve the request asynchronously.
- **Persistent Sandboxing**: Worker execution will be decoupled from the core orchestration engine. Workers will operate inside isolated, persistent sandboxes (e.g., long-lived Docker containers). Persistence ensures agents do not have to repeatedly reinstall dependencies (like `npm` or `pip`) across sessions.
- **Statefulness Controls**: The Broker's conversation memory will be fully controllable via two methods:
  - A global toggle in the UI/settings to switch between stateful and stateless modes.
  - On-the-fly slash commands (e.g., `/stateless`) to issue one-off commands without pulling historical context.
- **Fleet Supervision**: New REPL commands (e.g., `!fleet`) to view active agents, queue depth, and resource usage.
- **Graceful Lifecycle Controls**: Implementation of `!pause` and `!kill` signals backed by Redis flags, ensuring workers safely wind down without leaving orphaned processes.

## [Current Version] - Base Infrastructure Pivot

### Added
- **Native CLI REPL**: Replaced the rigid Textual TUI with a standard, fluid terminal REPL using `prompt_toolkit` and `rich`. WebSocket events stream gracefully above the permanent bottom prompt bar using `patch_stdout`.
- **Shell Passthrough**: Retained the `!command` feature to allow local host shell execution directly from the REPL.

### Changed
- **Broker Engine**: Completely refactored `BrokerAgent` to use the native `google-generativeai` SDK, utilizing `enable_automatic_function_calling=True` and `start_chat()` for robust, native tool orchestration.

### Removed
- **LLM Abstraction Layers**: Removed `litellm` dependency to eliminate function-calling translation bugs and stabilize on Gemini as the core orchestration model.
- **Textual UI**: Deleted the `cli/tui` directory.

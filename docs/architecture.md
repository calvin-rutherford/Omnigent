# 🏗 Omnigent Architecture

Omnigent is designed around an event-driven, broker-worker model. It utilizes a production-grade Python stack to ensure stability and scalability.

## High-Level Diagram

```mermaid
graph TD
    User([User]) -->|Natural Language| TUI[Textual TUI Dashboard]
    TUI <-->|WebSockets (Channels)| Django[Django Backend / Broker]
    
    subgraph "Broker Node"
        Django <--> PG[(PostgreSQL)]
        Django -->|Task Dispatch| RMQ[RabbitMQ Message Broker]
        Django <--> BrokerAgent[Broker Agent LLM]
    end
    
    subgraph "Worker Fleet"
        RMQ --> Celery1[Celery Worker: Research]
        RMQ --> Celery2[Celery Worker: Coding]
    end
    
    BrokerAgent --> LiteLLM[Universal Provider Layer]
    Celery1 --> LiteLLM
    Celery2 --> LiteLLM
    
    LiteLLM --> APIs((Gemini / OpenAI / Anthropic / Local))
```

## Core Abstractions

### 1. The Broker Agent
The Broker isn't just a router—it's an LLM equipped with Function Calling. When a user types a command in the TUI, the Broker interprets the intent. If a complex task is requested, the Broker autonomously invokes the `spawn_agent` tool to dispatch a Celery worker.

### 2. Append-Only Event Log
Every action is recorded in the `EventLog` database table. 
- `AgentCreated`
- `TaskAssigned`
- `ArtifactCreated`
- `MessageSent`
The entire project history can be reconstructed from these events.

### 3. Persistent Agent Sessions
Agents are represented as database rows (`Agent` model) with distinct statuses (`Running`, `Waiting`, `Complete`, `Error`). A Celery task represents the active execution thread of an Agent.

### 4. Artifacts
When an agent produces code or documentation, it generates an `Artifact` record with a status of `Proposed`. The Broker (or User) can then review and transition it to `Committed`.

### 5. Universal Provider Layer
Thanks to **LiteLLM**, Omnigent is model-agnostic. Workers and the Broker communicate with a universal provider interface, allowing users to swap between Gemini, OpenAI, Anthropic, or local Ollama models simply by changing the `.env` variable.

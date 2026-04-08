# GLYPH8 SaaS and Event System Architecture

## Current state

This repository currently has a small extractor and a new event-driven engine prototype.
It is not yet a complete SaaS product, but the architecture is arranged so it can grow into one.

## Goals

- Accept behavior data as events.
- Categorize events into 3 cultural levels.
- Track probability and choice history like an "arcade casino" layer.
- Translate pattern extraction into font/paleographic output for designers.
- Keep the system strictly scoped to user instruction and math-based objectives.
- Produce responses in a closed loop with evaluation against prior data.

## Key concepts

### Event-based workflow

1. User submits an event entry with category, description, probability, and metadata.
2. The system categorizes the event into one of three cultural levels.
3. The event is banded in a vector-style score (alpha/beta/gamma) using global event statistics.
4. The event is recorded, audited, and analyzed against prior event data.
5. The engine generates a small set of candidate outputs:
   - spec
   - definition
   - artifact
   - code
6. The outputs are ranked by confidence, probability, and the overall mean band.

### Constraint-driven behavior

- The engine should not drift into suggestions or interpretation unless asked.
- It should only act when a clear instruction is present.
- Scope is enforced with term matching and explicit user constraints.
- Majority bias is avoided by weighting structural and historical evidence.
- Context references are stored and retrieved for compact reasoning when specific information is required.
- An audit trail tracks event ingestion, band evaluations, and report creation.

### Arcade/casino probability layer

- Choices can be ranked by expected probability.
- Selection depends on observed category frequency and explicit user weights.
- The engine can track probability growth across decisions and use that to choose next questions.

### Font / paleographic extraction

- The system can produce a font spec or a glyph package from event metadata.
- This is represented as a builder function in the current prototype.
- A future version could convert extracted paleographic patterns into actual font assets.

## SaaS-readiness checklist

- [x] Event ingestion model
- [x] Behavior analytics and probability engine
- [x] Candidate response generation
- [ ] API layer / web service
- [ ] Persistent storage and user sessions
- [ ] Landing page and interactive UI
- [ ] Formal constraint enforcement and guardrails
- [ ] Documentation and onboarding flow

## Recommended next steps

1. Add a minimal API endpoint around `glyph_system.GlyphEngine`.
2. Build a landing page that accepts event input, displays the three candidate responses, and shows probability analytics.
3. Create a strict task filter so the engine only answers when the user asks for help or when an event is submitted.
4. Develop a front-end game layer for selection tracking and probability growth.
5. Persist event history and use it to further narrow responses.

## How to keep the system on-task

- Make the user constraint the highest-priority input.
- Treat every new entry as a single event with a fixed scope.
- Use a three-step response process: receive, evaluate against prior data, generate narrowed candidate output.
- Avoid offering next steps or critique unless explicitly requested.
- Rank output by relevance, reason, and scope before any other factor.

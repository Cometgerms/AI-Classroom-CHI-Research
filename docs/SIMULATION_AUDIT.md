# First-class simulation audit — 2026-09-19

Read AGENTS, current state, architecture, decisions, models and latest XVF handoff before edits. Baseline: 55 passed, 1 hardware test deselected. Preserve existing uncommitted XVF work.

Conflicts: scenarios directly set semantic activity; sensor collection does not feed the estimator/agent. No normalized camera contract, session replay or split basic/AI simulation profiles. Researcher console starts visible and controlled-failure evidence can leak to participant state. Hybrid config rejects known but unimplemented adapters at parsing time rather than reporting actual adapter availability. No physical projector/PTZ integration is authorized by this task.

Plan: data-driven timestamped normalized observations through one fusion/state/authority loop; separate explicit experiment injections; persistent replay inputs plus existing decision/action logs; profile-based adapter factories, honest unavailable placeholders for deferred real AV protocols, and participant-safe study UI. Keep generic audio interfaces and original FakeAgent. Existing semantic injection becomes debug-only. No model, hardware, or GPU required for basic simulation/CI.

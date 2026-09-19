# Current state — 2026-09-19

**The researcher console is preserved but product UI/functionality is now the primary implementation priority. Research tooling is preserved but temporarily frozen while the instructor-facing product interaction is developed.**

**Product:** `/` opens Agentic Classroom with AI Mode Off / Assist / Auto, room/AI/recording health, readable activity, separate program preview and room display, camera/follow/source/audio/recording controls, lightweight suggestions, recent actions, safe latest-action Undo and Take Control. `/devices`, `/settings` and `/dev` separate availability, preferences and diagnostics. No research controls appear on the normal route; old query flags do not change it. [Product guide](PRODUCT.md).

**Architecture:** typed InstructorAppState from `/api/instructor/state` projects shared RoomState/agent/delegation/adapters without research metadata. AI modes remain independent of simulation/hybrid/hardware profiles. Async Qwen availability/inference does not block manual operation. Product approvals expire/bind to ID. Follow/blank/mute are typed intents. VideoEngine owns layout/recording/status/preview; simulated engine works, OBS engine explicitly disconnected until transport implementation. No physical protocols added.

**Primary development:** simulation-ai with real local Qwen3:8b and simulated physical devices. Launch wrappers default to this profile; explicit simulation-basic remains model/hardware-free and uses the same UI. Current local backend/frontend left running at localhost:8000/5173. Recording stopped, AI Off after verification; choose Assist/Auto to use Qwen.

**Preserved research:** old console/component/styles at `/research`, participant presentation at `/research?view=participant`; study routes/models/logs/replay/scenarios/errors unchanged except shared-device/routing compatibility. Protected CHI V1 is instructor/TA-only, one participant/one facilitator, no students/actors. DoA and multi-person capabilities remain optional/deferred. No counterbalancing/questionnaire/session UX work in this milestone.

**Verification:** **126 passed, 1 hardware-optional deselected**; frontend production build passed; desktop browser verified actual Qwen Assist/Apply, Auto/action/Undo, recording/timer and Take Control without stopping recording, device health, settings/diagnostics, isolated research route. No physical AV or Windows success claimed. Existing model/dependency versions unchanged.

**Known limits:** illustrated preview, simulated recording writes no file, OBS transport not implemented. Hardware calibration/mapping/destination setup is clearly described as future adapter work. No full setup wizard; no physical touchscreen QA. Single-process/shared-room state, local route separation not authentication, bounded in-memory product history. Product Undo is latest-action/simulation only and never implicitly reverses recording transport. [Detailed boundaries](PRODUCT.md).

**Next:** improve instructor interaction from use, then connect OBSVideoEngine and physical adapters one by one without changing product UX. Keep research tooling frozen until explicitly reprioritized.

**Latest handoff:** [2026-09-19_1642_product-first-instructor-ui.md](HANDOFFS/2026-09-19_1642_product-first-instructor-ui.md). Earlier handoffs immutable. Changes since 33504d0 remain uncommitted.

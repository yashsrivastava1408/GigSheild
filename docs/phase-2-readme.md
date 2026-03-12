# Phase 2 Readme

Phase 2 starts after the completion of the core policy, claims, trust-score, and disruption workflows delivered in Phase 1.

This phase is focused on making GigShield operationally usable without expanding the security scope prematurely.

## Decisions locked for Phase 2

- Payments are considered complete for this phase.
- OTP delivery stays on mock mode for now.
- Security hardening is intentionally deferred to a later dedicated pass.

## Phase 2 goals

1. Strengthen admin operations inside the existing web app.
2. Improve disruption operations using the current internal backend endpoints.
3. Add user-facing activity and notification patterns without depending on real SMS delivery.
4. Keep the implementation deployable from the current monorepo and current API shape.

## Current execution order

1. Admin operations console in the frontend
2. Worker-facing activity and notification experience
3. Better visibility for disruption sync and policy expiry outcomes
4. Documentation updates for the Phase 2 operating model

## Out of scope for now

- OTP provider rollout
- Security hardening and abuse protection
- Splitting worker and admin into separate frontend apps
- Large analytics or reporting infrastructure

## Definition of done

Phase 2 should be considered complete when:

- Admin users can load manual review claims and fraud logs from the existing admin area.
- Admin users can trigger weather sync and policy expiry from the frontend.
- The worker experience exposes a clearer activity timeline based on current policy, claim, payout, and disruption state.
- The project documentation reflects the chosen Phase 2 scope and deferred items.

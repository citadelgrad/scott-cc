# Plan: Refresh Empty-State Copy on the Dashboard

## §1. Background

User research found the current empty-state message on the dashboard
("Nothing here yet.") reads as curt and doesn't tell new users what to do
next.

## §2. Scope

- Update the empty-state string in `DashboardEmptyState.tsx` from
  "Nothing here yet." to "You haven't created a project yet — click **New
  Project** to get started."
- Update the accompanying illustration asset (swap `empty-box.svg` for
  `empty-desk.svg`, purely decorative).
- Update the same copy in the localization bundle for `en-US` only; other
  locales get a follow-up pass tracked separately.
- No changes to any endpoint, data model, auth flow, or component props —
  this is a string and asset swap inside an already-authenticated, already
  server-rendered dashboard shell.

## §3. Out of scope

- Any other locale.
- Any other empty-state screen in the app.

## §4. Rollout

Ship directly to production, no feature flag needed — copy-only change.

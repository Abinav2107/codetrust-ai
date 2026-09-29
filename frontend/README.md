# DebugAgent

DebugAgent is a focused developer workspace for inspecting repositories, reviewing static-analysis findings, asking contextual questions, applying suggested fixes, and reviewing test results. This repository is a polished frontend demo backed by realistic local data and asynchronous mock services.

## Features

- Dashboard with project health, activity, issue counts, and test status.
- Project search, status filtering, local project creation, and workspace entry points.
- IDE-style workspace with file tree, issue-marked source code, editor tabs, and contextual AI assistant.
- Analysis, issue review, suggested diff, apply-fix, test, report, and settings flows.
- Responsive shell with collapsible sidebar, keyboard navigation, command palette, toast feedback, and error boundary.
- Persisted Light, Dark, and System themes with designed dark tokens.

## Getting started

Install Node.js LTS, then run:

```powershell
npm install
npm run dev
```

If PowerShell blocks `npm.ps1`, use the Windows command wrapper:

```powershell
npm.cmd install
npm.cmd run dev
```

Open the local URL Vite prints, usually `http://localhost:5173/`.

Useful checks:

```powershell
npm run lint
npm run build
```

## Architecture

- `src/App.tsx` owns the demo session state and routes views through the existing hash navigation.
- `src/pages/` composes product screens; `src/components/` contains feature and UI primitives.
- `src/data/` contains believable project, issue, test, activity, and source-file fixtures.
- `src/services/` provides asynchronous mock boundaries for analysis, chat, reports, tests, and projects.
- `src/types/` contains the shared TypeScript contracts.
- `src/styles/` contains semantic tokens, global rules, and component layout styles.

## Demo flow

Open Dashboard, enter `acme-dashboard`, open Workspace, inspect `src/services/auth.ts`, run analysis, open the authentication issue, ask the assistant for context, apply the suggested optional-chain fix, then review Tests and Report. Applying the fix updates both issue status and the visible editor line in local state.

## Backend integration

The service modules are the intended API boundary. Replace their delayed fixture responses with repository, analysis, chat, test-run, and report clients without moving business logic into presentation components. `.env.example` documents the only planned backend URL variable; no secret is needed for the demo.

## Project structure

## Where to edit things

- `src/pages/` — full screens.
- `src/components/` — reusable UI and feature sections.
- `src/data/` — demo data used by the frontend.
- `src/services/` — places for API/analysis logic when a backend is connected.
- `src/styles/` — design tokens, global CSS, and component styles.
- `src/hooks/` — reusable React hooks.
- `src/types/` — shared TypeScript types.
- `legacy/` — the original single-file implementation for reference.

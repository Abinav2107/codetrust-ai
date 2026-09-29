# DebugAgent architecture

Think of the app as a small team:

- **pages/** decide what a screen contains.
- **components/** are reusable pieces of the screen.
- **ui/** contains generic building blocks such as buttons, cards, badges and modals.
- **data/** contains the demo data currently used by the frontend.
- **services/** are the place where real API calls can be added later.
- **hooks/** contains reusable React behavior.
- **types/** keeps the data shapes consistent across the project.
- **utils/** contains tiny helpers that do not belong to one screen.
- **styles/** contains the design system and visual rules.

## A real backend later

When the project gets a backend, most changes should happen in `src/services/` rather than inside the UI. For example:

```text
GitHub / backend API
        ↓
src/services/projectService.ts
        ↓
src/pages/ProjectsPage.tsx
        ↓
src/components/dashboard/ProjectTable.tsx
```

That separation makes it easier to replace fake data with real API data without rebuilding the interface.

# DebugAgent — Frontend (Production-Ready Demo)

A self-contained single-file HTML/CSS/JS prototype of the AI Debugging & Testing Agent frontend. No build step, no external dependencies. Just open `index.html` in a browser.

## ✓ What's included (pass 3 — production polish)

**App Shell**
- Responsive sidebar (collapsible on mobile)
- Professional header with search
- Clean navigation with issue/test badges
- Real icons (Lucide-style inline SVG)

**Core Screens**
- **Dashboard**: Projects, issues, tests, recent activity
- **Projects**: Searchable, filterable project list
- **Workspace**: File explorer + code viewer + AI chat
- **Analysis**: Issues with severity filters, search
- **Issue Detail**: Full investigation view with root cause
- **Diff Viewer**: Side-by-side original → suggested
- **Test Results**: Summary + detailed failure analysis
- **Test Detail**: Stack traces and AI integration
- **Final Report**: Executive summary, metrics, recommendations
- **Settings**: 4 tabs with toggles and form controls

**Interactions (State-Driven)**
- Run Analysis: animated analyzing state → completion toast
- File switching: updates code viewer + AI panel
- Apply Fix: rewrites mock code, updates counts
- Chat: working conversation with typing indicator
- Filters & search: real-time updates (projects, issues)
- Settings: tab switching with mock persistence

**UI States**
- Loading indicators (pulse animation on analysis)
- Empty states (no projects, no matches)
- Error states (failed analysis badges)
- Success feedback (toast notifications)
- Keyboard shortcuts (⌘K search, ⌘/ chat, ⌘↵ analyze)

**Responsive Design**
- Desktop (1440px, 1280px, 1024px) — 3-column workspace
- Tablet (768px) — stacked panels
- Mobile (375px) — collapsed sidebar, scrollable code

**Visual Design**
- Professional color system (no gradients, no AI gimmicks)
- Restrained spacing (8px baseline grid)
- Clear hierarchy (24px titles, 12px metadata)
- Subtle shadows and borders (not excessive)
- Smooth transitions (.1s ease)

## ⚡ Key Features

**Developer-Focused**
- Real syntax highlighting (TypeScript, Python, Go)
- Error/warning markers in code
- Issue severity badges (Critical, High, Medium, Low)
- Test results breakdown (18 passed, 2 failed, etc.)
- Stack traces and root cause explanations

**Realistic Mock Data**
- 5 issues across multiple files
- 6 tests (4 passed, 2 failed, 1 skipped)
- 4 projects in different states
- Full issue details with suggested fixes

**Connected Workflow**
- Open issue → view code location
- Ask AI → jumps to workspace
- Failed test → open code + ask AI
- Apply fix → updates sidebar counts

## 📱 Browser Compatibility

Modern browsers (Chrome, Safari, Firefox, Edge). No IE support.

## 🚀 Next Steps: Porting to React/TypeScript

This static prototype is the complete visual/behavior reference. To build a real production app:

```
npm create vite@latest debugagent -- --template react-ts
npm install -D tailwindcss shadcn-ui lucide-react
npm install @monaco-editor/react
```

Use this folder structure:

```
src/
  components/
    layout/
      Sidebar.tsx
      Header.tsx
      PageContainer.tsx
    dashboard/
      StatCard.tsx
      ProjectTable.tsx
      RecentActivity.tsx
    workspace/
      FileExplorer.tsx
      CodeEditor.tsx  (wrap Monaco)
      AIAssistant.tsx
    issues/
      IssueList.tsx
      IssueDetail.tsx
      DiffViewer.tsx
    tests/
      TestTable.tsx
      TestDetail.tsx
    reports/
      ReportSummary.tsx
      ReportSection.tsx
    ui/  (shadcn components)
      Button.tsx
      Card.tsx
      Badge.tsx
      etc.
  services/
    projects.ts
    analysis.ts
    issues.ts
    tests.ts
    reports.ts
    chat.ts
  hooks/
    useNavigation.ts
    useWorkspace.ts
  App.tsx
  index.css
```

All styling, colors, spacing, and interactions from `index.html` should map 1:1 to Tailwind classes and React state.

## 🎨 Design System

**Colors**
- Background: #F8FAFC
- Surface: #FFFFFF
- Text: #111827 / #64748B
- Primary: #1D4ED8
- Success: #16A34A
- Error: #DC2626
- Warning: #D97706

**Typography**
- Font: Inter (fallback: system-ui, sans-serif)
- Title: 24px / 600
- Heading: 14.5px / 600
- Body: 14px
- Metadata: 12px

**Spacing**
- Base: 8px
- Common: 12px, 16px, 20px, 24px
- Cards: 8px radius
- Buttons: 6px radius

## 📄 License

Built for hackathon demo. Use freely for reference.

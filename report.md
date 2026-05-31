# GuardianHealth Frontend Exploration Report

**Generated:** May 28, 2026
**Deployed URL:** https://yoflynzmkm674.kimi.page

---

## 1. Executive Summary

GuardianHealth is a professional AI-powered medical triage single-page application (SPA) built with React 18, TypeScript, Vite, and Tailwind CSS. The application features a dark clinical theme optimized for healthcare use, with two primary views: a Chat interface for symptom analysis and an Eval dashboard displaying G-Eval benchmark results from the Kaggle Disease Diagnosis Dataset. The frontend implements a comprehensive component architecture with 12+ specialized components, JWT-based authentication, privacy badges, audit logging, and structured diagnosis cards.

---

## 2. Pages / Screens

The application uses conditional rendering with no client-side router. Navigation is handled via a tab switcher in the header.

| View | Tab | Component | Description |
|------|-----|-----------|-------------|
| Chat | chat | ChatInterface | Main triage chat interface where users describe symptoms and receive AI analysis |
| Eval | eval | KaggleEvalPage | Static benchmark results page showing G-Eval scores from the Kaggle Disease Diagnosis Dataset |

**Navigation State:**
```typescript
const [activeTab, setActiveTab] = useState<'chat' | 'eval'>('chat');
```

Tab switching uses Framer Motion's `layoutId` for smooth animated transitions between Chat and Eval views.

---

## 3. Component Architecture (14 Components)

### 3.1 Core Components

| Component | Purpose | File |
|-----------|---------|------|
| **App.tsx** | Root shell. Manages `activeTab`, `sidebarOpen`, `authModalOpen`. Wraps everything in `AuthProvider`. | `src/App.tsx` |
| **ChatInterface** | Core chat UI. Displays message history (user bubbles + bot cards), handles input, sends messages to `/triage`, renders different bot message types (triage, diagnosis, emergency, follow-up, rejected). | `src/components/ChatInterface.tsx` |
| **Sidebar** | Left sidebar (visible only when logged in). Lists previous chats with titles/dates/symptom tags. Has "New Consultation" button. Responsive with mobile overlay. | `src/components/Sidebar.tsx` |
| **AuthModal** | Login/register modal. Toggles between sign-in and create-account forms. Calls `/login` and `/register`. Includes password visibility toggle. | `src/components/AuthModal.tsx` |

### 3.2 Triage / Diagnosis Components

| Component | Purpose | File |
|-----------|---------|------|
| **TriageResult** | Renders structured triage/diagnosis cards. Two modes: triage (level, reasoning, red flags, remedies) and disease (name, confidence bar, symptoms, all_predictions, care advice, OTC products). Includes disclaimer footer. | `src/components/TriageResult.tsx` |
| **PrivacyBadge** | Small inline badge above bot messages showing PII status: "Privacy Verified" (green) or "PII Redacted" (amber). | `src/components/PrivacyBadge.tsx` |
| **RejectedMessage** | Styled banner shown when the backend rejects a non-health query (`status === 'rejected'`). | `src/components/RejectedMessage.tsx` |
| **ResearchOverview** | Expandable PubMed research card. Shows AI-generated summary, article count, expandable abstracts with journal/year/PMID links, and medical disclaimer. | `src/components/ResearchOverview.tsx` |

### 3.3 Governance / Audit Components

| Component | Purpose | File |
|-----------|---------|------|
| **AuditLog** | Right-side governance panel (visible only when not logged in). Shows SHA-256 audit hashes with "GOVERNED", "ANONYMIZED", "VERIFIED" badges. HIPAA compliant footer. | `src/components/AuditLog.tsx` |

### 3.4 Evaluation Components

| Component | Purpose | File |
|-----------|---------|------|
| **KaggleEvalPage** | Static eval results page (the current "Eval" tab). Hard-coded summary + 20-case results from pre-run benchmark. No live API calls. Features filterable table with expandable detail rows. | `src/components/KaggleEvalPage.tsx` |

### 3.5 Context & Hooks

| Component | Purpose | File |
|-----------|---------|------|
| **AuthContext** | Global auth state with `useContext`. Persists token and username to `localStorage`. Provides `login`, `register`, `logout` methods. | `src/context/AuthContext.tsx` |
| **useTriage** | Custom hook managing messages, loading state, chat ID. Exposes `sendMessage`, `loadChat`, `newChat`, `deleteChat`. | `src/hooks/useTriage.ts` |
| **useSidebar** | Custom hook fetching chat list from `/chats` endpoint. | `src/hooks/useSidebar.ts` |

---

## 4. API Integration

All backend calls go through an axios instance in `src/utils/api.ts`.

**Base URL Configuration:**
- Dev: `/api` (proxied by Vite to `http://localhost:8000`)
- Prod: `https://r5t9bf3p0g.execute-api.ap-southeast-2.amazonaws.com/Stage`
- Override: `VITE_API_BASE_URL`

### Endpoint Matrix

| Endpoint | Method | Called From | Purpose |
|----------|--------|-------------|---------|
| `/login` | POST | `AuthContext.tsx` | Authenticate user, returns `access_token` + `username` |
| `/register` | POST | `AuthContext.tsx` | Create account, returns `access_token` + `username` |
| `/triage` | POST | `useTriage.ts` | Main triage endpoint. Payload: `{ query, chat_id, conversation_history }` |
| `/chats` | GET | `useSidebar.ts` | List all chats for logged-in user |
| `/chats/:id` | GET | `useTriage.ts` | Load message history for a specific chat |
| `/chats/:id` | DELETE | `useTriage.ts` | Delete a chat |

**Auth:** JWT Bearer token attached to all requests via `api.defaults.headers.common['Authorization']` after login. Response interceptor handles 401 by clearing localStorage and reloading.

---

## 5. State Management

No Redux, Zustand, or React Query. State is managed with plain React hooks:

| State | Location | Description |
|-------|----------|-------------|
| Auth (user, token) | `AuthContext` | Global auth state. Persists to `localStorage`. |
| Messages / Input | `ChatInterface` | `messages`, `input` state |
| Chat list | `Sidebar` (via `useSidebar`) | `chats` array fetched from `/chats` |
| Active tab | `App` | `activeTab` ('chat' \| 'eval') |
| Sidebar open | `App` | `sidebarOpen` boolean |
| Auth modal | `App` | `authModalOpen` boolean |
| Current chat ID | `useTriage` | `currentChatId` |

---

## 6. Design System & Styling

### 6.1 Color Palette (Dark Medical Theme)

| Token | HSL Value | Usage |
|-------|-----------|-------|
| Background | `220 20% 4%` | Main app background |
| Card | `220 18% 7%` | Card/panel backgrounds |
| Primary (Teal) | `174 72% 38%` | Primary actions, accents |
| Muted | `220 15% 18%` | Secondary backgrounds |
| Border | `220 12% 18%` | Borders, dividers |
| Triage Emergency | `0 72% 50%` | Emergency-level triage |
| Triage Urgent | `25 85% 50%` | Urgent-level triage |
| Triage Moderate | `45 85% 45%` | Moderate-level triage |
| Triage Mild | `174 72% 38%` | Mild-level triage |
| Triage Self-Care | `220 40% 55%` | Self-care triage |

### 6.2 Typography

- **Font Family:** Inter (Google Fonts) with system fallbacks
- **Hierarchy:** 10px (labels) → 11px (badges) → 12px (metadata) → 13px (body) → 14px (UI) → 16px (headings) → 24px (hero)

### 6.3 Key UI Patterns

- **Glass Panels:** `bg-card/80 backdrop-blur-xl border border-border/60` for modals and elevated surfaces
- **Glow Effects:** Teal glow for primary elements (`glow-teal`), red glow for alerts (`glow-red`)
- **Gradient Text:** Used for brand accents with `background-clip: text`
- **Typing Animation:** Three-dot bounce animation for loading states
- **Shimmer Effect:** Skeleton loading animation with gradient sweep

---

## 7. Special Features

### 7.1 G-Eval / LLM-as-Judge Scoring

The Eval page displays benchmark data with these metrics (1-5 scale):
- **Relevance:** 4.35/5
- **Safety:** 4.65/5
- **Coherence:** 4.50/5
- **Groundedness:** 4.20/5
- **Overall:** 4.43/5

Hallucination detection and PII leakage checks are included in the dataset. The benchmark includes 20 test cases covering normal diagnoses, PII scrubbing tests, prescription refusal, and non-health query rejection.

### 7.2 Privacy / PII Scrubbing

- **PrivacyBadge** displays per-message privacy status
- PII cases explicitly test that names/addresses are redacted
- 0% PII leak rate in the benchmark dataset

### 7.3 Audit / Governance

- **AuditLog** shows SHA-256 hashes for interactions
- Only visible to anonymous (non-logged-in) users
- HIPAA Compliant badge displayed
- Supports "GOVERNED", "ANONYMIZED", "VERIFIED" status badges

### 7.4 OTC Product Links

**TriageResult** renders clickable tags for OTC products that link to Blinkit (`https://blinkit.com/s/?q=...`).

### 7.5 Force Triage Button

When the backend returns `status === 'follow_up'`, a "Give me results with current information" button appears that auto-fills the input with "That's it. Just give me results."

### 7.6 Quick Actions & Suggested Queries

The welcome screen includes:
- 4 quick action buttons (Fever, Cough, Headache, Stomach Pain)
- 3 suggested query buttons for common scenarios
- Trust badges (HIPAA Compliant, End-to-End Encrypted, 24/7 Available)

---

## 8. Tech Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Build Tool | Vite | 7.x |
| Framework | React | 18.x |
| Language | TypeScript | 5.x |
| Styling | Tailwind CSS | 3.4.19 |
| UI Components | shadcn/ui | latest |
| Animation | Framer Motion | 11.x |
| HTTP Client | Axios | latest |
| Auth | JWT (localStorage) | - |
| Icons | Lucide React | latest |

---

## 9. File Structure

```
/mnt/agents/output/app/
├── index.html
├── package.json
├── tailwind.config.js
├── vite.config.ts
├── public/
│   ├── hero-bg.jpg              # Hero background image
│   └── bot-avatar.png           # Bot avatar icon
├── src/
│   ├── main.tsx                 # Entry point (no StrictMode)
│   ├── App.tsx                  # Root shell with tab navigation
│   ├── index.css                # Global styles, dark theme tokens
│   ├── context/
│   │   └── AuthContext.tsx      # JWT auth context provider
│   ├── components/
│   │   ├── AuthModal.tsx        # Login/register modal
│   │   ├── ChatInterface.tsx    # Core chat UI
│   │   ├── Sidebar.tsx          # Left sidebar with chat history
│   │   ├── TriageResult.tsx     # Diagnosis/triage result cards
│   │   ├── PrivacyBadge.tsx     # PII status badge
│   │   ├── RejectedMessage.tsx  # Non-health query rejection
│   │   ├── ResearchOverview.tsx # PubMed research expandable card
│   │   ├── AuditLog.tsx         # SHA-256 governance panel
│   │   └── KaggleEvalPage.tsx   # Static benchmark dashboard
│   ├── hooks/
│   │   ├── useTriage.ts         # Triage chat logic
│   │   └── useSidebar.ts        # Chat list fetching
│   ├── data/
│   │   └── evalData.ts          # 20-case benchmark dataset
│   └── utils/
│       └── api.ts               # Axios instance with auth
```

---

## 10. Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `VITE_TOGETHER_API_KEY` | No (live eval only) | - | Together AI API key for G-Eval |
| `VITE_TOGETHER_MODEL` | No | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | G-Eval judge model |
| `VITE_API_BASE_URL` | No | Dev: `/api`, Prod: AWS Gateway | Backend base URL |

---

## 11. Accessibility & UX Considerations

- **Keyboard Navigation:** Enter to send, Shift+Enter for new line in textarea
- **Scroll Behavior:** Auto-scroll to bottom on new messages
- **Loading States:** Typing animation for AI responses
- **Empty States:** Informative empty states for sidebar, audit log
- **Responsive Design:** Mobile-optimized with collapsible sidebar and overlay
- **Medical Disclaimer:** Visible on every triage result and in the input footer
- **Privacy Indicators:** Real-time PII status badges on messages
- **Error Handling:** Graceful error messages with retry capability

---

## 12. Known Observations

1. **AuditLog is dormant:** The `onNewLog` callback architecture is in place but ChatInterface does not currently invoke it, so the audit panel shows an empty state.
2. **EvalPanel is orphaned:** `EvalPanel.jsx` (interactive live evaluation) is fully implemented but not rendered. The Eval tab shows `KaggleEvalPage` (static results) instead.
3. **No chat delete UI:** `useTriage` exports `deleteChat`, but no component currently calls it.
4. **Login-gated chat:** The chat input is disabled for anonymous users (`disabled={!user}`), so unauthenticated users can only view the AuditLog and Eval page.
5. **Sidebar chat loading:** `handleSelectChat` in App.tsx has the callback wired but the actual `loadChat` from `useTriage` is not connected across the component boundary (noted in comment).

---

## 13. Deployment

- **Target:** Static hosting
- **Deploy Tool:** `mshtools-deploy_website`
- **Output:** `dist/` folder with `index.html`, bundled JS/CSS, optimized assets
- **Live URL:** https://yoflynzmkm674.kimi.page

---

## 14. Screenshots

### Chat View (Anonymous User)
Shows the welcome screen with quick actions, suggested queries, sign-in prompt, and Audit Trail panel on the right.

### Eval Dashboard
Shows the G-Eval benchmark with summary statistics, metric breakdown progress bars, filter controls, and the 20-case results table with expandable detail rows.

---

*Report generated automatically from source code analysis and deployment verification.*

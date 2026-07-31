# AGENTS.md — COLA-ZERO

Guidelines, conventions, and instructions for AI agents working on the COLA-ZERO repository.

---

## 1. Document Purpose & Scope

This document specifies repository standards, coding conventions, documentation rules, and execution workflows for AI agents.

Architectural principles, domain model details, database schemas, and design decisions are specified in [ARCHITECTURE.md](file:///var/home/nmoreira/Projetos/cola-zero/ARCHITECTURE.md). Agents MUST consult [ARCHITECTURE.md](file:///var/home/nmoreira/Projetos/cola-zero/ARCHITECTURE.md) before making database, structural, or API contract changes.

---

## 2. Core Project Principles

1. **Keep It Simple**: Prefer clean, simple implementations over complex abstractions or premature optimizations.
2. **Security First**: Every endpoint and feature must enforce authentication and role-based authorization (RBAC).
3. **Privacy & LGPD by Design**: Minimize data collection. Explicitly inform users of any online monitoring.
4. **Answer Key Centrality**: Maintain the core domain model centered on `Answer Key + Attempt Engine` *(Gabarito + Motor de Tentativas/Avaliação)*. Treat the Question Bank as an optional producer of Answer Keys, not as the core of the assessment model. Refer to [ARCHITECTURE.md](file:///var/home/nmoreira/Projetos/cola-zero/ARCHITECTURE.md) for full domain flows.

---

## 3. Repository Conventions

### 3.1 Directory Structure
- `backend/`: FastAPI application, Alembic migrations, SQLAlchemy models, Pydantic schemas, OpenCV/ReportLab services, pytest suite.
- `frontend/`: Next.js App Router application, React components, TailwindCSS styles, Vitest suite.
- `docs/`: Historical archive (`docs/archive/`) and documentation sitemaps.
- Root `.md` files: Official specifications (`README.md`, `ARCHITECTURE.md`, `STATUS_ATUAL.md`, `ROADMAP.md`, `PLANO_*.md`).

### 3.2 File & Identifier Naming
- Database tables and columns: `snake_case` (e.g., `student_code`, `created_at`).
- Python files and variables: `snake_case`.
- TypeScript / React components: `PascalCase` (e.g., `QuestionCard.tsx`).
- API Endpoints: lowercase with hyphens for multi-word paths (e.g., `/api/v1/omr/scans/upload`).

---

## 4. Coding Conventions

### 4.1 Backend (Python / FastAPI / SQLAlchemy)
- **Service Layer**: Keep business logic inside service classes (`app/services/`), not inside route handlers or database controllers.
- **Schemas**: Always validate request/response payloads with Pydantic schemas (`app/schemas/`).
- **Database Access**: Inject SQLAlchemy sessions into endpoints via FastAPI dependencies.
- **UUID Primary Keys**: Ensure all new models use `UUID v4` as primary key (`id`). Never use auto-incrementing integer IDs.
- **Security & Auth**: Use `@get_current_user` for authentication and `@require_role` for RBAC enforcement. Tokens must be read from secure HttpOnly cookies.

### 4.2 Frontend (Next.js / React / TypeScript)
- **Component Design**: Keep visual components focused and reusable. Avoid putting business logic or raw API fetches directly inside presentation UI components.
- **Type Safety**: Strictly type all props and API responses in TypeScript.
- **Styling**: Use Vanilla CSS / TailwindCSS. Maintain cohesive color tokens and responsive layouts.
- **Security**: Never store JWT tokens in `localStorage` or `sessionStorage`.

---

## 5. Documentation Conventions

1. **Single Source of Truth**: Each topic has exactly ONE authoritative document. Do not duplicate information across markdown files.
   - System Architecture, Data Model, Database Schema & Design Decisions -> [ARCHITECTURE.md](file:///var/home/nmoreira/Projetos/cola-zero/ARCHITECTURE.md)
   - Current Project Status & Implemented Features -> [STATUS_ATUAL.md](file:///var/home/nmoreira/Projetos/cola-zero/STATUS_ATUAL.md)
   - Future Phases & Priorities -> [ROADMAP.md](file:///var/home/nmoreira/Projetos/cola-zero/ROADMAP.md)
   - OMR Printed Exams -> [PLANO_OMR.md](file:///var/home/nmoreira/Projetos/cola-zero/PLANO_OMR.md)
   - Assessment System & Attempts -> [PLANO_AVALIACOES.md](file:///var/home/nmoreira/Projetos/cola-zero/PLANO_AVALIACOES.md)
   - Question Bank (Optional Producer) -> [PLANO_BANCO_QUESTOES.md](file:///var/home/nmoreira/Projetos/cola-zero/PLANO_BANCO_QUESTOES.md)
   - Pedagogical Analytics & Dashboard -> [PLANO_DASHBOARD.md](file:///var/home/nmoreira/Projetos/cola-zero/PLANO_DASHBOARD.md)
   - Online Integrity & LGPD -> [PLANO_ANTI_COLA.md](file:///var/home/nmoreira/Projetos/cola-zero/PLANO_ANTI_COLA.md)
2. **Internal Links**: Always use markdown file links (e.g. `[ARCHITECTURE.md](file:///var/home/nmoreira/Projetos/cola-zero/ARCHITECTURE.md)`) when referencing other documents.
3. **Preserve Valid Data**: When updating documentation, update the relevant single source of truth without erasing valid historical information.

---

## 6. Implementation Workflow for AI Agents

1. **Inspect Before Modifying**: Search and view target code/documentation files before making changes.
2. **Enforce Core Business Rules**:
   - The **Answer Key** is the central domain concept. The Question Bank is an optional producer of Answer Keys.
   - Online exams with question content MUST deliver **one question at a time** (`GET /attempts/{id}/next-question`).
   - Answers MUST be saved immediately upon submission (autosave).
   - OMR is ONLY for printed exams; online exams NEVER use OMR.
   - The pedagogical dashboard MUST function even if no registered questions exist in the Question Bank (operating directly on Answer Key & Skills).
3. **Verify Implementation**: After completing code changes, run automated tests (`pytest` / `vitest`) or lint checks. Never declare victory without empirical verification.

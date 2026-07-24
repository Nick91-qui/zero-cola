# COLA-ZERO — Status Atual (2026-07-24)

## Progresso Geral

**Milestone 1: Fundação & Autenticação**
- Bloco 1 (Fundação Backend): **100% completo**
- Bloco 2 (Autenticação Backend + Frontend): **100% completo**

**Milestone 2: COLA-ZERO OMR (MVP)**
- Backend (models, migration, layouts, PDF, engine, API): **completo**
- Frontend (upload e revisão visual): **pendente**

**Percentual geral**: Milestone 1 concluída; backend OMR da Milestone 2 entregue

---

## Bloco 1 — Fundação do Backend (COMPLETO)

### Entregas
- FastAPI aplicação funcional
- PostgreSQL conectado e validado
- Alembic configurado com migrations
- Health check endpoint
- Docker Compose com Postgres, Backend, Frontend

### Testes
- Testes de fundação passando

### Commits principais
- `b5664f9` - adiciona setup inicial do projeto
- `1a64c55` - fundação de banco e primeira modelagem
- `ccb01e1` - implementações básicas
- `8d7f1e6` - chore: add docker-compose and scripts to run dev containers

---

## Bloco 2 — Identidade e Segurança (COMPLETO)

### Backend Authentication

**Implementação**
- Endpoint POST `/api/v1/auth/register` (201)
- Endpoint POST `/api/v1/auth/login` (200, retorna tokens)
- Endpoint POST `/api/v1/auth/refresh` (200, novo access token)
- Endpoint POST `/api/v1/auth/logout` (200, placeholder)
- Endpoint GET `/api/v1/auth/me` (200, current user)

**Segurança**
- Password hashing com bcrypt
- JWT tokens: access (15min) + refresh (7 dias) via cookies HttpOnly
- Token validation e verification
- RBAC decorator para proteção de endpoints
- get_current_user dependency para validação

**Database**
- Tabela `users` com UUID primary key
- User model com `is_active`, `role`, `student_code` (5 dígitos, opcional), timestamps
- Indexes em email (unique) e student_code (unique)
- UserRole enum (STUDENT, TEACHER, ADMIN)

**Repository Pattern**
- UserRepository com CRUD operations
- UUID-safe get_by_id, get_by_email
- Factory pattern em AuthService

### Frontend Authentication

**React Context + Hooks**
- `app/context/AuthContext.tsx` - centralized state management
- `app/hooks/useAuth.ts` - custom hook
- Token storage: Cookies seguros HttpOnly (gerenciados pelo backend)
- Auto-refresh token logic (via rotas de cookies HttpOnly)
- Error handling centralizado

**Pages**
- `app/auth/login/page.tsx` - login form
- `app/auth/register/page.tsx` - registration form com role selection
- `app/dashboard/page.tsx` - protected dashboard page
- `app/unauthorized/page.tsx` - 403 error page
- `app/page.tsx` - home redirect logic

**Components**
- `ProtectedRoute.tsx` - route guarding component
- `app/layout.tsx` - root layout com AuthProvider

### Stack Decisões

**Password Hashing**: bcrypt (definido via ADR-001; Argon2 recomendado para o futuro)
**Token Storage**: Cookies seguros HttpOnly (Access: SameSite=Lax; Refresh: SameSite=Strict)
**Token Strategy**: JWT via HttpOnly cookies com refresh token rotation
**RBAC**: Decorator pattern com get_current_user dependency
**Frontend State**: React Context integrado a cookies (sem Redux necessário para MVP)

---

## Milestone 2 — OMR Backend (COMPLETO)

### Escopo entregue

Subsistema OMR independente do fluxo de tentativas online, com modos **standalone** (gabarito avulso) e **integrado** (`exam_id` opcional).

**Identificação do aluno:** grid OMR de 5 dígitos (`student_code`), sem QR Code.
**Entrada:** upload de imagem única (JPG/JPEG/PNG). PDF multipágina adiado.
**Layouts:** coordenadas em código (`app/core/omr_layouts.py`), referenciadas por `layout_version`.

### Entregas backend

- Tabelas `omr_templates`, `omr_scans` e entidade unificada `grades`
- Migration Alembic `8c7e7c2e4e00_create_omr_and_grades_tables`
- Campo `users.student_code` + `users.is_active` alinhados ao schema
- Layouts versionados e gerador de PDF (ReportLab) com matrícula pré-preenchida
- Engine OpenCV (alinhamento por âncoras, bolhas e student code)
- API REST com RBAC (teacher/admin):
  - `POST /api/v1/omr/templates`
  - `GET /api/v1/omr/templates/{id}/pdf`
  - `POST /api/v1/omr/scans/upload`
  - `GET /api/v1/omr/scans/{id}`
  - `PATCH /api/v1/omr/scans/{id}`
  - `POST /api/v1/omr/scans/{id}/confirm` → grava `Grade`
- Mount estático `/uploads` para imagens de scan
- Testes: `test_omr_models`, `test_omr_layouts`, `test_omr_pdf`, `test_omr_engine`, `test_omr_service`, `test_omr_api`

### Pendente (frontend OMR)

- Interface Next.js de upload de gabaritos
- Tela de revisão visual com overlays para o professor
- Confirmação de nota a partir da UI

Planejamento detalhado: [PLANO_OMR.md](./PLANO_OMR.md)

---

## Estrutura de Diretórios (resumo)

```
cola-zero/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── omr_layouts.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── omr.py
│   │   │   ├── grade.py
│   │   │   └── enums.py
│   │   ├── schemas/
│   │   │   ├── user.py
│   │   │   └── omr.py
│   │   ├── repositories/
│   │   │   ├── user.py
│   │   │   ├── omr.py
│   │   │   └── grade.py
│   │   ├── services/
│   │   │   ├── auth.py
│   │   │   ├── omr.py
│   │   │   ├── omr_engine.py
│   │   │   └── omr_pdf.py
│   │   ├── api/routes/
│   │   │   ├── auth.py
│   │   │   └── omr.py
│   │   └── main.py
│   ├── alembic/versions/
│   ├── tests/test_auth.py, test_omr_*.py
│   ├── uploads/scans/   # runtime; ignorado no git
│   └── pyproject.toml
├── frontend/            # auth completo; UI OMR pendente
├── PLANO_OMR.md
└── STATUS_ATUAL.md
```

---

## Tecnologias Utilizadas

### Backend
- FastAPI, SQLAlchemy 2, PostgreSQL 16, Alembic
- Auth: PyJWT, bcrypt
- OMR: OpenCV (headless), NumPy, ReportLab, python-multipart

### Frontend
- Next.js, React, TypeScript, TailwindCSS

### Infrastructure
- Podman / Docker Compose, Makefile

---

## Métricas (aprox.)

| Métrica | Valor |
|---------|-------|
| Endpoints auth | 5 |
| Endpoints OMR | 6 |
| Testes OMR | 6 arquivos (`test_omr_*`) |
| Frontend OMR | 0% (pendente) |

---

## Como Iniciar Localmente

### Backend
```bash
cd backend
pip install -e ".[dev]"

DATABASE_URL="postgresql://colazero:colazero@localhost:5432/colazero" \
  python -m alembic upgrade head

uvicorn app.main:app --reload
pytest tests/ -v
```

### Frontend
```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
npm run dev
```

### Compose
```bash
make up
podman compose ps
make down
```

---

## Próximos Passos

1. **Frontend OMR** — upload, revisão visual e confirmação de nota (ISSUE-059)
2. **Validação E2E** — template → PDF → upload → confirm → `grades`
3. **Milestone 3** — Question Bank, Exams e Attempts online (core acadêmico)
4. **Auditoria de login** — logs de sucesso/falha antes de produção

---

## Notas

- OMR é prioridade de produto e permanece desacoplado do Exam Engine online
- Scans em `backend/uploads/scans/` são artefatos de runtime (não versionados)
- `Grade` unifica notas ONLINE e OMR via `source_type` + `source_id`

---

**Última atualização**: 2026-07-24  
**Autor**: NCM  
**Status**: M1 completa; M2 backend OMR completo; frontend OMR e core online pendentes

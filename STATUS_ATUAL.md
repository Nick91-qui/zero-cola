# COLA-ZERO — Status Atual (2026-07-24)

## Progresso Geral

**Milestone 1: Fundação & Autenticação**
- Bloco 1 (Fundação Backend): **100% completo**
- Bloco 2 (Autenticação Backend + Frontend): **100% completo**

**Milestone 2: COLA-ZERO OMR (MVP)**
- Backend (models, migration, layouts, PDF, engine, API): **completo**
- Frontend (criar gabarito, PDF/preview, upload e revisão): **completo**
- `student_code` no cadastro/perfil: **completo**
- Calibração layout↔detecção (PNG sintético): **completo**
- Calibração com foto real impressa: **pendente (campo)**

**Percentual geral**: Milestone 1 concluída; Milestone 2 OMR utilizável em modo avulso

---

## Bloco 1 — Fundação do Backend (COMPLETO)

### Entregas
- FastAPI aplicação funcional
- PostgreSQL conectado e validado
- Alembic configurado com migrations
- Health check endpoint
- Docker Compose com Postgres, Backend, Frontend

---

## Bloco 2 — Identidade e Segurança (COMPLETO)

**Auth**
- Register / login / refresh / logout / me / patch me
- JWT via Bearer + cookies HttpOnly no cliente
- bcrypt + RBAC
- `student_code` (5 dígitos) obrigatório para alunos no registro; editável via `PATCH /auth/me`

**Frontend auth**
- Login/register, AuthContext, ProtectedRoute, dashboard

---

## Milestone 2 — OMR (COMPLETO para modo avulso)

### Backend
- Tabelas `omr_templates`, `omr_scans`, `grades` + migration `8c7e7c2e4e00`
- Layouts `v1_std_20q` / `v1_std_50q`
- PDF (ReportLab) + preview PNG (mesmo espaço do motor)
- Engine OpenCV + score + confirm → `grades`
- Endpoints:
  - `POST/GET /omr/templates`, `GET /omr/templates/{id}`
  - `GET .../pdf`, `GET .../preview.png`
  - `POST /omr/scans/upload`, `GET/PATCH /omr/scans/{id}`, `POST .../confirm`

### Frontend (`/omr`)
- Lista e criação de gabarito (chave A–E)
- Detalhe: baixar PDF / preview PNG, upload JPG/PNG
- Revisão: editar código/respostas, confirmar nota
- Link no dashboard para teacher/admin

### Como usar agora
1. Subir stack (`make up`) e rodar `make migrate`
2. Registrar **teacher** e **student** (student com código 5 dígitos)
3. Login teacher → Dashboard → **Abrir módulo OMR**
4. Criar gabarito → baixar PDF → preencher/fotografar → upload → revisar → confirmar

Para testar sem impressora: baixe o **preview PNG**, marque bolhas no editor de imagem, e faça upload.

---

## Próximos Passos

1. Validar com folhas **impressas** e fotos reais (ajuste fino de âncoras se necessário)
2. Listagem de scans por template na UI
3. Milestone 3 — Question Bank / Exams / Attempts (modo OMR integrado a Exam)

---

**Última atualização**: 2026-07-24  
**Status**: OMR avulso ponta a ponta disponível (API + UI)

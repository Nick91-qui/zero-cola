# COLA-ZERO — Status Atual do Projeto

> **Single Source of Truth** para o status real do desenvolvimento, funcionalidades já implementadas, limitações conhecidas e débitos técnicos.

---

## 1. Resumo Executivo do Status

- **Status Geral**: Backend MVP Milestones 1 (Auth), 2 (OMR Standalone), 3 (Assessment Core), 4 (Online Attempt Engine) e 5 (Classes, Monitoring, Audit & LGPD) implementados e validados. Frontend funcional para Auth e OMR.
- **Suíte de Testes Automatizados**: **111 testes de backend passando sem erros** na validação mais recente.
- **Infraestrutura**: Totalmente containerizada com Docker e Docker Compose (`postgres`, `backend`, `frontend`).

---

## 2. Funcionalidades Implemented & Validadas (Completed Milestones)

### 2.1 Milestone 1 — Autenticação e Gestão de Identidade (RBAC) ✅
- **Cadastro e Login**: Suporte a perfis `STUDENT`, `TEACHER` e `ADMIN`.
- **Código do Estudante (`student_code`)**: Campo numérico de 5 dígitos obrigatório para perfis de alunos (criado no registro e editável via `PATCH /api/v1/auth/me`).
- **Segurança de Tokens**: JWT Access Token (15 min) e Refresh Token (7 dias) gerenciados via cookies HttpOnly (`SameSite=Lax/Strict`).
- **Hashing de Senha**: Criptografia segura com `bcrypt`.
- **Endpoints de Autenticação**:
  - `POST /api/v1/auth/register`
  - `POST /api/v1/auth/login`
  - `POST /api/v1/auth/refresh`
  - `POST /api/v1/auth/logout`
  - `GET /api/v1/auth/me`
  - `PATCH /api/v1/auth/me`

### 2.2 Milestone 2 — Módulo OMR Standalone e Integrado ✅
- **Layouts OMR em Código**: Layouts versionados `v1_std_20q` (20 questões) e `v1_std_50q` (50 questões) mantidos estaticamente em `app/core/omr_layouts.py`.
- **Geração de PDF com ReportLab**: Geração dinâmica de cartões-resposta em PDF com âncoras nos cantos e `student_code` de 5 dígitos preenchido/sombreado. Preview em PNG disponível.
- **Motor de Visão Computacional OpenCV**:
  - Alinhamento perspectivo de imagem (deskew & warp).
  - Leitura do grid numérico de 5 dígitos do aluno.
  - Leitura de densidade de bolhas de resposta (alternativas A–E).
- **Processamento e Correção Automática**: Upload de imagem única (JPG/PNG), cálculo automático de pontuação e interface visual de revisão com overlay colorido (verde/vermelho).
- **Confirmação de Nota**: Confirmação da correção pelo professor salvando o registro final na tabela unificada `grades`.

### 2.3 Milestone 3 — Core Domain & Relatórios ✅
- **Domínio Acadêmico no Backend**:
  - Modelos e migrations para `questions`, `skills`, `question_skills`, `classes`, `class_students`, `exams`, `exam_questions`, `attempts`, `attempt_answers`, `omr_templates`, `omr_scans`, `grades`.
  - Suporte a Habilidades SEDU/BNCC.
  - CRUD de exames, questões e habilidades.
- **Integração OMR ↔ Exam**:
  - Confirmação de folha OMR integrada gera automaticamente registros em `exams`, `attempts` e `attempt_answers`.
- **Relatórios & Exportação**:
  - Estatísticas por questão e desempenho no backend (`GET /api/v1/exams/{id}/statistics`).
  - Exportação de relatórios em PDF (`GET /api/v1/exams/{id}/export/pdf`) e planilhas Excel XLSX (`GET /api/v1/exams/{id}/export/xlsx`).

### 2.4 Milestone 4 — Online Attempt Engine ✅
- **Fluxo Online de Tentativas**: suporte ao ciclo `not_started -> in_progress -> submitted -> graded`.
- **Entrega Sequencial**: a API entrega uma questão por vez para o estudante.
- **Persistência e Autosave**: respostas são salvas incrementalmente durante a tentativa.
- **Correção Unificada**: a correção online usa `AnswerKeyItem.correct_answer` como fonte autoritativa, com notas unificadas em `grades` via `source_type = ONLINE`.
- **Compatibilidade de Modelos**: os fluxos de Workflow A e Workflow B continuam funcionando no mesmo modelo unificado de `Exam`, `AnswerKey`, `Attempt` e `AttemptAnswer`.

### 2.5 Milestone 5 — Classes, Monitoring, Audit & LGPD ✅
- **Classes e Matrículas**: modelos e rotas para `classes` e `class_students`, com ownership por professor, acesso administrativo e listagem de vínculos do estudante.
- **RBAC e Isolamento**: professores só acessam suas próprias turmas; admins têm acesso ampliado; estudantes acessam apenas turmas autorizadas.
- **Auditoria Imutável**: trilha de auditoria em `audit_logs` para ações sensíveis de autenticação, classes, consentimentos, privacidade e monitoramento.
- **Eventos de Segurança**: `security_events` registra eventos observáveis de monitoramento em tentativas online.
- **Consentimentos**: modelo dedicado `consents` com registro, revogação e auditoria; o consentimento de monitoramento é pré-requisito para eventos de segurança.
- **Privacidade e LGPD**: endpoint público de política de privacidade, exportação estruturada de dados do usuário e anonimização suave com preservação de integridade histórica.
- **Validação de Banco de Dados**: migração Alembic `f7a8b9c0d1e2` aplicada com sucesso em PostgreSQL de desenvolvimento, a partir de `e6f7a8b9c0d1`.

---

## 3. Limitações Conhecidas

1. **Upload OMR Individual**: O endpoint OMR aceita apenas uma imagem por requisição (JPG/PNG). Não há suporte para uploads de PDFs multipágina contendo várias folhas digitalizadas em lote.
2. **Layouts OMR Fixos**: Somente os layouts `v1_std_20q` e `v1_std_50q` estão registrados no código. Novos formatos exigem inclusão manual no registry de layouts em código.
3. **Calibração de Iluminação OMR**: Fotos com sombras extremamente fortes ou iluminação muito desfavorável podem exigir revisão manual pelo professor na interface de conferência.
4. **Interface Frontend para Provas Online**: As rotas de backend do Assessment Engine estão 100% implementadas e testadas, porém a interface visual Next.js para alunos realizarem a prova online sequencial ainda não foi construída.
5. **Interfaces Frontend de Step 9**: A gestão visual de classes, auditoria, consentimentos, eventos de segurança e LGPD ainda não foi implementada no frontend.

---

## 4. Débitos Técnicos (Technical Debt)

1. **Migração de Hashing de Senha**: O sistema utiliza `bcrypt` (ADR-001 / Design Decision DECISION-001). A migração para `Argon2` permanece como um item de hardening técnico pré-produção.
2. **Persistência Temporária de Uploads OMR**: Imagens enviadas para o OMR são armazenadas no sistema de arquivos local (`uploads/`). Para ambientes de produção com múltiplas instâncias, será necessário abstrair o armazenamento para um serviço de storage S3/Object Storage.

---

## 5. Histórico de Verificação de Qualidade

- **Backend Pytest**: 111 testes passando sem erros.
  - Step 8 online attempt API: 2 testes passando.
  - Step 8 attempt service: 6 testes passando.
  - OMR API: 4 testes passando.
  - Step 9 targeted tests: 10 testes passando.
  - Suite completa do backend: 111 passed, 0 failed, 0 skipped.
- **Execução dos Testes**:
  - Os testes foram executados dentro do container `cola_zero_backend`.
  - O PostgreSQL estava acessível durante a execução.
  - `alembic current` reportou `e6f7a8b9c0d1` antes da migração e `f7a8b9c0d1e2 (head)` após a migração.
  - `alembic_version` no PostgreSQL: `f7a8b9c0d1e2`.
  - Health endpoint da API: `{"status":"ok"}`.
  - A falha de timeout observada anteriormente na execução via virtualenv do host foi ambiental; a execução dentro do container backend completou com sucesso.
- **Frontend Vitest**: Testes de componentes de autenticação e formulários 100% verde.

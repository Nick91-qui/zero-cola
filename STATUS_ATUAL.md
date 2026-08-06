# COLA-ZERO — Status Atual do Projeto

> **Single Source of Truth** para o status real do desenvolvimento, funcionalidades já implementadas, limitações conhecidas e débitos técnicos.

---

## 1. Resumo Executivo do Status

- **Status Geral**: os módulos backend centrais do COLA-ZERO estão implementados e validados, incluindo autenticação/RBAC, OMR, AnswerKey/Attempt Engine, Question Bank, Workflow A, Workflow B, classes, auditoria, consentimentos e LGPD básica. A Fase 8 de produção e visualização de provas está em implementação.
- **Frontend**: já existem as telas principais para autenticação, painel, avaliações, tentativas online e OMR; a camada visual de administração para classes, auditoria e LGPD é mais enxuta e ainda pode evoluir.
- **Suíte de Testes Automatizados**: a validação consolidada mais recente registrou **111 testes de backend aprovados** e **8 testes Vitest de frontend aprovados**.
- **Infraestrutura**: o ambiente continua containerizado com Docker e Docker Compose (`postgres`, `backend`, `frontend`).

---

## 2. Funcionalidades Implementadas e Validadas

### 2.1 Milestone 1 — Autenticação e Gestão de Identidade (RBAC) ✅
- Cadastro e login com perfis `STUDENT`, `TEACHER` e `ADMIN`.
- `student_code` numérico de 5 dígitos para estudantes.
- JWT Access Token e Refresh Token em cookies HttpOnly.
- Hashing seguro de senha com `bcrypt`.
- Endpoints de autenticação, sessão e atualização de perfil.

### 2.2 Milestone 2 — Módulo OMR Standalone e Integrado ✅
- Layouts OMR versionados em código.
- Geração dinâmica de PDF e preview visual.
- Leitura de bolhas com OpenCV.
- Upload e correção automática de uma imagem por requisição.
- Confirmação da correção com gravação na tabela unificada `grades`.

### 2.3 Milestone 3 — Core Domain, Question Bank e Relatórios ✅
- Question Bank reutilizável com `questions`, `skills` e `question_skills`.
- Exames, tentativas, respostas e estatísticas pedagógicas.
- Workflow A e Workflow B já coexistem no backend.
- Exportações em PDF e XLSX disponíveis para exames.

### 2.4 Milestone 4 — Online Attempt Engine ✅
- Fluxo `not_started -> in_progress -> submitted -> graded`.
- Entrega sequencial de uma questão por vez.
- Autosave incremental das respostas.
- Correção online baseada em `AnswerKeyItem.correct_answer`.
- Geração de `Grade` com `source_type = ONLINE`.

### 2.5 Milestone 5 — Classes, Monitoring, Audit & LGPD ✅
- `classes`, `teacher_classes`, `class_students` e `exam_classes` implementados.
- Isolamento por vínculo explícito entre professor, turma e exame.
- `audit_logs`, `security_events` e `consents` disponíveis no backend.
- Política de privacidade, exportação de dados e anonimização suave implementadas.

### 2.6 Frontend Atual ✅
- `/auth/login` e `/auth/register`
- `/dashboard`
- `/exams`, `/exams/new`, `/exams/[examId]`
- `/attempts/start`, `/attempts/[attemptId]`
- `/omr`, `/omr/new`, `/omr/[templateId]`, `/omr/scans/[scanId]`

---

## 3. Limitações Conhecidas

1. **Upload OMR Individual**: o endpoint OMR segue aceitando uma imagem por vez.
2. **Layouts OMR Fixos**: os layouts continuam registrados no código e novos formatos ainda exigem atualização manual.
3. **Calibração de Iluminação OMR**: imagens muito degradadas podem exigir revisão manual.
4. **Frontend Administrativo de Step 9**: a camada visual para classes, auditoria, consentimentos, eventos de segurança e LGPD ainda pode ser expandida.
5. **Anti-Cheating Analítico**: a base de eventos existe, mas a análise pedagógica de suspeitas continua como funcionalidade futura.
6. **Produção OMR Personalizada**: a geração de folhas por aluno e por turma está em implementação e ainda precisa de validação final de fluxo e UX.

---

## 4. Débitos Técnicos

1. **Migração de Hashing de Senha**: permanece a troca para `Argon2` como hardening pré-produção. A decisão atual é manter `bcrypt` no MVP e tratar a migração para `Argon2` como débito técnico para depois da estabilização funcional.
2. **Persistência de Uploads OMR**: os arquivos ainda estão no filesystem local; para escala horizontal, o storage precisa de abstração. O caminho recomendado é introduzir um adaptador de storage compatível com MinIO/object storage, mantendo o filesystem local como backend de desenvolvimento enquanto o MVP amadurece.

## 5. Próximo Passo Planejado

1. **Produção e Visualização de Provas**: o próximo incremento funcional planejado e atualmente em implementação é separar a montagem da prova da criação de questões, permitir a consulta visual do Banco de Questões e gerar folhas OMR personalizadas por aluno. O plano detalhado está em [PLANO_PRODUCAO_PROVAS.md](file:///var/home/nmoreira/Projetos/cola-zero/PLANO_PRODUCAO_PROVAS.md).

---

## 6. Histórico de Verificação de Qualidade

- **Backend Pytest**: 111 testes aprovados.
  - Step 8 online attempt API: 2 testes aprovados.
  - Step 8 attempt service: 6 testes aprovados.
  - OMR API: 4 testes aprovados.
  - Step 9 targeted tests: 10 testes aprovados.
  - Suite completa do backend: `111 passed, 0 failed, 0 skipped`.
- **Execução dos Testes**:
  - Os testes foram executados dentro do container backend.
  - O PostgreSQL de desenvolvimento esteve acessível durante a execução.
  - A migração Alembic foi validada no banco de desenvolvimento antes de registrar o status.
  - Health endpoint da API: `{"status":"ok"}`.
- **Frontend Vitest**: 8 testes aprovados, cobrindo autenticação, tentativas online, OMR e avaliação.

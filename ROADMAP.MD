# COLA-ZERO — Roadmap de Implementação

Este documento define a ordem de desenvolvimento do COLA-ZERO com foco em MVP, segurança por padrão, privacidade e arquitetura centrada em Question Bank + Attempt Engine.

---

# Fase 0 — Fundação do projeto

## Objetivo
Estruturar a base técnica do sistema.

## Entregas
- estrutura inicial de backend e frontend
- configuração de Docker e Docker Compose
- configuração de PostgreSQL
- definição de `.env.example`
- logging básico
- setup inicial de testes

---

# Fase 1 — Autenticação e RBAC (Backend)

## Objetivo
Criar a base de identidade e segurança do backend antes do desenvolvimento de features do domínio.

## Entregas
- modelo `User` com UUID
- hash de senha com Argon2 preferencialmente
- geração de JWT com a estratégia de sessão aprovada:
  - Access Token: expiração curta (15–30 minutos)
  - Refresh Token: expiração longa (7–30 dias)
- suporte a controle de acesso baseado em regras (RBAC) com perfis `student`, `teacher` e `admin`
- endpoints `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`

---

# Fase 2 — Modelagem Completa de Domínio e Migrações (Backend)

## Objetivo
Modelar, criar e estabilizar o schema do banco de dados relacional e migrações antes de construir interfaces.

## Entregas
- criação de tabelas e modelos SQLAlchemy com UUID:
  - `users`
  - `classes`
  - `class_students`
  - `questions`
  - `exams`
  - `exam_questions`
  - `attempts`
  - `answers`
  - `security_events` (substituindo o termo anterior `monitoring_events`)
  - `audit_logs`
- aplicação de migrações com Alembic
- definição do modelo de Tentativas aprovado:
  - `exams`: `max_attempts` (INTEGER, default=1), `time_limit`, `randomize`, `status`
  - `attempts`: `attempt_number` (INTEGER), `status`, `score`

---

# Fase 3 — Login e Gerenciamento de Sessão no Frontend

## Objetivo
Criar a interface de autenticação do usuário utilizando a política de cookies HttpOnly estabelecida.

## Entregas
- tela de login no Next.js
- persistência de sessão e tratamento de tokens:
  - Cookies seguros HttpOnly gerenciados pelo backend
  - Access Token: HttpOnly, Secure, SameSite=Lax
  - Refresh Token: HttpOnly, Secure, SameSite=Strict
  - **Nota:** Proibido armazenar JWTs em `localStorage` ou `sessionStorage`
- middleware de proteção de rotas no Next.js com base no perfil do usuário

---

# Fase 4 — Banco de Questões (Question Bank)

## Objetivo
Construir o núcleo de conteúdo do domínio de forma reutilizável.

## Entregas
- Question Bank como repositório central de conteúdo
- CRUD de questões pelo professor no backend (`POST /questions`, `GET /questions`, `PATCH /questions/{id}`)
- filtros de questões por disciplina, dificuldade e tags
- interface no frontend para o professor gerenciar e buscar questões no banco

---

# Fase 5 — Exam Engine (Motor de Provas)

## Objetivo
Permitir que professores componham provas (Exams) como configurações de entrega compostas por questões reutilizáveis.

## Entregas
- CRUD de provas no backend e frontend
- relação de composição `ExamQuestion` (vínculo de questões com ordem e peso)
- regras de publicação de prova:
  - Possui título
  - Contém pelo menos 1 questão associada
  - Todas as questões existem no banco de dados
  - Todos os pesos de questões são maiores que 0
  - Soma total dos pesos é exatamente 100
  - Turma (`class_id`) está atribuída
  - Limite de tempo válido configurado
  - Usuário requisitante é o professor dono ou administrador

---

# Fase 6 — Attempt Engine (Motor de Tentativas)

## Objetivo
Implementar o fluxo operacional de realização de provas pelos alunos.

## Entregas
- ciclo de vida de tentativas e respostas (`Attempt -> Answer`)
- entrega obrigatória de uma questão por vez (`GET /attempts/{id}/next-question`)
- autosave de respostas (`POST /attempts/{id}/answers`) e cálculo de nota automática/manual
- aplicação das regras de tentativa:
  - Apenas uma tentativa ativa (`in_progress`) por aluno por prova.
  - Tentativas ativas existentes devem ser resumidas em vez de criar uma nova.
  - Nova tentativa só pode ser criada se `max_attempts` da prova não foi excedido.
  - Tentativas enviadas (`submitted`) não podem ser modificadas.
  - Tentativas corrigidas (`graded`) são imutáveis.
- tela de realização de prova no frontend consumindo de forma sequencial

---

# Fase 7 — Eventos de Segurança (Security Events) e Auditoria

## Objetivo
Registrar eventos de tela do navegador relacionados à integridade do exame e ações sensíveis de usuários.

## Entregas
- captura de eventos no frontend (`visibilitychange`, `blur`, `focus`, `fullscreen_enter`, `fullscreen_exit`)
- ingestão e persistência de eventos no backend na tabela `security_events`
- relatórios de segurança e integridade para professores
- logs de auditoria imutáveis no backend para ações administrativas e pedagógicas
- **Aviso de Segurança (Remind):** O COLA-ZERO não é um lockdown browser. É expressamente proibido alegar ou prometer detecção de uso de ChatGPT, detecção de dispositivos externos, prevenção de capturas de tela ou bloqueio de toda e qualquer fraude. O sistema apenas registra e relata eventos observáveis do navegador.

---

# Fase 8 — Recursos de LGPD

## Objetivo
Implementar governança de dados, consentimento explícito e direitos de privacidade dos usuários.

## Entregas
- aviso claro e consentimento de monitoramento antes do início da prova
- implementação e exposição dos seguintes endpoints operacionais de LGPD:
  - `GET /me/data-export` (exportação de dados do titular)
  - `POST /me/request-anonymization` (pedido de anonimização)
  - `GET /privacy-policy` (política de privacidade do sistema)
  - `POST /consents/monitoring` (registro do consentimento de eventos de segurança)

---

# Fase 9 — Qualidade, Hardening e Testes

## Objetivo
Reforçar a robustez da aplicação antes da entrega final do MVP.

## Entregas
- testes automatizados de autenticação, autorização, entrega de questão, submissão de respostas, correção e ingestão de `security_events`
- rate limiting de endpoints
- validações de segurança e sanitização de dados de entrada

---

# Critério de conclusão do MVP

O MVP é considerado concluído quando:
- usuários autenticam com segurança usando cookies HttpOnly
- professores gerenciam o Question Bank
- professores criam e publicam provas válidas
- alunos realizam tentativas sequenciais respeitando a regra de uma questão por vez
- respostas são salvas imediatamente e avaliadas
- eventos do navegador são salvos em `security_events`
- relatórios básicos e logs de auditoria são gerados
- requisitos essenciais e endpoints operacionais de LGPD estão disponíveis

---

# Fora do escopo imediato

- geração assistida por IA de questões
- análise estatística de itens
- calibração de dificuldade
- learning analytics
- multi-tenancy institucional avançado
- integração com Safe Exam Browser
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

# Fase 1 — Autenticação e controle de acesso

## Objetivo

Criar a base de identidade e segurança do sistema.

## Backend

- modelo `User` com UUID
- autenticação com JWT access token e refresh token
- hash de senha com Argon2 preferencialmente
- RBAC com perfis `student`, `teacher` e `admin`
- auditoria de login e eventos sensíveis iniciais

## Frontend

- página de login
- persistência de sessão
- proteção de rotas por perfil

---

# Fase 2 — Banco de questões

## Objetivo

Construir o núcleo reutilizável do domínio.

## Backend

- modelo `Question`
- CRUD de questões
- filtros por disciplina, dificuldade e tags
- vínculo entre questão e professor criador

## Frontend

- interface de criação e edição de questões
- listagem e busca no banco de questões

---

# Fase 3 — Provas

## Objetivo

Permitir a composição de provas a partir de questões reutilizáveis.

## Backend

- modelo `Exam`
- modelo `ExamQuestion`
- criação e edição de provas
- publicação de provas

## Frontend

- interface de criação de prova
- seleção de questões do banco
- visualização de provas por professor

---

# Fase 4 — Attempt Engine

## Objetivo

Implementar o motor principal de execução da prova.

## Backend

- modelo `Attempt`
- lifecycle de tentativa
- endpoint de próxima questão
- entrega de uma questão por vez
- persistência imediata de resposta
- temporizador da tentativa

## Frontend

- tela de tentativa
- renderização da questão atual
- envio imediato de resposta
- solicitação sequencial da próxima questão

## Regra crítica

O frontend não deve receber todas as questões da prova em uma única resposta.

---

# Fase 5 — Respostas e correção

## Objetivo

Persistir respostas e consolidar avaliação.

## Backend

- modelo `Answer`
- correção automática para questões objetivas
- base para correção manual quando aplicável
- cálculo de score
- finalização da tentativa

## Frontend

- feedback de envio de resposta
- visualização de resultado liberado
- painel básico de correção para professor

---

# Fase 6 — Monitoramento e auditoria

## Objetivo

Registrar eventos relacionados à integridade da tentativa e ações sensíveis do sistema.

## Backend

- modelo `MonitoringEvent`
- modelo `AuditLog`
- endpoint de ingestão de eventos
- relatório básico para professor

## Frontend

- captura de `visibilitychange`
- captura de `blur` e `focus`
- captura de `fullscreen enter` e `fullscreen exit`
- aviso de monitoramento ao usuário

## Observação

Esta fase não deve incluir promessas de detecção de IA, outro dispositivo ou bloqueio total de fraude.

---

# Fase 7 — LGPD e governança de dados

## Objetivo

Atender requisitos essenciais de transparência, minimização e direitos do titular.

## Backend

- exportação de dados do usuário
- anonimização quando legalmente permitida
- política de retenção para logs e registros acadêmicos

## Frontend

- aviso claro de monitoramento
- interface para solicitação de exportação de dados, se aplicável no MVP

---

# Fase 8 — Qualidade e hardening

## Objetivo

Estabilizar o MVP e reforçar qualidade operacional.

## Entregas

- testes automatizados para autenticação
- testes de autorização
- testes de entrega de questão
- testes de submissão de resposta
- testes de correção
- testes de monitoramento
- rate limiting
- observabilidade básica

---

# Critério de conclusão do MVP

O MVP pode ser considerado pronto quando:

- usuários autenticam com segurança
- professores criam questões
- professores criam e publicam provas
- alunos realizam tentativas
- respostas são persistidas e corrigidas
- eventos de monitoramento são registrados
- relatórios básicos existem
- requisitos essenciais de LGPD são atendidos

---

# Fora do escopo imediato

Itens futuros que não devem impactar a arquitetura mínima do MVP:

- geração assistida por IA de questões
- análise estatística de itens
- calibração de dificuldade
- learning analytics
- multi-tenancy institucional avançado
- integração com Safe Exam Browser
# COLA-ZERO — Issues Iniciais de Execução

## 1. Objetivo

Este documento converte o backlog técnico inicial em issues prontas para execução, com estrutura adequada para uso em GitHub Issues, Jira ou Linear.

Convenções:

- prioridade: `P0`, `P1`, `P2`, `P3`
- tipo: `backend`, `frontend`, `infra`, `security`, `qa`, `product-tech`
- status inicial: `todo`

## 2. Issues da milestone 1

### ISSUE-001 — Estruturar backend FastAPI
- ID técnico: `CZ-A01`
- Prioridade: `P0`
- Tipo: `backend`
- Status: `todo`
- Dependências: nenhuma
- Descrição:
  - criar a base do backend com FastAPI e organizar a estrutura inicial do projeto
- Escopo:
  - criar `backend/app`
  - criar `main.py`
  - criar módulos `core`, `db`, `models`, `schemas`, `api`, `services`, `utils`
  - adicionar rota simples de healthcheck
- Critérios de aceite:
  - backend sobe localmente
  - rota de healthcheck responde com sucesso
  - estrutura inicial está consistente com os documentos do projeto
- Checklist:
  - [ ] criar estrutura de diretórios
  - [ ] configurar app FastAPI
  - [ ] criar endpoint de healthcheck

### ISSUE-002 — Configurar SQLAlchemy e conexão com PostgreSQL
- ID técnico: `CZ-B01`
- Prioridade: `P0`
- Tipo: `backend`
- Status: `todo`
- Dependências: `ISSUE-001`
- Descrição:
  - configurar persistência base do backend com SQLAlchemy e sessão de banco
- Escopo:
  - configurar engine
  - configurar session factory
  - criar base declarativa
- Critérios de aceite:
  - backend conecta no PostgreSQL
  - sessão pode ser injetada nas rotas e serviços
- Checklist:
  - [ ] configurar conexão
  - [ ] configurar sessão
  - [ ] criar base dos modelos

### ISSUE-003 — Configurar Alembic e primeira migration
- ID técnico: `CZ-B02`
- Prioridade: `P0`
- Tipo: `backend`
- Status: `todo`
- Dependências: `ISSUE-002`
- Descrição:
  - configurar migrações do banco para suportar evolução do schema
- Escopo:
  - configurar Alembic
  - criar primeira migration funcional
- Critérios de aceite:
  - migrations sobem e descem corretamente
- Checklist:
  - [ ] inicializar Alembic
  - [ ] integrar com SQLAlchemy
  - [ ] validar upgrade e downgrade

### ISSUE-004 — Implementar modelo de usuário
- ID técnico: `CZ-B03`
- Prioridade: `P0`
- Tipo: `backend`
- Status: `todo`
- Dependências: `ISSUE-003`
- Descrição:
  - criar a tabela e o modelo de usuários com UUID e papéis do sistema
- Escopo:
  - model `users`
  - email único
  - timestamps
  - papel `student`, `teacher`, `admin`
- Critérios de aceite:
  - tabela criada com schema esperado
  - UUID é usado como chave primária
- Checklist:
  - [ ] criar model
  - [ ] criar migration
  - [ ] validar constraints

### ISSUE-005 — Implementar hash de senha seguro
- ID técnico: `CZ-C01`
- Prioridade: `P0`
- Tipo: `security`
- Status: `todo`
- Dependências: `ISSUE-004`
- Descrição:
  - implementar utilitário de hash de senha seguro para autenticação
- Escopo:
  - Argon2 preferencialmente
  - fallback seguro, se necessário
  - verificação de hash
- Critérios de aceite:
  - senha nunca é armazenada em texto puro
  - hash e verificação funcionam corretamente
- Checklist:
  - [ ] criar utilitário de hash
  - [ ] criar utilitário de verificação
  - [ ] validar com testes unitários

### ISSUE-006 — Implementar autenticação JWT
- ID técnico: `CZ-C02`
- Prioridade: `P0`
- Tipo: `security`
- Status: `todo`
- Dependências: `ISSUE-005`
- Descrição:
  - implementar emissão e validação de access token e refresh token
- Escopo:
  - gerar access token
  - gerar refresh token
  - validar assinatura e expiração
- Critérios de aceite:
  - login pode retornar tokens válidos
  - refresh token gera novo access token
- Checklist:
  - [ ] implementar geração de tokens
  - [ ] implementar validação
  - [ ] definir expiração configurável

### ISSUE-007 — Implementar rotas de autenticação
- ID técnico: `CZ-C03`
- Prioridade: `P0`
- Tipo: `backend`
- Status: `todo`
- Dependências: `ISSUE-006`
- Descrição:
  - expor autenticação via API
- Escopo:
  - `POST /auth/login`
  - `POST /auth/refresh`
  - `POST /auth/logout`
- Critérios de aceite:
  - login autentica usuário
  - refresh funciona com token válido
  - logout invalida o fluxo definido
- Checklist:
  - [ ] criar schemas
  - [ ] criar rotas
  - [ ] integrar serviço de autenticação

### ISSUE-008 — Implementar RBAC
- ID técnico: `CZ-C04`
- Prioridade: `P0`
- Tipo: `security`
- Status: `todo`
- Dependências: `ISSUE-007`
- Descrição:
  - implementar autorização baseada em papéis
- Escopo:
  - perfis `student`, `teacher`, `admin`
  - dependências reutilizáveis para autorização
- Critérios de aceite:
  - endpoints protegidos bloqueiam perfis indevidos
- Checklist:
  - [ ] criar dependências de autorização
  - [ ] aplicar em endpoints críticos
  - [ ] validar cenários de permissão e negação

### ISSUE-009 — Estruturar frontend Next.js
- ID técnico: `CZ-A02`
- Prioridade: `P0`
- Tipo: `frontend`
- Status: `todo`
- Dependências: nenhuma
- Descrição:
  - criar a base do frontend e organizar a estrutura inicial da aplicação
- Escopo:
  - criar `frontend/app`
  - configurar layout base
  - preparar rota inicial de login
- Critérios de aceite:
  - frontend sobe localmente
  - layout inicial renderiza sem erro
- Checklist:
  - [ ] criar estrutura de diretórios
  - [ ] configurar app router
  - [ ] criar layout base

### ISSUE-010 — Criar página de login no frontend
- ID técnico: `CZ-D01`
- Prioridade: `P0`
- Tipo: `frontend`
- Status: `todo`
- Dependências: `ISSUE-007`, `ISSUE-009`
- Descrição:
  - implementar interface de login integrada ao backend
- Escopo:
  - formulário
  - tratamento de erro
  - integração com API
- Critérios de aceite:
  - usuário consegue autenticar pela interface
- Checklist:
  - [ ] criar formulário
  - [ ] integrar com API
  - [ ] tratar estados de erro e loading

### ISSUE-011 — Persistir sessão no frontend
- ID técnico: `CZ-D02`
- Prioridade: `P0`
- Tipo: `frontend`
- Status: `todo`
- Dependências: `ISSUE-010`
- Descrição:
  - manter a sessão autenticada do usuário no frontend
- Escopo:
  - persistência de tokens ou sessão conforme estratégia definida
  - renovação de sessão
- Critérios de aceite:
  - usuário autenticado permanece logado conforme regra escolhida
- Checklist:
  - [ ] implementar persistência
  - [ ] implementar renovação
  - [ ] proteger acesso autenticado básico

### ISSUE-012 — Implementar modelos centrais do domínio
- ID técnico: `CZ-B04`
- Prioridade: `P0`
- Tipo: `backend`
- Status: `todo`
- Dependências: `ISSUE-003`
- Descrição:
  - criar as tabelas principais do domínio do MVP
- Escopo:
  - `questions`
  - `classes`
  - `class_students`
  - `exams`
  - `exam_questions`
  - `attempts`
  - `answers`
  - `monitoring_events`
  - `audit_logs`
- Critérios de aceite:
  - schema reflete `DATABASE.MD`
  - relacionamentos principais funcionam
- Checklist:
  - [ ] criar models
  - [ ] criar migrations
  - [ ] validar relacionamentos

### ISSUE-013 — Implementar modelo e schemas de Question
- ID técnico: `CZ-E01`
- Prioridade: `P0`
- Tipo: `backend`
- Status: `todo`
- Dependências: `ISSUE-012`
- Descrição:
  - preparar a camada de aplicação para trabalhar com questões
- Escopo:
  - schema de criação
  - schema de leitura
  - schema de atualização
- Critérios de aceite:
  - payloads válidos persistem corretamente
- Checklist:
  - [ ] criar schemas
  - [ ] validar tipagem
  - [ ] integrar com model

### ISSUE-014 — Implementar CRUD de questões no backend
- ID técnico: `CZ-E02`
- Prioridade: `P1`
- Tipo: `backend`
- Status: `todo`
- Dependências: `ISSUE-008`, `ISSUE-013`
- Descrição:
  - permitir que professores gerenciem o banco de questões
- Escopo:
  - `POST /questions`
  - `GET /questions`
  - `GET /questions/{id}`
  - `PATCH /questions/{id}`
- Critérios de aceite:
  - professor cria, consulta e atualiza questões
  - aluno não acessa área de gestão
- Checklist:
  - [ ] implementar rotas
  - [ ] implementar service
  - [ ] aplicar autorização

### ISSUE-015 — Implementar filtros de questões
- ID técnico: `CZ-E03`
- Prioridade: `P1`
- Tipo: `backend`
- Status: `todo`
- Dependências: `ISSUE-014`
- Descrição:
  - permitir busca filtrada no banco de questões
- Escopo:
  - filtros por disciplina
  - filtros por dificuldade
  - filtros por tags
- Critérios de aceite:
  - listagem responde corretamente aos filtros combinados
- Checklist:
  - [ ] adicionar filtros na query
  - [ ] validar combinações
  - [ ] cobrir com testes

### ISSUE-016 — Implementar modelo e schema de Exam
- ID técnico: `CZ-F01`
- Prioridade: `P0`
- Tipo: `backend`
- Status: `todo`
- Dependências: `ISSUE-012`
- Descrição:
  - preparar a camada de aplicação para criação e leitura de provas
- Escopo:
  - schema de criação
  - schema de leitura
- Critérios de aceite:
  - prova pode ser criada em estado `draft`
- Checklist:
  - [ ] criar schemas
  - [ ] validar model
  - [ ] integrar com service

### ISSUE-017 — Implementar vínculo ExamQuestion
- ID técnico: `CZ-F02`
- Prioridade: `P0`
- Tipo: `backend`
- Status: `todo`
- Dependências: `ISSUE-013`, `ISSUE-016`
- Descrição:
  - permitir composição de prova a partir de questões reutilizáveis
- Escopo:
  - associação prova-questão
  - ordem de exibição
  - peso da questão
- Critérios de aceite:
  - prova reutiliza questões sem duplicar conteúdo
- Checklist:
  - [ ] implementar model/service
  - [ ] validar ordenação
  - [ ] validar peso

### ISSUE-018 — Implementar rotas de prova no backend
- ID técnico: `CZ-F03`
- Prioridade: `P1`
- Tipo: `backend`
- Status: `todo`
- Dependências: `ISSUE-008`, `ISSUE-017`
- Descrição:
  - expor criação, consulta, composição e publicação de provas
- Escopo:
  - `POST /exams`
  - `GET /exams`
  - `GET /exams/{id}`
  - `POST /exams/{id}/questions`
  - `POST /exams/{id}/publish`
- Critérios de aceite:
  - professor cria e publica provas via API
- Checklist:
  - [ ] implementar rotas
  - [ ] aplicar RBAC
  - [ ] validar publicação

### ISSUE-019 — Implementar lifecycle de tentativa
- ID técnico: `CZ-G01`
- Prioridade: `P0`
- Tipo: `backend`
- Status: `todo`
- Dependências: `ISSUE-012`, `ISSUE-018`
- Descrição:
  - modelar início, execução e encerramento de tentativa
- Escopo:
  - criação de tentativa
  - mudanças de status
  - encerramento
- Critérios de aceite:
  - tentativa evolui entre estados válidos
- Checklist:
  - [ ] criar regras de transição
  - [ ] persistir status
  - [ ] validar cenários inválidos

### ISSUE-020 — Implementar endpoint de próxima questão
- ID técnico: `CZ-G02`
- Prioridade: `P0`
- Tipo: `backend`
- Status: `todo`
- Dependências: `ISSUE-019`
- Descrição:
  - entregar apenas a questão atual ao frontend
- Escopo:
  - `GET /attempts/{id}/next-question`
- Critérios de aceite:
  - apenas a questão atual é retornada
  - a prova inteira nunca é enviada ao frontend
- Checklist:
  - [ ] implementar rota
  - [ ] calcular próxima questão
  - [ ] validar restrição de uma questão por vez

### ISSUE-021 — Implementar submissão imediata de resposta
- ID técnico: `CZ-G03`
- Prioridade: `P0`
- Tipo: `backend`
- Status: `todo`
- Dependências: `ISSUE-019`
- Descrição:
  - registrar respostas imediatamente após envio do aluno
- Escopo:
  - `POST /attempts/{id}/answers`
  - persistência em `answers`
- Critérios de aceite:
  - resposta é persistida imediatamente
  - resposta fica associada à tentativa e questão corretas
- Checklist:
  - [ ] implementar rota
  - [ ] validar payload
  - [ ] persistir resposta

### ISSUE-022 — Criar tela de tentativa no frontend
- ID técnico: `CZ-G05`
- Prioridade: `P1`
- Tipo: `frontend`
- Status: `todo`
- Dependências: `ISSUE-020`, `ISSUE-021`, `ISSUE-011`
- Descrição:
  - implementar interface sequencial de realização de prova
- Escopo:
  - exibir questão atual
  - enviar resposta
  - solicitar próxima questão
- Critérios de aceite:
  - aluno consegue responder prova em fluxo sequencial
- Checklist:
  - [ ] criar página de tentativa
  - [ ] integrar próxima questão
  - [ ] integrar envio de resposta

## 3. Issues da milestone 2

### ISSUE-023 — Implementar correção automática de questões objetivas
- ID técnico: `CZ-H01`
- Prioridade: `P1`
- Tipo: `backend`
- Status: `todo`
- Dependências: `ISSUE-013`, `ISSUE-021`
- Descrição:
  - avaliar automaticamente respostas objetivas
- Escopo:
  - comparar resposta enviada com gabarito
  - preencher `is_correct`
- Critérios de aceite:
  - respostas objetivas são corrigidas corretamente
- Checklist:
  - [ ] criar serviço de correção
  - [ ] integrar com submissão de resposta
  - [ ] validar casos corretos e incorretos

### ISSUE-024 — Consolidar score da tentativa
- ID técnico: `CZ-H02`
- Prioridade: `P1`
- Tipo: `backend`
- Status: `todo`
- Dependências: `ISSUE-023`
- Descrição:
  - calcular score final da tentativa com base nos pesos da prova
- Escopo:
  - consolidar nota
  - persistir em `attempts.score`
- Critérios de aceite:
  - score corresponde ao peso das questões e acertos
- Checklist:
  - [ ] implementar cálculo
  - [ ] persistir resultado
  - [ ] validar com cenários de teste

### ISSUE-025 — Implementar captura de eventos de monitoramento no frontend
- ID técnico: `CZ-I01`
- Prioridade: `P1`
- Tipo: `frontend`
- Status: `todo`
- Dependências: `ISSUE-022`
- Descrição:
  - capturar eventos suportados durante a tentativa
- Escopo:
  - `visibilitychange`
  - `blur`
  - `focus`
  - `fullscreen_enter`
  - `fullscreen_exit`
- Critérios de aceite:
  - eventos são capturados apenas durante a tentativa
- Checklist:
  - [ ] criar hook `useMonitoring`
  - [ ] integrar no fluxo da tentativa
  - [ ] validar ciclo de vida do hook

### ISSUE-026 — Implementar ingestão de eventos de monitoramento no backend
- ID técnico: `CZ-I02`
- Prioridade: `P1`
- Tipo: `backend`
- Status: `todo`
- Dependências: `ISSUE-012`, `ISSUE-025`
- Descrição:
  - persistir eventos suportados associados à tentativa
- Escopo:
  - `POST /attempts/{id}/monitoring-events`
  - persistência em `monitoring_events`
- Critérios de aceite:
  - eventos válidos são persistidos com `attempt_id`
- Checklist:
  - [ ] criar schema
  - [ ] criar rota
  - [ ] validar tipos de evento suportados

### ISSUE-027 — Exibir aviso de monitoramento ao usuário
- ID técnico: `CZ-I04`
- Prioridade: `P1`
- Tipo: `frontend`
- Status: `todo`
- Dependências: `ISSUE-022`
- Descrição:
  - informar o usuário sobre a existência e finalidade do monitoramento
- Escopo:
  - aviso antes da tentativa
  - aviso visível durante a tentativa
- Critérios de aceite:
  - usuário é informado com clareza sobre o monitoramento
- Checklist:
  - [ ] criar componente de aviso
  - [ ] posicionar no fluxo da tentativa
  - [ ] validar visibilidade

### ISSUE-028 — Implementar exportação de dados do usuário
- ID técnico: `CZ-J01`
- Prioridade: `P1`
- Tipo: `backend`
- Status: `todo`
- Dependências: `ISSUE-007`, `ISSUE-012`
- Descrição:
  - permitir exportação estruturada dos dados essenciais do usuário
- Escopo:
  - `GET /me/data-export`
- Critérios de aceite:
  - usuário recebe seus dados essenciais em formato estruturado
- Checklist:
  - [ ] definir payload de exportação
  - [ ] implementar rota
  - [ ] validar autorização

### ISSUE-029 — Implementar testes de autenticação
- ID técnico: `CZ-K01`
- Prioridade: `P0`
- Tipo: `qa`
- Status: `todo`
- Dependências: `ISSUE-007`
- Descrição:
  - cobrir login e refresh com testes automatizados
- Critérios de aceite:
  - fluxos principais de autenticação estão cobertos
- Checklist:
  - [ ] testar login válido
  - [ ] testar login inválido
  - [ ] testar refresh

### ISSUE-030 — Implementar testes de autorização
- ID técnico: `CZ-K02`
- Prioridade: `P0`
- Tipo: `qa`
- Status: `todo`
- Dependências: `ISSUE-008`
- Descrição:
  - cobrir cenários de autorização e negação de acesso
- Critérios de aceite:
  - perfis corretos acessam o que devem
  - perfis incorretos são bloqueados
- Checklist:
  - [ ] testar acesso permitido
  - [ ] testar acesso negado
  - [ ] validar RBAC nas rotas críticas

### ISSUE-031 — Implementar testes de entrega de uma questão por vez
- ID técnico: `CZ-K03`
- Prioridade: `P1`
- Tipo: `qa`
- Status: `todo`
- Dependências: `ISSUE-020`
- Descrição:
  - validar o comportamento central do attempt engine
- Critérios de aceite:
  - testes garantem que a prova inteira não é enviada ao frontend
- Checklist:
  - [ ] testar retorno de questão única
  - [ ] testar progressão da tentativa
  - [ ] testar restrições de fluxo

### ISSUE-032 — Implementar testes de submissão imediata de resposta
- ID técnico: `CZ-K04`
- Prioridade: `P1`
- Tipo: `qa`
- Status: `todo`
- Dependências: `ISSUE-021`
- Descrição:
  - validar persistência imediata de respostas
- Critérios de aceite:
  - resposta é persistida no envio
- Checklist:
  - [ ] testar persistência da resposta
  - [ ] validar vínculo com tentativa
  - [ ] validar payload inválido

### ISSUE-033 — Implementar testes de correção automática
- ID técnico: `CZ-K05`
- Prioridade: `P1`
- Tipo: `qa`
- Status: `todo`
- Dependências: `ISSUE-023`, `ISSUE-024`
- Descrição:
  - validar correção automática e cálculo de score
- Critérios de aceite:
  - score e correção ficam cobertos por testes
- Checklist:
  - [ ] testar acerto
  - [ ] testar erro
  - [ ] testar score ponderado

### ISSUE-034 — Implementar testes de ingestão de monitoramento
- ID técnico: `CZ-K06`
- Prioridade: `P1`
- Tipo: `qa`
- Status: `todo`
- Dependências: `ISSUE-026`
- Descrição:
  - validar registro de eventos suportados de monitoramento
- Critérios de aceite:
  - ingestão de eventos fica coberta por testes
- Checklist:
  - [ ] testar evento válido
  - [ ] testar evento inválido
  - [ ] validar associação com tentativa

## 4. Issues complementares pós-milestone 2

### ISSUE-035 — Configurar Docker e Docker Compose
- ID técnico: `CZ-A03`
- Prioridade: `P0`
- Tipo: `infra`
- Status: `todo`
- Dependências: `ISSUE-001`, `ISSUE-009`

### ISSUE-036 — Definir variáveis de ambiente do projeto
- ID técnico: `CZ-A04`
- Prioridade: `P0`
- Tipo: `infra`
- Status: `todo`
- Dependências: `ISSUE-001`, `ISSUE-009`, `ISSUE-035`

### ISSUE-037 — Configurar observabilidade mínima
- ID técnico: `CZ-A05`
- Prioridade: `P2`
- Tipo: `infra`
- Status: `todo`
- Dependências: `ISSUE-001`

### ISSUE-038 — Criar índices iniciais do banco
- ID técnico: `CZ-B05`
- Prioridade: `P1`
- Tipo: `backend`
- Status: `todo`
- Dependências: `ISSUE-012`

### ISSUE-039 — Implementar auditoria de ações sensíveis
- ID técnico: `CZ-C05`
- Prioridade: `P1`
- Tipo: `security`
- Status: `todo`
- Dependências: `ISSUE-007`, `ISSUE-012`

### ISSUE-040 — Proteger rotas do frontend por perfil
- ID técnico: `CZ-D03`
- Prioridade: `P1`
- Tipo: `frontend`
- Status: `todo`
- Dependências: `ISSUE-008`, `ISSUE-011`

### ISSUE-041 — Criar dashboard inicial por perfil
- ID técnico: `CZ-D04`
- Prioridade: `P1`
- Tipo: `frontend`
- Status: `todo`
- Dependências: `ISSUE-040`

### ISSUE-042 — Criar interface de gestão de questões
- ID técnico: `CZ-E04`
- Prioridade: `P1`
- Tipo: `frontend`
- Status: `todo`
- Dependências: `ISSUE-014`, `ISSUE-015`

### ISSUE-043 — Criar interface de criação e publicação de provas
- ID técnico: `CZ-F04`
- Prioridade: `P1`
- Tipo: `frontend`
- Status: `todo`
- Dependências: `ISSUE-018`, `ISSUE-042`

### ISSUE-044 — Implementar finalização de tentativa
- ID técnico: `CZ-G04`
- Prioridade: `P1`
- Tipo: `backend`
- Status: `todo`
- Dependências: `ISSUE-020`, `ISSUE-021`

### ISSUE-045 — Implementar temporizador da tentativa
- ID técnico: `CZ-G06`
- Prioridade: `P2`
- Tipo: `frontend`
- Status: `todo`
- Dependências: `ISSUE-022`

### ISSUE-046 — Criar visualização de resultado para aluno
- ID técnico: `CZ-H03`
- Prioridade: `P2`
- Tipo: `frontend`
- Status: `todo`
- Dependências: `ISSUE-024`

### ISSUE-047 — Criar painel básico de correção para professor
- ID técnico: `CZ-H04`
- Prioridade: `P2`
- Tipo: `frontend`
- Status: `todo`
- Dependências: `ISSUE-024`

### ISSUE-048 — Criar relatório básico de monitoramento para professor
- ID técnico: `CZ-I03`
- Prioridade: `P2`
- Tipo: `frontend`
- Status: `todo`
- Dependências: `ISSUE-026`

### ISSUE-049 — Implementar solicitação de anonimização
- ID técnico: `CZ-J02`
- Prioridade: `P2`
- Tipo: `backend`
- Status: `todo`
- Dependências: `ISSUE-028`

### ISSUE-050 — Definir política técnica de retenção
- ID técnico: `CZ-J03`
- Prioridade: `P2`
- Tipo: `product-tech`
- Status: `todo`
- Dependências: `ISSUE-012`

## 5. Ordem sugerida de abertura

1. ISSUE-001
2. ISSUE-002
3. ISSUE-003
4. ISSUE-004
5. ISSUE-005
6. ISSUE-006
7. ISSUE-007
8. ISSUE-008
9. ISSUE-009
10. ISSUE-010
11. ISSUE-011
12. ISSUE-012
13. ISSUE-013
14. ISSUE-014
15. ISSUE-015
16. ISSUE-016
17. ISSUE-017
18. ISSUE-018
19. ISSUE-019
20. ISSUE-020
21. ISSUE-021
22. ISSUE-022
23. ISSUE-023
24. ISSUE-024
25. ISSUE-025
26. ISSUE-026
27. ISSUE-027
28. ISSUE-028
29. ISSUE-029
30. ISSUE-030
31. ISSUE-031
32. ISSUE-032
33. ISSUE-033
34. ISSUE-034

## 6. Resultado esperado após milestone 2

Ao concluir as issues das milestones 1 e 2, o sistema deve permitir:

- autenticação segura
- RBAC básico
- criação e gestão de questões
- criação e publicação de provas
- tentativa sequencial com uma questão por vez
- submissão imediata de respostas
- correção automática básica
- score consolidado
- monitoramento suportado com transparência
- exportação essencial de dados do usuário
- cobertura inicial dos fluxos críticos
# COLA-ZERO — Plano de Implementação

## 1. Objetivo do sistema

Plataforma de avaliação online para instituições de ensino com foco em:

- banco de questões reutilizável
- criação e aplicação de provas
- execução de tentativas com uma questão por vez
- correção automática e manual
- registro de eventos de monitoramento
- auditoria de ações sensíveis
- conformidade com LGPD

O eixo central da arquitetura é:

**Question Bank + Attempt Engine**

O banco de questões (Question Bank) é o repositório central de conteúdo. As provas (Exams) são configurações de entrega compostas por questões reutilizáveis. O histórico acadêmico é representado por tentativas (Attempts) e respostas (Answers).

Fluxo do domínio: Question -> Exam -> Attempt -> Answer

## 2. Princípios obrigatórios

### 2.1 Simplicidade

- preferir soluções simples
- evitar abstrações prematuras
- evitar lógica de negócio em rotas e componentes visuais

### 2.2 Segurança primeiro

Toda funcionalidade deve ser avaliada quanto a:

- autenticação
- autorização
- exposição de dados
- impacto em LGPD

### 2.3 Privacidade por padrão

Coletar apenas:

- dados de conta
- respostas da prova
- eventos relacionados à tentativa
- logs de auditoria

Não coletar:

- arquivos pessoais
- conteúdo do dispositivo
- histórico de navegação
- dados sem finalidade clara

## 3. Stack tecnológica

### Backend

- Python 3.12
- FastAPI 0.137.x
- SQLAlchemy 2.0.x
- Alembic 1.18.x
- PostgreSQL 16.14
- Pydantic 2.13.x

### Frontend

- Next.js 16.2.x
- React 19.2.x
- TypeScript 5.9.x
- TailwindCSS 4.3.x

### Infraestrutura

- Docker
- Docker Compose
- lint desde a fundação do projeto
- Prettier no frontend e em arquivos compatíveis de configuração

## 4. Estrutura de diretórios alvo

```text
cola-zero/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   └── api.py
│   │   ├── services/
│   │   ├── repositories/
│   │   └── utils/
│   ├── tests/
│   └── Dockerfile
├── frontend/
│   ├── app/
│   ├── components/
│   ├── hooks/
│   ├── services/
│   └── Dockerfile
├── infra/
│   ├── docker-compose.yml
│   ├── postgres/
│   └── nginx/
├── .env.example
└── README.md
```

## 5. Regras de domínio e banco de dados

### 5.1 Identificadores

- todas as chaves primárias devem usar UUID
- não usar IDs incrementais

### 5.2 Auditoria e histórico

- não apagar registros acadêmicos importantes
- preferir soft delete ou arquivamento
- respostas não devem ser sobrescritas quando histórico for necessário

### 5.3 Banco de questões

- questões devem ser reutilizáveis
- uma questão pode pertencer a várias provas
- prova não deve duplicar conteúdo de questão
- relacionamento correto: `Exam -> ExamQuestion -> Question`

### 5.4 Entidades principais

#### User

- id
- email
- password_hash
- role (`student`, `teacher`, `admin`)
- created_at
- updated_at

#### Question

- id
- statement
- type
- options
- correct_answer
- explanation
- subject
- difficulty
- tags
- image_url
- created_by
- created_at

#### Exam

- id
- title
- class_id
- status (`draft`, `published`, `archived`)
- total_time_seconds
- max_attempts (default = 1)
- randomization_enabled
- created_by
- created_at

#### ExamQuestion

- id
- exam_id
- question_id
- display_order
- weight

#### Attempt

- id
- exam_id
- student_id
- attempt_number
- status (`not_started`, `in_progress`, `submitted`, `graded`)
- started_at
- ended_at
- score

#### Answer

- id
- attempt_id
- question_id
- answer_payload
- is_correct
- answered_at

#### SecurityEvent

- id
- attempt_id
- event_type
- metadata
- created_at

#### AuditLog

- id
- user_id
- event_type
- metadata
- created_at

## 6. Papéis e permissões

### Student

Pode:

- ver provas atribuídas
- iniciar tentativas
- responder questões
- ver resultados liberados

Não pode:

- acessar banco de questões
- acessar dados de outros alunos
- modificar provas

### Teacher

Pode:

- criar questões
- gerenciar banco de questões
- criar provas
- corrigir provas
- ver relatórios de monitoramento

### Administrator

Pode:

- gerenciar usuários
- gerenciar instituições
- acessar configurações da plataforma
- visualizar logs de auditoria

## 7. Backend

### 7.1 Organização

- rotas finas
- lógica de negócio em services
- acesso a dados em repositories quando fizer sentido
- uso de dependency injection
- validações com schemas

### 7.2 Rotas principais do MVP

#### Autenticação

- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`

#### Questões

- `POST /questions`
- `GET /questions`
- `GET /questions/{id}`
- `PATCH /questions/{id}`

#### Provas

- `POST /exams`
- `GET /exams`
- `GET /exams/{id}`
- `POST /exams/{id}/questions`
- `POST /exams/{id}/publish`

#### Tentativas

- `POST /attempts`
- `GET /attempts/{id}`
- `GET /attempts/{id}/next-question`
- `POST /attempts/{id}/submit`

#### Respostas

- `POST /attempts/{id}/answers`

#### Eventos de Segurança

- `POST /attempts/{id}/security-events`

#### LGPD

- `GET /me/data-export`
- `POST /me/request-anonymization`
- `GET /privacy-policy`
- `POST /consents/monitoring`

### 7.3 Fluxo crítico da prova

#### Entrega de questão

`GET /attempts/{id}/next-question`

Resposta esperada:

```json
{
  "question_id": "uuid",
  "statement": "...",
  "options": ["A", "B", "C", "D"],
  "current_index": 1,
  "total_questions": 10
}
```

Regras:

- o frontend nunca recebe a prova inteira
- apenas a próxima questão liberada deve ser retornada
- a próxima questão só deve ser entregue após persistência da resposta anterior, quando aplicável

#### Envio de resposta

`POST /attempts/{id}/answers`

Regras:

- salvar imediatamente
- permitir correção automática quando aplicável
- registrar auditoria quando necessário

### 7.4 Regras de Negócio Críticas

#### Regras de Publicação de Prova

Uma prova só pode ser publicada (`POST /exams/{id}/publish`) se:

- Possuir um título
- Conter pelo menos 1 questão associada
- Todas as questões associadas existirem no banco de dados
- Todos os pesos de questões forem maiores que 0
- A soma total do peso das questões (`ExamQuestion.weight`) for exatamente 100
- Estiver associada a uma turma (`class_id`)
- Possuir um limite de tempo válido configurado (`total_time_seconds` maior que 0)
- O usuário requisitante for o professor dono da prova ou um administrador

#### Regras de Tentativa

A configuração `max_attempts` da prova (tabela `exams`) define o número máximo de tentativas permitidas (padrão = 1).

Regras de controle no backend:

- Permitir apenas uma tentativa ativa (`in_progress`) por aluno por prova.
- Se uma tentativa ativa já existir, o backend deve reutilizar/retornar a tentativa ativa em vez de criar uma nova.
- Uma nova tentativa só pode ser criada se a contagem total de tentativas finalizadas/submetidas for menor que `max_attempts`.
- Tentativas submetidas (`submitted`) não podem ser alteradas.
- Tentativas corrigidas (`graded`) são imutáveis.

## 8. Frontend

### 8.1 Estrutura alvo

```text
frontend/
├── app/
│   ├── login/
│   ├── dashboard/
│   ├── exams/
│   ├── attempt/
│   ├── teacher/
│   ├── admin/
│   └── layout.tsx
├── components/
│   ├── QuestionCard.tsx
│   ├── Timer.tsx
│   └── MonitoringNotice.tsx
├── hooks/
│   └── useMonitoring.ts
└── services/
    ├── api.ts
    ├── auth.ts
    ├── exams.ts
    ├── attempts.ts
    └── monitoring.ts
```

### 8.2 Regras de implementação

- componentes reutilizáveis
- tipagem forte em TypeScript
- evitar lógica de negócio dentro de componentes visuais
- páginas pequenas e focadas

### 8.3 Fluxo da tentativa

1. aluno autentica
2. aluno inicia tentativa
3. frontend solicita próxima questão
4. backend entrega apenas a questão atual
5. aluno responde
6. frontend envia resposta imediatamente
7. backend persiste e retorna estado atualizado
8. frontend solicita próxima questão

## 9. Eventos de Segurança (Security Events) e Monitoramento

COLA-ZERO não é um lockdown browser.

A plataforma pode:

- detectar eventos
- registrar eventos em `security_events`
- gerar relatórios

Lembrete de Segurança (A plataforma não deve alegar/afirmar que consegue):

- detectar uso de ChatGPT
- detectar outro dispositivo
- detectar telefones externos
- detectar capturas de tela de forma confiável
- impedir toda forma de cola

A plataforma apenas registra e reporta eventos observáveis do navegador.

### 9.1 Eventos suportados

- `visibilitychange`
- `blur`
- `focus`
- `fullscreen_enter`
- `fullscreen_exit`

### 9.2 Regras de transparência

- o usuário deve ser informado sobre o monitoramento
- o propósito do monitoramento deve ser explícito
- a coleta deve ser limitada ao contexto da prova

## 10. LGPD

Desde a primeira versão, implementar:

- aviso de monitoramento
- base de exportação de dados do usuário
- suporte a anonimização quando legalmente permitido
- política de retenção para logs e registros acadêmicos

## 11. Segurança

### 11.1 Autenticação

- JWT Access Token: Armazenado pelo backend em cookie seguro HttpOnly (`Secure`, `SameSite=Lax`), expiração curta (15-30 min).
- JWT Refresh Token: Armazenado pelo backend em cookie seguro HttpOnly (`Secure`, `SameSite=Strict`), expiração longa (7-30 dias).
- Armazenamento no Cliente: Estritamente proibido utilizar `localStorage` ou `sessionStorage` para armazenar tokens JWT.
- Hash de senha: Atualmente utiliza bcrypt com salt (ADR-001); Argon2 permanece como recomendação futura de hardening pós-MVP.
- Nunca armazenar senha em texto puro.

### 11.2 Autorização

- RBAC obrigatório.
- Todo endpoint deve validar permissões baseando-se nos perfis `STUDENT`, `TEACHER` e `ADMIN`.

### 11.3 Auditoria

Registrar ações sensíveis. **Importante:** O log de auditoria para sucesso e falha de login é obrigatório e está pendente de implementação para prontidão de produção (Production Readiness). A autenticação não é considerada pronta para produção até que o logging de auditoria exista.

Ações auditáveis planejadas:
- login (pendente: validação de credenciais funcional, logging de auditoria pendente)
- troca de senha 
- criação de prova
- alteração de nota
- publicação de prova

## 12. Testes obrigatórios

Abordagem obrigatória para módulos críticos:

- aplicar TDD nas partes com maior risco funcional e de segurança
- ciclo: escrever teste que falha, implementar o mínimo para passar, refatorar sem quebrar comportamento
- todo bug crítico corrigido deve receber teste de regressão

Prioridade de cobertura:

1. autenticação
2. autorização
3. entrega de prova
4. submissão de resposta
5. correção
6. monitoramento
7. healthcheck, contratos básicos de API e integrações essenciais da fundação

## 13. Ordem de implementação (Milestone Order)

*Nota de Prioridade e Arquitetura:*
- A **avaliação online (Online Assessment)** continua sendo a arquitetura de plataforma primária do COLA-ZERO.
- A priorização do módulo **COLA-ZERO OMR** como a Milestone 2 é uma **decisão de prioridade de produto**, e não uma dependência arquitetural. O OMR é um subsistema independente e desacoplado do motor online.

### Fase 1 — Autenticação e RBAC (Backend)
- Estrutura inicial do backend FastAPI, conexão PostgreSQL, Docker e Docker Compose, lint e Prettier.
- Healthcheck com TDD.
- Modelo `User`.
- Hash de senha com bcrypt (ADR-001) e geração de JWT (cookies HttpOnly).
- Dependências e middlewares de RBAC (`STUDENT`, `TEACHER`, `ADMIN`).
- *Nota:* Logging de auditoria de login (sucesso/falha) está pendente e é mandatório para produção.

### Fase 2 — Módulo OMR (MVP) — Banco de Dados e Layouts em Código
- Criação das tabelas de OMR (`omr_templates` e `omr_scans`) com UUID.
- Criação da tabela unificada de notas (`grades`) com UUID, associando notas consolidando de qualquer fonte (OMR ou ONLINE).
- Definição do relacionamento opcional com `exams` (Modo Standalone e Integrado).
- Implementação de layouts versionados mantidos no código (`app/core/omr_layouts.py`). O banco apenas salvará a string referencial no campo `layout_version`.
- Migrações do banco via Alembic.

### Fase 3 — Módulo OMR (MVP) — Geração de PDF e OpenCV Engine
- Geração de PDF com **ReportLab** contendo 4 âncoras e o `student_code` de 5 dígitos preenchido automaticamente pelo gerador.
- OpenCV + NumPy para alinhamento perspectivo de imagem (deskew & warp).
- Algoritmo de OMR para leitura do código do aluno (5 colunas x 10 linhas) e marcação das alternativas por densidade relativa.

### Fase 4 — Módulo OMR (MVP) — Upload API, Correção Automática e Revisão UI
- Endpoint de upload aceitando estritamente **uma única imagem por requisição (JPG, JPEG, PNG)**.
- Lógica de processamento assíncrona em background e cálculo automático da nota.
- Gravação da nota final confirmada pelo professor na tabela unificada `grades`.
- Tela de upload no frontend.
- Interface de revisão visual com overlay colorido em cima das bolhas detectadas e suporte a ajustes manuais.

### Fase 5 — Modelagem Completa de Domínio Acadêmico Core e Migrações
- Criação de tabelas e migrations via Alembic:
  - `classes`, `class_students`, `questions` (com suporte a parent_id, version e is_active para imutabilidade de versões publicadas), `exams`, `exam_questions`, `attempts`, `answers`, `security_events`, `audit_logs`
- Estabilização do modelo de dados (Core Academic Domain Freeze).

### Fase 6 — Banco de Questões (Question Bank) e Provas (Exam Engine)
- CRUD de questões pelo professor no backend e frontend.
- Filtros de questões por disciplina, dificuldade e tags.
- Criação, composição e publicação de provas (Exams) compostas por `ExamQuestion`.

### Fase 7 — Motor de Tentativas Online (Attempt Engine)
- Lifecycle da tentativa (`Attempt`), incluindo ordem de tentativas e autosave de respostas (`Answer`).
- Entrega de uma questão por vez e envio sequencial.
- Finalização, cálculo do score e gravação na tabela unificada `grades`.

### Fase 8 — Eventos de Segurança (Security Events) e Auditoria de Sistema
- Captura de eventos de tela no frontend e persistência em `security_events`.
- Ingestão de logs de auditoria para ações administrativas e pedagógicas no backend.

### Fase 9 — Recursos de LGPD
- Aviso e consentimento transparente de monitoramento.
- Endpoints operacionais: `GET /me/data-export`, `POST /me/request-anonymization`, `GET /privacy-policy`, `POST /consents/monitoring`.

### Fase 10 — Qualidade, Hardening e Testes E2E
- Testes integrados de ponta a ponta dos fluxos críticos online e offline.
- Rate limiting, logs de auditoria de login e hardening de segurança.

## 14. Critérios de MVP concluído

O MVP é considerado pronto quando:
- Usuários autenticam com segurança usando cookies HttpOnly (Lax/Strict) e logs de auditoria de login estão ativos.
- Módulo OMR independente de correção offline de imagens de gabaritos funciona (standalone e integrado).
- Professores gerenciam o Question Bank e criam/publicam provas válidas.
- Alunos realizam tentativas online sequenciais (uma questão por vez) com autosave.
- Eventos de segurança (security_events) e auditoria de ações sensíveis são persistidos.
- Requisitos essenciais e endpoints operacionais de LGPD estão disponíveis.

## 15. Fora do escopo do MVP

Itens possíveis para versões futuras:
- Geração assistida por IA de questões.
- Análise estatística de itens e calibração de dificuldade.
- Processamento em lote de PDFs multipágina (OMR).
- Integração com Safe Exam Browser.
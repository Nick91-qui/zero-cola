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

A prova é uma configuração de entrega de questões. A entidade principal do domínio é a questão.

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

#### MonitoringEvent

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

#### Monitoramento

- `POST /attempts/{id}/monitoring-events`

#### LGPD

- `GET /me/data-export`
- `POST /me/anonymization-request`

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

## 9. Monitoramento

COLA-ZERO não é um lockdown browser.

A plataforma pode:

- detectar eventos
- registrar eventos
- gerar relatórios

A plataforma não deve afirmar que consegue:

- detectar uso de ChatGPT
- detectar outro dispositivo
- detectar telefones externos
- detectar capturas de tela de forma confiável
- impedir toda forma de cola

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

- JWT access token
- JWT refresh token
- Argon2 preferencialmente
- bcrypt como alternativa aceitável
- nunca armazenar senha em texto puro

### 11.2 Autorização

- RBAC obrigatório
- todo endpoint deve validar permissões

### 11.3 Auditoria

Registrar ações sensíveis como:

- login
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

## 13. Ordem de implementação

### Fase 1 — Fundação

- estrutura inicial do backend FastAPI
- estrutura inicial do frontend Next.js
- configuração PostgreSQL
- configuração Docker e Docker Compose
- configuração de lint
- configuração de Prettier
- healthcheck com TDD
- autenticação com JWT guiada por TDD
- modelo `User`
- RBAC básico guiado por TDD

### Fase 2 — Banco de questões

- modelo `Question`
- CRUD de questões
- filtros por disciplina, dificuldade e tags
- associação de questões a professores

### Fase 3 — Provas

- modelo `Exam`
- modelo `ExamQuestion`
- criação e edição de provas
- publicação de provas

### Fase 4 — Tentativas

- modelo `Attempt`
- lifecycle da tentativa
- entrega de uma questão por vez
- temporizador da prova

### Fase 5 — Respostas e correção

- modelo `Answer`
- submissão imediata de respostas
- correção automática para questões objetivas
- score consolidado

### Fase 6 — Monitoramento e auditoria

- captura de eventos suportados no frontend
- persistência de `MonitoringEvent`
- `AuditLog` para ações sensíveis
- relatório simples para professores

### Fase 7 — LGPD

- aviso de transparência
- exportação de dados
- anonimização quando aplicável
- retenção e governança de dados

## 14. Critérios de MVP concluído

O MVP é considerado pronto quando:

- usuários autenticam com segurança
- professores criam questões
- professores criam e publicam provas
- alunos realizam tentativas
- respostas são persistidas e corrigidas
- eventos de monitoramento são registrados
- relatórios básicos são gerados
- requisitos essenciais de LGPD são atendidos

## 15. Fora do escopo do MVP

Itens possíveis para versões futuras:

- geração assistida por IA de questões
- análise estatística de itens
- calibração de dificuldade
- learning analytics
- multi-tenancy institucional avançado
- integração com Safe Exam Browser

Esses itens não devem influenciar a arquitetura mínima necessária do MVP.
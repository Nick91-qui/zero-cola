# COLA-ZERO — Secure Online Assessment & OMR Platform

COLA-ZERO é uma plataforma educacional de avaliação segura para instituições de ensino, centrada no **Gabarito (Answer Key)** como conceito principal de domínio. O sistema já suporta entrega dinâmica de exames online, correção automática por **Leitura Óptica de Cartão-Resposta (OMR)** para provas físicas impressas, repositório opcional de **Banco de Questões**, turmas com vínculos explícitos, auditoria, consentimentos e infraestrutura LGPD básica.

---

## 1. Visão Geral e Arquitetura

O sistema é construído sobre o princípio central:

> **Answer Key + Attempt Engine** *(Gabarito + Motor de Tentativas/Avaliação)*

O **Gabarito (Answer Key)** é a unidade operacional central do sistema. O **Banco de Questões (Question Bank)** atua como um **produtor opcional de Gabaritos**, permitindo a reutilização de questões, enquanto avaliações com Gabarito direto funcionam sem dependência de acervos de questões.

- **Backend**: Python 3.12, FastAPI 0.137.x, SQLAlchemy 2.0.x, Alembic 1.18.x, OpenCV (Motor OMR), ReportLab (Gerador de PDF OMR), Pydantic 2.13.x.
- **Frontend**: Next.js 16.2.x (App Router), React 19.2.x, TypeScript 5.9.x, TailwindCSS 4.3.x, Vitest.
- **Banco de Dados**: PostgreSQL 16.14 (Chaves Primárias em UUID v4).
- **Infraestrutura**: Docker & Docker Compose.

---

## 2. Índice da Documentação (Documentation Index)

A documentação do COLA-ZERO é organizada com base no princípio de **Fonte Única da Verdade (Single Source of Truth)**. Cada assunto possui exatamente um documento autoritativo:

| Documento | Assunto / Responsabilidade |
|-----------|----------------------------|
| [README.md](file:///var/home/nmoreira/Projetos/cola-zero/README.md) | Visão geral do projeto, guia de instalação, execução e índice da documentação. |
| [ARCHITECTURE.md](file:///var/home/nmoreira/Projetos/cola-zero/ARCHITECTURE.md) | **Fonte da Verdade Arquitetural**: Modelo de domínio centrado no Gabarito, modelo de dados relacional (PostgreSQL), interações entre componentes e decisões de design. |
| [TARGET_DOMAIN_MODEL.md](file:///var/home/nmoreira/Projetos/cola-zero/TARGET_DOMAIN_MODEL.md) | Especificação aprovada do modelo de domínio alvo e das etapas de implementação principais. |
| [STATUS_ATUAL.md](file:///var/home/nmoreira/Projetos/cola-zero/STATUS_ATUAL.md) | **Status do Projeto**: Funcionalidades já implementadas, relatórios de testes, limitações conhecidas e débitos técnicos. |
| [ROADMAP.md](file:///var/home/nmoreira/Projetos/cola-zero/ROADMAP.md) | **Roadmap e Planejamento**: Fases futuras de desenvolvimento, prioridades, dependências e Definition of Done (DoD). |
| [PLANO_AVALIACOES.md](file:///var/home/nmoreira/Projetos/cola-zero/PLANO_AVALIACOES.md) | Especificação funcional do sistema de avaliações centrado no Gabarito, ciclo de vida de provas, fluxos de trabalho (Workflow A e B), tentativas online e consolidação de notas. |
| [PLANO_BANCO_QUESTOES.md](file:///var/home/nmoreira/Projetos/cola-zero/PLANO_BANCO_QUESTOES.md) | Especificação do Banco de Questões como produtor opcional de Gabaritos, versionamento imutável e habilidades SEDU/BNCC. |
| [PLANO_OMR.md](file:///var/home/nmoreira/Projetos/cola-zero/PLANO_OMR.md) | Pipeline de Leitura Óptica de Cartão-Resposta (OMR) validado contra o Gabarito. |
| [PLANO_DASHBOARD.md](file:///var/home/nmoreira/Projetos/cola-zero/PLANO_DASHBOARD.md) | Analytics pedagógico baseado no Gabarito, desempenho por habilidade SEDU/BNCC, relatórios executivos e exportações (PDF/XLSX). |
| [PLANO_ANTI_COLA.md](file:///var/home/nmoreira/Projetos/cola-zero/PLANO_ANTI_COLA.md) | Monitoramento de integridade em provas online, eventos de segurança de tela (`security_events`), auditoria, consentimento e LGPD. |
| [PLANO_MODELO_ACADEMICO.md](file:///var/home/nmoreira/Projetos/cola-zero/PLANO_MODELO_ACADEMICO.md) | Modelo acadêmico de turmas, matrículas, professores e atribuição multi-turma de exames. |
| [AGENTS.md](file:///var/home/nmoreira/Projetos/cola-zero/AGENTS.md) | Convenções de código, padrões do repositório, fluxo de trabalho e instruções para agentes de IA. |
| [docs/archive/](file:///var/home/nmoreira/Projetos/cola-zero/docs/archive/) | Arquivo histórico de planejamentos técnicos anteriores e backlog inicial. |

---

## 3. Ambiente de Desenvolvimento com Docker Compose

O projeto é totalmente containerizado para desenvolvimento local rápido e reproduzível.

### Serviços Containerizados

- **`postgres`** (`cola_zero_postgres`): Banco de dados relacional PostgreSQL 16 na porta `5432`.
- **`backend`** (`cola_zero_backend`): Aplicação FastAPI com execução automática de migrations Alembic no startup, escutando na porta `8000`.
- **`frontend`** (`cola_zero_frontend`): Aplicação Next.js (com dev server e Turbopack) escutando na porta `3000`.

---

### Como Iniciar o Projeto

1. Certifique-se de que o Docker (ou Podman com `docker compose`) esteja instalado e rodando.
2. Na raiz do repositório, execute:

```bash
docker compose up -d --build
```
*(ou utilize `make up`)*

3. Para aplicar ou verificar migrações de banco de dados manualmente:

```bash
docker compose exec backend alembic upgrade head
```
*(ou utilize `make migrate`)*

---

### Como Verificar o Status dos Containers

Para listar os containers ativos e suas portas:

```bash
docker compose ps
```

Para visualizar os logs em tempo real:

```bash
docker compose logs -f
```

---

### URLs de Desenvolvimento

- **Frontend (Interface)**: [http://localhost:3000](http://localhost:3000)
- **Backend API (Base)**: [http://localhost:8000](http://localhost:8000)
- **Documentação Interativa Swagger / OpenAPI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Healthcheck da API**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## 4. Configuração do Banco de Dados PostgreSQL & Variáveis de Ambiente

### Variáveis de Ambiente Padrão (Desenvolvimento Local)

No arquivo `.env` (baseado em `.env.example`):

```env
POSTGRES_USER=colazero
POSTGRES_PASSWORD=colazero
POSTGRES_DB=colazero
DATABASE_URL=postgresql+psycopg://colazero:colazero@postgres:5432/colazero
SECRET_KEY=dev-secret-key-change-in-production
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### Como Acessar o Banco de Dados via Terminal (`psql`)

Para abrir o terminal interativo do PostgreSQL:

```bash
docker compose exec postgres psql -U colazero -d colazero
```

Comandos úteis dentro do `psql`:

- `\dt` — Lista todas as tabelas criadas no banco de dados (`users`, `questions`, `exams`, `attempts`, `grades`, `omr_templates`, `omr_scans`, etc.).
- `SELECT id, email, role, student_code FROM users;` — Consulta usuários cadastrados.
- `SELECT id, student_id, score, source_type FROM grades;` — Consulta notas unificadas registradas.
- `\q` — Sair do terminal psql.

---

## 5. Execução de Testes Automatizados

### Testes do Backend (Pytest)

Para executar a suíte de testes unitários e de integração do backend:

```bash
docker compose exec backend pytest
```

### Testes do Frontend (Vitest)

Para executar os testes do frontend:

```bash
docker compose exec frontend npm test
```

---

## 6. Estrutura de Diretórios do Repositório

```text
cola-zero/
├── backend/
│   ├── alembic/                # Migrações do banco de dados
│   ├── app/
│   │   ├── api/                # Rotas FastAPI (v1)
│   │   ├── core/               # Configurações, segurança (JWT) e layouts OMR em código
│   │   ├── db/                 # Sessão do SQLAlchemy
│   │   ├── models/             # Entidades SQLAlchemy (User, Question, Exam, OMR, Grade, etc.)
│   │   ├── repositories/       # Camada de repositório
│   │   ├── schemas/            # Schemas Pydantic
│   │   └── services/           # Lógica de negócio, motor OMR (OpenCV) e gerador de PDF
│   └── tests/                  # Suíte de testes pytest
├── frontend/
│   ├── app/                    # Páginas Next.js (App Router: auth, dashboard, attempts, omr, exams)
│   ├── lib/                    # Cliente de API e utilitários
│   └── tests/                  # Testes do frontend (Vitest)
├── docs/
│   └── archive/                # Documentos de planejamento técnicos legados e arquivados
├── docker-compose.yml          # Orquestração de containers
├── Makefile                    # Atalhos para comandos do Docker
├── ARCHITECTURE.md             # Fonte Única da Verdade da Arquitetura e Modelo de Dados
├── STATUS_ATUAL.md             # Status Atual das Implementações
├── ROADMAP.md                  # Planejamento das Próximas Fases
├── PLANO_AVALIACOES.md         # Especificação de Avaliações e Tentativas
├── PLANO_BANCO_QUESTOES.md     # Especificação do Banco de Questões (Produtor Opcional)
├── PLANO_OMR.md                # Especificação do Módulo OMR Impresso
├── PLANO_DASHBOARD.md          # Especificação do Analytics Pedagógico
├── PLANO_ANTI_COLA.md          # Especificação de Integridade Online e LGPD
├── PLANO_MODELO_ACADEMICO.md   # Especificação do Modelo Acadêmico de Turmas
├── AGENTS.md                   # Diretrizes para Agentes de IA
└── README.md                   # Visão Geral do Projeto e Guia de Instalação
```

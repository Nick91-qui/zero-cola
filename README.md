# COLA-ZERO — Secure Online Assessment & OMR Platform

COLA-ZERO é uma plataforma educacional de avaliação segura, combinando gestão de banco de questões, entrega dinâmica de exames online e um **módulo de Leitura Óptica de Cartão-Resposta (OMR)** para correção automática de provas físicas.

---

## 1. Visão Geral e Arquitetura

O sistema é construído sobre o princípio central:

> **Question Bank + Attempt Engine**

- **Backend**: Python 3.12, FastAPI 0.137.x, SQLAlchemy 2.0.x, Alembic 1.18.x, OpenCV (motor OMR), ReportLab (gerador de PDF OMR), Pydantic 2.13.x.
- **Frontend**: Next.js 16.2.x (App Router), React 19.2.x, TypeScript 5.9.x, TailwindCSS 4.3.x, Vitest.
- **Banco de Dados**: PostgreSQL 16.14.
- **Infraestrutura**: Docker & Docker Compose.

---

## 2. Status Funcional do Projeto

### ✅ Funcionalidades Implementadas e Validadas

1. **Milestone 1 — Autenticação e Gestão de Identidade (RBAC)**
   - Cadastro e Login de Usuários com perfis (`teacher`, `student`, `admin`).
   - `student_code` (código de 5 dígitos) obrigatório para o perfil de estudante.
   - Autenticação via JWT (Access Token e Refresh Token) armazenados com segurança pelo backend em cookies HttpOnly (`SameSite=Lax/Strict`).
   - Hashing de senhas com `bcrypt`.
   - Consulta e atualização de perfil (`GET /api/v1/auth/me`, `PATCH /api/v1/auth/me`).

2. **Milestone 2 — Módulo OMR Standalone (Leitura Óptica de Cartão-Resposta)**
   - Criação de gabaritos/templates OMR (layouts `v1_std_20q` de 20 questões e `v1_std_50q` de 50 questões).
   - Geração automática da folha de respostas em **PDF** para impressão e **preview PNG** de calibração.
   - Upload de digitalizações/fotos do cartão-resposta (formatos JPG/PNG).
   - Motor visual OpenCV para detecção de marcas de alinhamento, código do aluno (5 dígitos) e bolhas preenchidas (alternativas A–E).
   - Processamento de imagem, correção automática comparando a imagem com o gabarito.
   - Interface de revisão para verificação de respostas detectadas e confirmação de nota final, persistida na entidade unificada `grades`.

---

### ⏳ Funcionalidades Planejadas / Em Desenvolvimento

- **Milestone 3 — Question Bank & Engine de Provas Online**:
  - Banco de Questões reutilizáveis (professores).
  - Composição e publicação de exames online com entrega de **uma questão por vez**.
  - Persistência imediata de respostas por tentativa (Autosave).
- **Monitoramento de Tentativas Online**:
  - Registro de eventos do navegador (`visibilitychange`, `blur`, `focus`, `fullscreen enter/exit`) na tabela `security_events`.
- **Integração OMR ↔ Exam**:
  - Vinculação direta de folhas OMR a exames do Question Bank.
- **Auditoria e LGPD**:
  - Logs detalhados de auditoria e rotas de exportação/anonimização de dados do usuário.

---

## 3. Ambiente de Desenvolvimento com Docker Compose

O projeto é totalmente containerizado para desenvolvimento local rápido e reproduzível.

### Serviços Existentes

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

### Como Acessar o Banco de Dados e Verificar Tabelas

Para abrir o terminal interativo do PostgreSQL (`psql`):

```bash
docker compose exec postgres psql -U colazero -d colazero
```

Comandos úteis dentro do `psql`:

- `\dt` — Lista todas as tabelas criadas no banco de dados (`users`, `omr_templates`, `omr_scans`, `grades`, `alembic_version`, etc.).
- `SELECT id, email, role, student_code FROM users;` — Consulta usuários cadastrados.
- `SELECT id, title, total_questions FROM omr_templates;` — Consulta gabaritos OMR.
- `SELECT id, status, score_percentage FROM omr_scans;` — Consulta digitalizações de folhas.
- `SELECT id, student_id, score, max_score, source_type FROM grades;` — Consulta notas confirmadas.
- `\q` — Sair do psql.

---

## 5. Fluxo OMR Validado (Passo a Passo)

O fluxo completo de correção OMR avulsa foi validado de ponta a ponta:

1. **Professor cria uma conta**:
   - Acesse [http://localhost:3000/auth/register](http://localhost:3000/auth/register) e registre-se com o perfil **Teacher**.
2. **Professor cria um gabarito/template**:
   - Acesse o dashboard do professor e navegue até **Módulo OMR** (`/omr`).
   - Clique em **Novo Gabarito**, insira o título, selecione a quantidade de questões (ex: 20 questões) e defina a chave de respostas (ex: Q1=A, Q2=B, etc.).
3. **Sistema gera e permite baixar a folha**:
   - O sistema gera dinamicamente a folha de respostas em **PDF** para download (ou preview PNG).
4. **Folha é respondida/preenchida**:
   - A folha em PDF é impressa e preenchida manualmente pelo aluno (ou preenchida digitalmente sobre a imagem PNG de preview para testes).
5. **Folha respondida é enviada ao sistema**:
   - No painel do template, faça o upload do arquivo de imagem preenchido (JPG/PNG).
6. **Sistema processa a imagem**:
   - O motor visual OpenCV realiza o pré-processamento, alinhamento por âncoras, leitura do código do aluno (5 dígitos) e extração do preenchimento das bolhas.
7. **Sistema realiza a correção**:
   - O backend compara as respostas extraídas da imagem com a chave de respostas do gabarito e calcula a pontuação.
8. **Resultado da correção é retornado**:
   - A tela exibe o resultado do scanner com os marcadores visuais. O professor pode ajustar o código do aluno ou respostas se necessário e clicar em **Confirmar Nota**, salvando o registro final na tabela `grades`.

---

## 6. Testes e Qualidade

### Testes do Backend (Pytest)

Para executar a suíte completa de testes unitários e de integração do backend:

```bash
docker compose exec backend pytest
```

*(Resultado: 37 testes automatizados cobrindo autenticação, modelos, serviços e rotas de OMR com 100% de aprovação).*

### Testes do Frontend (Vitest)

Para executar os testes do frontend:

```bash
docker compose exec frontend npm test
```

---

## 7. Estrutura do Repositório

```text
cola-zero/
├── backend/
│   ├── alembic/                # Migrações do banco de dados
│   ├── app/
│   │   ├── api/                # Rotas FastAPI (v1)
│   │   ├── core/               # Configurações e segurança (JWT)
│   │   ├── db/                 # Sessão do SQLAlchemy
│   │   ├── models/             # Entidades SQLAlchemy (User, OMR, Grade)
│   │   ├── repositories/       # Camada de repositório
│   │   ├── schemas/            # Schemas Pydantic
│   │   └── services/           # Regras de negócio, motor OMR (OpenCV) e gerador de PDF
│   └── tests/                  # Suíte de testes pytest
├── frontend/
│   ├── app/                    # Telas Next.js (App Router: auth, dashboard, omr)
│   ├── lib/                    # Cliente de API e utilitários
│   └── tests/                  # Testes do frontend (Vitest)
├── docker-compose.yml          # Orquestração de containers
├── Makefile                    # Atalhos para comandos do Podman/Docker
├── STATUS_ATUAL.md             # Status detalhado do desenvolvimento
└── README.md                   # Documentação principal
```

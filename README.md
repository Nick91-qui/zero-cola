# COLA-ZERO

Plataforma de avaliação online com banco de questões reutilizável, tentativas dinâmicas e monitoramento transparente de integridade.

---

# 1. Visão geral

O COLA-ZERO é uma plataforma educacional orientada por:

- banco de questões reutilizável
- provas compostas por questões reutilizadas
- execução de tentativa com uma questão por vez
- correção automática e manual
- auditoria de ações sensíveis
- conformidade com LGPD

Modelo central do sistema:

> Question Bank + Attempt Engine

A prova é uma configuração de entrega. A entidade principal do domínio é a questão.

---

# 2. Arquitetura

- Frontend: Next.js 16.2.x, React 19.2.x, TypeScript 5.9.x, TailwindCSS 4.3.x
- Backend: Python 3.12, FastAPI 0.137.x, SQLAlchemy 2.0.x, Alembic 1.18.x, Pydantic 2.13.x
- Banco de dados: PostgreSQL 16.14
- Infraestrutura: Docker e Docker Compose

Princípios principais:

- simplicidade
- segurança primeiro
- privacidade por padrão
- separação entre interface, regras de negócio e persistência

---

# 3. Funcionalidades do MVP

## Alunos

- autenticação
- acesso às provas atribuídas
- início de tentativas
- resposta de uma questão por vez
- visualização de resultados liberados

## Professores

- criação e gestão de questões
- criação e publicação de provas
- correção de respostas quando aplicável
- acesso a relatórios básicos de monitoramento

## Administradores

- gestão de usuários
- acesso a configurações da plataforma
- acesso a logs de auditoria

---

# 4. Fluxo da prova

1. aluno autentica
2. aluno inicia tentativa
3. frontend solicita a próxima questão
4. backend entrega apenas a questão atual
5. aluno envia resposta
6. backend persiste imediatamente
7. frontend solicita a próxima questão
8. tentativa é finalizada e corrigida conforme o tipo da questão

Regra central:

O frontend nunca deve receber a prova inteira de uma vez.

---

# 5. Segurança

## 5.1 Autenticação

- JWT access token
- JWT refresh token
- hash de senha com Argon2 preferencialmente
- bcrypt como alternativa aceitável

---

## 5.2 Autorização

- RBAC obrigatório
- perfis:
  - student
  - teacher
  - admin
- todo endpoint deve validar permissões

---

## 5.3 Auditoria

Ações sensíveis devem gerar logs, incluindo:

- login
- troca de senha
- criação de prova
- publicação de prova
- alteração de nota

---

# 6. Monitoramento

O sistema registra eventos relacionados à tentativa, como:

- visibilitychange
- blur
- focus
- fullscreen enter
- fullscreen exit

Esses eventos são usados para análise posterior e geração de relatórios.

COLA-ZERO não é um lockdown browser.

O sistema não deve afirmar que consegue:

- detectar uso de ChatGPT
- detectar outro dispositivo
- detectar telefones externos
- detectar capturas de tela de forma confiável
- impedir toda forma de cola

---

# 7. LGPD

O sistema segue princípios de:

- minimização de dados
- finalidade explícita
- transparência
- segurança
- retenção compatível com exigências legais e acadêmicas

Dados tratados no MVP:

- identificação de conta
- respostas de prova
- eventos relacionados à tentativa
- logs de auditoria

Capacidades necessárias:

- aviso de monitoramento
- exportação de dados do usuário
- anonimização quando legalmente permitida

---

# 8. Estrutura do projeto

```text
cola-zero/
├── backend/
├── frontend/
├── infra/
├── .env.example
└── README.md
```

---

# 9. Estado do MVP

## Status Atual (2026-07-01)

**Milestone 1: Fundação - 50% completo**

- ✅ Bloco 1 (Fundação Backend): COMPLETO
  - FastAPI, PostgreSQL, Alembic, Docker Compose
  - 7 testes de fundação passando
  
- ✅ Bloco 2 (Autenticação Backend + Frontend): COMPLETO
  - Backend: 5 endpoints auth, JWT tokens, bcrypt hashing, RBAC
  - Frontend: AuthContext, login/register pages, ProtectedRoute
  - 14 testes passando (7 auth-specific)
  
- ⏳ Bloco 3-6 (Question Bank, Exams, Attempts): EM PLANEJAMENTO

**Detalhes em**: [STATUS_ATUAL.md](./STATUS_ATUAL.md)

## O MVP será considerado concluído quando:

- usuários autenticam com segurança ✅ (em progresso)
- professores criam questões ⏳
- professores criam e publicam provas ⏳
- alunos realizam tentativas ⏳
- respostas são persistidas e corrigidas ⏳
- eventos de monitoramento são registrados ⏳
- relatórios básicos são gerados ⏳
- requisitos essenciais de LGPD são atendidos ⏳

---

# 10. Execução

Configuração inicial recomendada:

- backend com Python 3.12 para equilibrar compatibilidade ampla com dependências e suporte ativo
- frontend com Next.js 16.2.x, React 19.2.x e TypeScript 5.9.x para reduzir risco de incompatibilidades iniciais
- PostgreSQL 16.14 como linha estável e atualizada de banco
- TailwindCSS 4.3.x no frontend
- lint obrigatório desde o início
- Prettier obrigatório no frontend e nos arquivos compartilhados compatíveis

Estratégia de qualidade desde a base:

- aplicar TDD nos módulos críticos do MVP
- ciclo obrigatório: teste falha, implementação mínima, refatoração
- prioridades de TDD:
  - autenticação
  - autorização
  - entrega de questão
  - submissão de resposta
  - monitoramento
- lint e formatação devem rodar antes de merge

Os detalhes de execução devem ser definidos nos módulos de backend, frontend e infraestrutura conforme o repositório evoluir.

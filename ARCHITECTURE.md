# COLA-ZERO — Arquitetura do Sistema

---

# 1. Visão geral

O COLA-ZERO é uma plataforma de avaliação online orientada por:

> Question Bank + Attempt Engine

O banco de questões (Question Bank) é o repositório central de conteúdo. As provas (Exams) são configurações de entrega compostas por questões reutilizáveis. O histórico acadêmico é representado por tentativas (Attempts) e respostas (Answers).

Fluxo do domínio:
Question -> Exam -> Attempt -> Answer

Pilares arquiteturais:

- banco de questões reutilizável
- entrega de uma questão por vez
- persistência imediata de respostas
- monitoramento transparente de eventos
- segurança por padrão
- conformidade com LGPD

---

# 2. Componentes principais

## 2.1 Frontend

Responsabilidades:

- autenticação do usuário
- dashboard por perfil
- interface de tentativa
- exibição de uma questão por vez
- envio imediato de respostas
- captura de eventos suportados de monitoramento

Tecnologias:

- Next.js 16.2.x
- React 19.2.x
- TypeScript 5.9.x
- TailwindCSS 4.3.x

---

## 2.2 Backend

Responsabilidades:

- autenticação e autorização
- gestão de usuários
- banco de questões
- composição e publicação de provas
- motor de tentativas
- persistência de respostas
- correção automática e manual
- auditoria e eventos de monitoramento
- recursos de LGPD

Tecnologias:

- Python 3.12
- FastAPI 0.137.x
- SQLAlchemy 2.0.x
- Alembic 1.18.x
- Pydantic 2.13.x

---

## 2.3 Banco de dados

Banco relacional PostgreSQL com foco em rastreabilidade e histórico.

Entidades centrais:

- users
- questions
- exams
- exam_questions
- attempts
- answers
- security_events
- audit_logs

Regras:

- chaves primárias com UUID
- sem IDs incrementais
- preservação de histórico acadêmico
- preferência por soft delete ou arquivamento quando aplicável

---

# 3. Modelo de domínio

## 3.1 Banco de questões

Uma questão pode ser reutilizada em várias provas.

Relacionamento principal:

`Exam -> ExamQuestion -> Question`

A prova não deve conter cópias independentes do conteúdo da questão.

---

## 3.2 Motor de tentativas

A tentativa controla:

- início da prova
- ordem de entrega das questões
- tempo total
- submissão incremental de respostas
- finalização
- cálculo de score

A tentativa é a unidade operacional da execução da prova.

---

# 4. Fluxo da prova

## 4.1 Inicialização

1. aluno autentica
2. aluno inicia tentativa
3. backend cria a tentativa
4. frontend solicita a próxima questão

---

## 4.2 Execução

1. backend retorna apenas uma questão
2. frontend exibe a questão atual
3. aluno envia resposta
4. backend persiste imediatamente
5. frontend solicita a próxima questão

Regra obrigatória:

O frontend nunca deve receber todas as questões da prova em uma única resposta.

---

## 4.3 Finalização

1. tentativa é encerrada
2. backend consolida score
3. eventos e auditoria permanecem associados à tentativa
4. resultado pode ser liberado conforme regra pedagógica

---

# 5. Estratégia de backend

Princípios de implementação:

- rotas finas
- lógica de negócio concentrada em services
- uso de repositories quando útil para persistência
- dependency injection
- validação via schemas
- sem acesso direto ao banco dentro de controladores

---

# 6. Estratégia de frontend

Princípios de implementação:

- componentes reutilizáveis
- tipagem forte
- páginas pequenas e focadas
- lógica de negócio fora dos componentes visuais
- renderização segura para ambiente Next.js
- lint obrigatório
- Prettier obrigatório para consistência de formatação

---

# 7. Estratégia de qualidade

Princípios obrigatórios:

- TDD nas áreas críticas do MVP
- ciclo: teste falha, implementação mínima, refatoração
- teste de regressão para bug crítico corrigido
- lint deve bloquear desvios básicos de qualidade
- Prettier deve padronizar arquivos compatíveis do frontend e configurações relacionadas

Prioridades de TDD:

- autenticação
- autorização
- delivery de questão
- submissão de resposta
- monitoramento

---

# 8. Segurança

## 8.1 Camada de autenticação (IMPLEMENTADO ✅)

**Implementação Atual:**
- Access Token: JWT com 15 minutos de expiração
- Refresh Token: JWT com 7 dias de expiração
- Password hashing: bcrypt com salt
- Token storage (Frontend): sessionStorage (seguro, sem localStorage)
- Token validation: decorator `@get_current_user`
- RBAC: decorator `@require_role(*roles)`

**Arquivos:**
- Backend: `app/core/security.py`, `app/services/auth.py`
- Frontend: `app/context/AuthContext.tsx`, `app/hooks/useAuth.ts`
- Endpoints: POST `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, GET `/auth/me`

**Status:** ✅ 7 testes passando, pronto para produção

---

## 8.2 Camada de autorização (IMPLEMENTADO ✅)

- RBAC implementado com decorator `@require_role(UserRole.TEACHER, UserRole.ADMIN)`
- Perfis: `STUDENT`, `TEACHER`, `ADMIN`
- Validação em todos os endpoints auth
- User model com campo `role` e `is_active`

**Status:** ✅ Pronto, falta aplicação em endpoints de negócio (Question, Exam)

---

## 8.3 Auditoria (PLANEJADO ⏳)

Ações sensíveis devem gerar registros auditáveis (implementar em Bloco 3+):

- login ✅ (parcial: temos validação, falta logging)
- troca de senha ⏳
- criação de prova ⏳
- publicação de prova ⏳
- alteração de nota ⏳

---

# 9. Monitoramento e Eventos de Segurança (Security Events)

COLA-ZERO não é um lockdown browser.

Eventos suportados (armazenados em `security_events`):

- visibilitychange
- blur
- focus
- fullscreen enter
- fullscreen exit

Objetivo do monitoramento:

- detectar eventos de tela no frontend
- registrar eventos em `security_events` no backend
- gerar relatórios básicos de integridade

Lembrete de Segurança (Limitações assumidas):

O sistema NUNCA deve alegar ou prometer:

- Detecção de uso de ChatGPT
- Detecção de outros dispositivos
- Prevenção de capturas de tela
- Prevenção de todas as formas de cola

A plataforma apenas registra e reporta eventos observáveis do navegador.

---

# 10. LGPD

Requisitos mínimos da arquitetura:

- transparência sobre monitoramento
- minimização de dados
- exportação de dados do usuário
- anonimização quando legalmente permitida
- retenção compatível com requisitos acadêmicos e legais

Endpoints operacionais planejados para conformidade com a LGPD:
- `GET /me/data-export` (exportação de dados estruturados do usuário)
- `POST /me/request-anonymization` (solicitação de anonimização/exclusão sob conformidade jurídica)
- `GET /privacy-policy` (política de privacidade do sistema)
- `POST /consents/monitoring` (registro de consentimento transparente de monitoramento)

Dados fora de escopo de coleta:

- arquivos pessoais
- conteúdo do dispositivo
- histórico de navegação
- dados sem finalidade definida

---

# 11. Critério arquitetural de MVP — Status Atual (2026-07-01)

**Arquitetura Milestone 1 — 50% implementada**

| Requisito | Status | Notas |
|-----------|--------|-------|
| Autenticação segura | ✅ | JWT, bcrypt, RBAC completo |
| Banco de questões reutilizável | ⏳ | Planejado para Bloco 3 |
| Criação e publicação de provas | ⏳ | Planejado para Bloco 4 |
| Execução por tentativa | ⏳ | Planejado para Bloco 5 |
| Uma questão por vez | ⏳ | Será garantido no motor de entrega |
| Correção e score | ⏳ | Planejado para Bloco 6 |
| Monitoramento com transparência | ⏳ | Planejado para Bloco 7 |
| Requisitos essenciais de LGPD | ⏳ | Planejado para iteração final |

**Próximos passos arquiteturais:**
1. Bloco 3: Implementar tabelas Question, Exam, ExamQuestion
2. Bloco 4: Implementar CRUD e publicação de provas
3. Bloco 5: Implementar motor de tentativas e entrega de questão
4. Bloco 6: Implementar correção automática/manual
5. Bloco 7: Implementar security_events e relatórios
6. Final: Implementar LGPD endpoints completos
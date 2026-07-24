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
- questions (com suporte a versionamento e imutabilidade)
- exams
- exam_questions
- attempts
- answers
- security_events
- audit_logs
- omr_templates
- omr_scans
- grades (entidade de notas unificada)

Regras:

- chaves primárias com UUID
- sem IDs incrementais
- preservação de histórico acadêmico
- preferência por soft delete ou arquivamento quando aplicável

---

# 3. Modelo de domínio

## 3.1 Banco de questões e versionamento

Uma questão pode ser reutilizada em várias provas.

Relacionamento principal:
`Exam -> ExamQuestion -> Question`

A prova não deve conter cópias independentes do conteúdo da questão.

**Regras de Imutabilidade e Versionamento**:
- Questões publicadas no sistema são **estritamente imutáveis**.
- Qualquer edição em uma questão publicada gera um novo registro no banco de dados (um novo UUID/row), com `parent_id` apontando para o registro original e com o contador `version` incrementado. A versão anterior tem o campo `is_active` definido como `FALSE`.
- As tentativas online (`attempts`) e os modelos OMR (`omr_templates`) sempre travam e referenciam o ID da versão específica da questão no momento de sua criação ou publicação do exame. Isso garante que alterações posteriores na questão não alterem o conteúdo histórico das avaliações já aplicadas.

---

## 3.2 Motor de tentativas

A tentativa controla:

- início da prova
- ordem de entrega das questões
- tempo total
- submissão incremental de respostas
- finalização
- cálculo de score (que é então persistido na entidade unificada `Grade`)

A tentativa é a unidade operacional da execução da prova.

---

## 3.3 Entidade Unificada de Nota (Grade)

Todas as avaliações no COLA-ZERO resultam em notas consolidadas registradas na entidade única compartilhada `Grade` (tabela `grades`), independentemente da origem da correção (online ou gabaritos OMR físicos).

**Estrutura de dados**:
- `student_id`: Estudante avaliado.
- `source_type`: Origem da avaliação (ex: `ONLINE` para tentativas do Exam Engine ou `OMR` para correções do OMR Engine).
- `source_id`: Vínculo lógico (polimórfico) para `attempts.id` ou `omr_scans.id`.
- `score`: Nota final computada.
- `teacher_id`: Professor responsável pelo lançamento ou confirmação da nota.
- `created_at` / `updated_at`: Timestamps de auditoria.

**Extensibilidade**:
Novos módulos avaliativos futuros (ex: avaliações discursivas manuais, projetos práticos) devem reutilizar essa mesma entidade unificada para gravação de histórico acadêmico.

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
- Access Token: JWT com 15 minutos de expiração (armazenado em cookie seguro HttpOnly, SameSite=Lax)
- Refresh Token: JWT com 7 dias de expiração (armazenado em cookie seguro HttpOnly, SameSite=Strict)
- Password hashing: bcrypt com salt (consulte ADR-001)
- Token storage (Frontend): Cookies seguros HttpOnly (não armazenar em localStorage ou sessionStorage)
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

## 8.3 Auditoria (PENDENTE ⏳)

Ações sensíveis devem gerar registros auditáveis. O log de auditoria para ações de login (sucesso e falha) é obrigatório e está pendente de implementação. O fluxo de autenticação não será considerado pronto para produção até que o logging de auditoria exista.

Ações auditáveis planejadas:
- login ⏳ (pendente: autenticação funcional, mas logging de auditoria de login é obrigatório para produção)
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

# 11. Estabilização do Domínio Acadêmico Core (Core Academic Domain Freeze)

O domínio acadêmico core da plataforma COLA-ZERO está considerado estável e congelado (*frozen*). Qualquer alteração arquitetural ou redesenho dos seguintes componentes exige obrigatoriamente a criação e aprovação de um novo **Architectural Decision Record (ADR)**:
- **Ano Acadêmico (AcademicYear)**
- **Turmas (Classes)**
- **Códigos de Estudante (Student Codes)**
- **Controle de Acesso Baseado em Regras (RBAC)**
- **Arquitetura do Banco de Questões (Question Bank)**
- **Arquitetura do Motor de Tentativas (Attempt Engine)**

---

# 12. Critério arquitetural de MVP — Status Atual (2026-07-20)

**Arquitetura Milestone 1 — Fundação & Autenticação Concluídas (50%)**

**Priorização e Independência do OMR**:
- O **Online Assessment** (avaliação digital no navegador) permanece como o core da arquitetura de plataforma do COLA-ZERO.
- A decisão de implementar o módulo **COLA-ZERO OMR** como o próximo passo de desenvolvimento (Milestone 2) é uma decisão de **PRIORIDADE DE PRODUTO**, e não uma dependência arquitetural.
- O OMR foi projetado como um subsistema independente e desacoplado que pode ser removido ou alterado sem quebrar o core de tentativas online.

**Declaração de Congelamento da Arquitetura (Architecture Freeze)**:
A arquitetura do COLA-ZERO para o escopo do MVP está declarada como **congelada (frozen)**. Nenhuma nova funcionalidade ou alteração estrutural no modelo de dados, contratos de API ou fluxos poderá ser efetuada a partir deste momento, exceto para correção de bugs de implementação ou se formalizada por um novo Architectural Decision Record (ADR).

| Requisito | Status | Notas |
|-----------|--------|-------|
| Autenticação segura | ⏳ | JWT e RBAC implementados, mas pendente de logs de auditoria de login para prontidão de produção |
| Módulo OMR Independente | ⏳ | Próximo Milestone (Prioridade de Produto, 100% isolado) |
| Banco de questões reutilizável | ⏳ | Planejado pós-OMR |
| Criação e publicação de provas | ⏳ | Planejado pós-OMR |
| Execução por tentativa | ⏳ | Planejado pós-OMR |
| Uma questão por vez | ⏳ | Será garantido no motor de entrega digital |
| Entidade Unificada de Nota | ⏳ | Planejado implementar junto ao OMR |
| Monitoramento com transparência | ⏳ | Planejado pós-OMR |
| Requisitos essenciais de LGPD | ⏳ | Planejado para iteração final |

**Próximos passos arquiteturais:**
1. **Milestone OMR:** Implementar tabelas OMR, layouts em código, geração de PDF (ReportLab) com 5 dígitos de student_code, engine OpenCV e APIs de correção avulsa/integrada, além da entidade unificada `Grade`.
2. **Milestone Question Bank & Exams:** Implementar tabelas Question (com versionamento imutável), Exam, ExamQuestion e CRUD de gestão.
3. **Milestone Attempt Engine:** Implementar motor de tentativas online (uma questão por vez e autosave).
4. **Milestone Monitoramento & Auditoria:** Implementar logs de auditoria de negócio e tabela `security_events`.
5. **Milestone LGPD:** Implementar consentimento explícito e endpoints de exportação/anonimização.

---

# 13. Architectural Decision Records (ADRs)

## ADR-001: Algoritmo de Hashing de Senhas (bcrypt)

### Contexto
O padrão de segurança de longo prazo definido para a plataforma COLA-ZERO é o **Argon2**, devido à sua robustez superior contra ataques de força bruta otimizados por hardware (GPU/ASIC) e canais laterais. No entanto, por razões de simplicidade no setup inicial e compatibilidade de dependências no ambiente Docker atual do MVP, a implementação atual foi construída utilizando **bcrypt** (com salt e fator de trabalho padrão).

### Decisão
Manter o uso do **bcrypt** na implementação atual da Milestone 1. Não há necessidade de alterações imediatas de código no backend. O uso do **Argon2** permanece registrado como a recomendação técnica de longo prazo e a migração de algoritmo de hash de senha está planejada para uma versão futura de hardening pré-produção.

### Status
- **Implementação Atual (Current):** bcrypt com salt.
- **Recomendação Futura (Future):** Argon2 (migração planejada pós-MVP).
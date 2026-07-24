Este documento define a ordem de desenvolvimento do COLA-ZERO com foco em MVP, segurança por padrão, privacidade e arquitetura centrada em Question Bank + Attempt Engine.

**Nota sobre Priorização e Arquitetura**:
- A **avaliação online (Online Assessment)** continua sendo a arquitetura de plataforma primária do COLA-ZERO.
- A decisão de implementar o módulo **COLA-ZERO OMR** (Fases 2 a 4) antes do fluxo completo de tentativas digitais é uma decisão de **PRIORIDADE DE PRODUTO** e não uma dependência ou limitação arquitetural. O OMR é um subsistema independente e desacoplado que pode ser adicionado ou removido sem influenciar o core do motor online.

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

# Fase 1 — Autenticação e RBAC (Backend & Frontend)

## Objetivo
Estabelecer a identidade e o controle de acesso baseado em regras (RBAC) com segurança avançada, sem armazenamento vulnerável no cliente.

## Entregas
- Modelo `User` com UUID.
- Hash de senha com bcrypt temporariamente (ADR-001); Argon2 planejado para o futuro.
- Geração de tokens JWT gerenciados por cookies:
  - Access Token: expiração de 15 minutos, armazenado em cookie seguro HttpOnly (`Secure`, `SameSite=Lax`).
  - Refresh Token: expiração de 7 dias, armazenado em cookie seguro HttpOnly (`Secure`, `SameSite=Strict`).
  - **Proibido:** Uso de `localStorage` ou `sessionStorage` para guardar tokens JWT no frontend.
- Controle de acesso baseado em regras (RBAC) com perfis `STUDENT`, `TEACHER` e `ADMIN`.
- Endpoints: `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me`.
- **Restrição de Produção:** Logs de auditoria de login (sucesso/falha) estão marcados como obrigatórios pendentes antes da homologação final em produção.

---

# Fase 2 — Módulo OMR (MVP) — Banco de Dados e Layouts em Código

## Objetivo
Estruturar o armazenamento e a definição geométrica do módulo de correção de gabaritos impressos de forma independente.

## Entregas
- Criação das tabelas de OMR (`omr_templates` e `omr_scans`) com UUID.
- Criação da tabela de notas unificada (`grades`), responsável por unificar o histórico de notas de qualquer fonte de avaliação (ONLINE ou OMR).
- Definição do relacionamento com `exams` como opcional (permitindo Modo Avulso e Modo Integrado).
- Implementação do sistema de layouts versionados mantidos diretamente no código-fonte (`app/core/omr_layouts.py`). O banco apenas salvará a string referencial no campo `layout_version`.
- Migrações do banco via Alembic.

---

# Fase 3 — Módulo OMR (MVP) — Geração de PDF e OpenCV Engine

## Objetivo
Desenvolver a geração de folhas de respostas preenchidas e a inteligência de processamento de imagem por OMR.

## Entregas
- Geração de gabarito em PDF (com **ReportLab**) contendo 4 âncoras nos cantos para alinhamento e o identificador de 5 dígitos do estudante (`student_code`) pré-preenchido (sombreado) no próprio PDF.
- Algoritmo de visão computacional em OpenCV + NumPy para:
  - Alinhamento de perspectiva de imagem (deskew & warp) através de contornos das âncoras.
  - Leitura do código do aluno (5 colunas $\times$ 10 linhas).
  - Detecção de bolhas de respostas das questões baseado em densidade relativa de cor (calibração dinâmica usando densidades das âncoras pretas e fundo branco).

---

# Fase 4 — Módulo OMR (MVP) — Upload API, Correção Automática e Revisão UI

## Objetivo
Unificar o backend e frontend OMR, permitindo upload, processamento assíncrono em background, correção e revisão visual das notas.

## Entregas
- Endpoint `POST /api/v1/omr/scans/upload` aceitando exclusivamente uploads de **imagens individuais (JPG, JPEG, PNG)**.
- Lógica de processamento assíncrona em background para execução da leitura e cálculo automático da nota.
- Tela no frontend para upload das imagens.
- Interface de revisão visual para o professor com overlay colorido (Verde/Vermelho) em cima das bolhas detectadas e suporte a ajustes manuais de leitura de bolhas ou código do estudante.
- Confirmação final das notas e gravação na tabela unificada `grades`.

---

# Fase 5 — Modelagem Completa de Domínio Acadêmico Core e Migrações

## Objetivo
Modelar, criar e estabilizar o schema do banco de dados relacional e migrações para o fluxo online.
*Nota: O domínio acadêmico core (AcademicYear, Classes, Student Codes, RBAC, Question Bank, Attempt Engine) é considerado congelado e alterações exigem ADR.*

## Entregas
- Criação de tabelas e modelos SQLAlchemy com UUID:
  - `classes`, `class_students`, `questions` (com suporte a imutabilidade por versão e parent_id), `exams`, `exam_questions`, `attempts`, `answers`, `security_events`, `audit_logs`
- Aplicação de migrações com Alembic.

---

# Fase 6 — Banco de Questões (Question Bank) e Provas (Exam Engine)

## Objetivo
Construir o gerenciamento de conteúdo e provas do sistema de forma reutilizável.

## Entregas
- CRUD de questões e filtros (disciplina, dificuldade, tags) no backend e frontend.
- CRUD e regras de publicação de provas (Exam composto por ExamQuestion).

---

# Fase 7 — Motor de Tentativas Online (Attempt Engine)

## Objetivo
Implementar o fluxo operacional e dinâmico de realização de provas online pelos alunos.

## Entregas
- Ciclo de vida da tentativa (`Attempt`), incluindo ordem de tentativas e autosave de respostas (`Answer`).
- Endpoint de entrega de **uma questão por vez** e envio sequencial de respostas no frontend.
- Consolidação de notas e scores automáticos.

---

# Fase 8 — Eventos de Segurança (Security Events) e Auditoria de Sistema

## Objetivo
Capturar eventos do navegador relacionados ao comportamento da tela da tentativa online e auditar ações sensíveis de negócio.

## Entregas
- Captura de eventos do navegador (`visibilitychange`, `blur`, `focus`, `fullscreen_enter`, `fullscreen_exit`) salvos na tabela `security_events`.
- Ingestão de logs de auditoria imutáveis no backend para ações administrativas, pedagógicas e eventos sensíveis (troca de senha, criação/publicação de prova, alteração de notas).

---

# Fase 9 — Recursos de LGPD

## Objetivo
Disponibilizar governança, consentimento explícito e direitos de privacidade dos usuários.

## Entregas
- Aviso claro e consentimento de monitoramento registrado em banco (`POST /consents/monitoring`).
- Endpoints de exportação estruturada (`GET /me/data-export`) e solicitação de anonimização (`POST /me/request-anonymization`).
- Endpoint de política de privacidade (`GET /privacy-policy`).

---

# Fase 10 — Qualidade, Hardening, Auditoria de Login e Testes E2E

## Objetivo
Reforçar a robustez técnica, auditoria completa de autenticação e validação ponta a ponta da plataforma.

## Entregas
- Implementação de logs de auditoria de login (sucesso/falha) obrigatórios antes da entrega de produção.
- Testes automatizados de integração e cobertura dos fluxos críticos online e offline (OMR).
- Rate limiting de endpoints e sanitização de dados.

---

# Critério de conclusão do MVP

O MVP é considerado concluído quando:
- Usuários autenticam com segurança usando cookies HttpOnly (Lax/Strict) e logs de auditoria de login estão ativos.
- Módulo OMR independente de correção offline de imagens de gabaritos funciona (standalone e integrado).
- Professores gerenciam o Question Bank e criam/publicam provas válidas.
- Alunos realizam tentativas online sequenciais (uma questão por vez) com autosave.
- Eventos de segurança (security_events) e auditoria de ações sensíveis são persistidos.
- Recursos operacionais de conformidade com a LGPD estão disponíveis.

---

# Fora do escopo imediato

- Geração assistida por IA de questões.
- Análise estatística de itens e calibração de dificuldade.
- Processamento em lote de PDFs multipágina (OMR).
- Integração com Safe Exam Browser.
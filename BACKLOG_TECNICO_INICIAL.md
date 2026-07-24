# COLA-ZERO — Backlog Técnico Inicial

## 1. Objetivo

Este backlog traduz os documentos de produto, arquitetura, roadmap e banco de dados em itens técnicos iniciais para execução do MVP.

Princípios obrigatórios:

- foco em `Question Bank + Attempt Engine`
- segurança por padrão
- privacidade por padrão
- uma questão por vez
- auditoria e rastreabilidade
- conformidade com LGPD desde o início

## 2. Convenções de priorização

- `P0`: bloqueia o início do MVP
- `P1`: necessário para o MVP funcional
- `P2`: importante para operação inicial
- `P3`: melhoria posterior

Status inicial de todos os itens:

- `todo`

## 3. Épico A — Fundação do repositório

### CZ-A01 — Estruturar backend FastAPI
- Prioridade: `P0`
- Status: `done`
- Dependências: nenhuma
- Entregas:
  - criar estrutura `backend/app`
  - configurar `main.py`
  - configurar módulos `core`, `db`, `models`, `schemas`, `api`, `services`, `utils`
- Critérios de aceite:
  - aplicação sobe localmente
  - rota de healthcheck responde com sucesso

### CZ-A02 — Estruturar frontend Next.js
- Prioridade: `P0`
- Status: `done`
- Dependências: nenhuma
- Entregas:
  - criar estrutura `frontend/app`
  - configurar layout base
  - criar rota inicial de login
- Critérios de aceite:
  - aplicação sobe localmente
  - página inicial renderiza sem erro

### CZ-A03 — Configurar Docker e Docker Compose
- Prioridade: `P0`
- Status: `done`
- Dependências: CZ-A01, CZ-A02
- Entregas:
  - `backend/Dockerfile`
  - `frontend/Dockerfile`
  - `infra/docker-compose.yml`
- Critérios de aceite:
  - backend, frontend e PostgreSQL sobem juntos

### CZ-A04 — Definir variáveis de ambiente
- Prioridade: `P0`
- Status: `done`
- Dependências: CZ-A01, CZ-A02, CZ-A03
- Entregas:
  - criar `.env.example`
  - documentar variáveis mínimas de backend e frontend
- Critérios de aceite:
  - projeto pode ser iniciado a partir de `.env.example`

### CZ-A05 — Configurar observabilidade mínima
- Prioridade: `P2`
- Status: `done`
- Dependências: CZ-A01
- Entregas:
  - logging estruturado básico no backend
  - logs mínimos de erro e inicialização
- Critérios de aceite:
  - erros principais aparecem de forma rastreável nos logs

## 4. Épico B — Banco de dados e persistência

### CZ-B01 — Configurar SQLAlchemy, sessão e base declarativa
- Prioridade: `P0`
- Status: `done`
- Dependências: CZ-A01
- Entregas:
  - configuração de conexão PostgreSQL
  - sessão do banco
  - base dos modelos
- Critérios de aceite:
  - backend conecta no banco com sucesso

### CZ-B02 — Configurar Alembic
- Prioridade: `P0`
- Status: `done`
- Dependências: CZ-B01
- Entregas:
  - configuração de migrações
  - primeira migration funcional
- Critérios de aceite:
  - migration sobe e desce com sucesso

### CZ-B03 — Implementar modelo `users`
- Prioridade: `P0`
- Status: `done`
- Dependências: CZ-B02
- Entregas:
  - model SQLAlchemy
  - constraints de email único
  - timestamps
- Critérios de aceite:
  - tabela criada com UUID e campos obrigatórios

### CZ-B04 — Implementar modelos centrais do domínio
- Prioridade: `P0`
- Status: `todo`
- Dependências: CZ-B02
- Entregas:
  - `questions`
  - `classes`
  - `class_students`
  - `exams`
  - `exam_questions`
  - `attempts`
  - `answers`
  - `security_events`
  - `audit_logs`
- Critérios de aceite:
  - relacionamentos principais funcionam
  - schema reflete `DATABASE.MD`

### CZ-B05 — Criar índices iniciais do MVP
- Prioridade: `P1`
- Status: `todo`
- Dependências: CZ-B04
- Entregas:
  - índices para email, questões, provas, tentativas, respostas, eventos e auditoria
- Critérios de aceite:
  - migration inclui índices recomendados

## 5. Épico C — Segurança e identidade

### CZ-C01 — Implementar hash de senha
- Prioridade: `P0`
- Status: `done`
- Dependências: CZ-B03
- Entregas:
  - utilitário com Argon2 preferencialmente
  - alternativa segura se necessário
- Critérios de aceite:
  - senhas nunca são armazenadas em texto puro

### CZ-C02 — Implementar autenticação JWT
- Prioridade: `P0`
- Status: `done`
- Dependências: CZ-C01
- Entregas:
  - access token
  - refresh token
  - expiração configurável
- Critérios de aceite:
  - login retorna tokens válidos
  - refresh emite novo access token

### CZ-C03 — Implementar rotas de autenticação
- Prioridade: `P0`
- Status: `done`
- Dependências: CZ-C02
- Entregas:
  - `POST /auth/login`
  - `POST /auth/refresh`
  - `POST /auth/logout`
- Critérios de aceite:
  - fluxos principais autenticam e renovam sessão

### CZ-C04 — Implementar RBAC
- Prioridade: `P0`
- Status: `done`
- Dependências: CZ-C03
- Entregas:
  - perfis `student`, `teacher`, `admin`
  - dependências de autorização por endpoint
- Critérios de aceite:
  - acesso indevido retorna erro de permissão

### CZ-C05 — Implementar auditoria de ações sensíveis
- Prioridade: `P1`
- Status: `todo`
- Dependências: CZ-B04, CZ-C03
- Entregas:
  - log de login
  - log de troca de senha
  - log de criação/publicação de prova
  - log de alteração de nota
- Critérios de aceite:
  - ações sensíveis persistem em `audit_logs`

## 6. Épico D — Frontend de autenticação e shell da aplicação

### CZ-D01 — Criar página de login
- Prioridade: `P0`
- Status: `done`
- Dependências: CZ-A02, CZ-C03
- Entregas:
  - formulário de login
  - tratamento de erro básico
- Critérios de aceite:
  - usuário consegue autenticar pela interface

### CZ-D02 — Persistir sessão no frontend
- Prioridade: `P0`
- Status: `done`
- Dependências: CZ-D01
- Entregas:
  - armazenamento seguro de sessão compatível com a estratégia escolhida
  - renovação de sessão
- Critérios de aceite:
  - usuário autenticado permanece logado conforme política definida

### CZ-D03 — Proteger rotas por perfil
- Prioridade: `P1`
- Status: `done`
- Dependências: CZ-D02, CZ-C04
- Entregas:
  - proteção de páginas de aluno, professor e admin
- Critérios de aceite:
  - acesso indevido é redirecionado ou bloqueado

### CZ-D04 — Criar layout base e dashboard inicial por perfil
- Prioridade: `P1`
- Status: `done`
- Dependências: CZ-D03
- Entregas:
  - layout principal
  - navegação mínima
  - dashboard inicial
- Critérios de aceite:
  - perfis acessam sua área inicial

## 7. Épico E — Banco de questões

### CZ-E01 — Implementar modelo e schema de `Question`
- Prioridade: `P0`
- Status: `todo`
- Dependências: CZ-B04
- Entregas:
  - model
  - schema de criação, leitura e atualização
- Critérios de aceite:
  - payloads válidos persistem corretamente

### CZ-E02 — Implementar CRUD de questões no backend
- Prioridade: `P1`
- Status: `todo`
- Dependências: CZ-E01, CZ-C04
- Entregas:
  - `POST /questions`
  - `GET /questions`
  - `GET /questions/{id}`
  - `PATCH /questions/{id}`
- Critérios de aceite:
  - professor gerencia questões com autorização correta

### CZ-E03 — Implementar filtros de questões
- Prioridade: `P1`
- Status: `todo`
- Dependências: CZ-E02
- Entregas:
  - filtros por disciplina
  - filtros por dificuldade
  - filtros por tags
- Critérios de aceite:
  - listagem responde aos filtros combinados

### CZ-E04 — Criar interface de gestão de questões no frontend
- Prioridade: `P1`
- Status: `todo`
- Dependências: CZ-E02, CZ-E03
- Entregas:
  - formulário de criação e edição
  - listagem e busca
- Critérios de aceite:
  - professor cria e consulta questões pela interface

## 8. Épico F — Provas

### CZ-F01 — Implementar modelo e schema de `Exam`
- Prioridade: `P0`
- Status: `todo`
- Dependências: CZ-B04
- Entregas:
  - model
  - schema de criação e leitura
- Critérios de aceite:
  - prova pode ser criada em estado `draft`

### CZ-F02 — Implementar vínculo `ExamQuestion`
- Prioridade: `P0`
- Status: `todo`
- Dependências: CZ-F01, CZ-E01
- Entregas:
  - associação entre prova e questão
  - ordenação e peso
- Critérios de aceite:
  - prova reutiliza questões sem duplicar conteúdo

### CZ-F03 — Implementar rotas de prova no backend
- Prioridade: `P1`
- Status: `todo`
- Dependências: CZ-F02, CZ-C04
- Entregas:
  - `POST /exams`
  - `GET /exams`
  - `GET /exams/{id}`
  - `POST /exams/{id}/questions`
  - `POST /exams/{id}/publish`
- Critérios de aceite:
  - professor cria, compõe e publica provas

### CZ-F04 — Criar interface de criação e publicação de provas
- Prioridade: `P1`
- Status: `todo`
- Dependências: CZ-F03, CZ-E04
- Entregas:
  - formulário de prova
  - seleção de questões
  - publicação
- Critérios de aceite:
  - professor monta prova a partir do banco de questões

## 9. Épico G — Attempt Engine

### CZ-G01 — Implementar lifecycle de tentativa
- Prioridade: `P0`
- Status: `todo`
- Dependências: CZ-B04, CZ-F03
- Entregas:
  - criação de tentativa
  - mudança de status
  - encerramento
- Critérios de aceite:
  - tentativa evolui entre estados previstos

### CZ-G02 — Implementar endpoint de próxima questão
- Prioridade: `P0`
- Status: `todo`
- Dependências: CZ-G01
- Entregas:
  - `GET /attempts/{id}/next-question`
- Critérios de aceite:
  - backend retorna apenas a questão atual
  - frontend nunca recebe a prova inteira

### CZ-G03 — Implementar submissão imediata de resposta
- Prioridade: `P0`
- Status: `todo`
- Dependências: CZ-G01
- Entregas:
  - `POST /attempts/{id}/answers`
  - persistência imediata em `answers`
- Critérios de aceite:
  - resposta fica registrada logo após envio

### CZ-G04 — Implementar finalização de tentativa
- Prioridade: `P1`
- Status: `todo`
- Dependências: CZ-G02, CZ-G03
- Entregas:
  - `POST /attempts/{id}/submit`
  - consolidação do estado final
- Critérios de aceite:
  - tentativa finalizada não aceita fluxo inválido

### CZ-G05 — Criar tela de tentativa no frontend
- Prioridade: `P1`
- Status: `todo`
- Dependências: CZ-G02, CZ-G03
- Entregas:
  - exibição da questão atual
  - envio da resposta
  - solicitação da próxima questão
- Critérios de aceite:
  - aluno realiza prova pela interface em fluxo sequencial

### CZ-G06 — Implementar temporizador da tentativa
- Prioridade: `P2`
- Status: `todo`
- Dependências: CZ-G05
- Entregas:
  - timer visual
  - sincronização mínima com backend
- Critérios de aceite:
  - tempo restante é exibido corretamente

## 10. Épico H — Correção e resultados

### CZ-H01 — Implementar correção automática de questões objetivas
- Prioridade: `P1`
- Status: `todo`
- Dependências: CZ-G03, CZ-E01
- Entregas:
  - serviço de correção automática
  - marcação de `is_correct`
- Critérios de aceite:
  - respostas objetivas são avaliadas corretamente

### CZ-H02 — Consolidar score da tentativa
- Prioridade: `P1`
- Status: `todo`
- Dependências: CZ-H01, CZ-G04
- Entregas:
  - cálculo de score total
  - persistência em `attempts.score`
- Critérios de aceite:
  - score final corresponde aos pesos da prova

### CZ-H03 — Criar visualização de resultado para aluno
- Prioridade: `P2`
- Status: `todo`
- Dependências: CZ-H02
- Entregas:
  - página de resultado liberado
- Critérios de aceite:
  - aluno visualiza score quando permitido

### CZ-H04 — Criar painel básico de correção para professor
- Prioridade: `P2`
- Status: `todo`
- Dependências: CZ-H02
- Entregas:
  - listagem de tentativas
  - revisão básica de respostas
- Critérios de aceite:
  - professor visualiza tentativas e resultados

## 11. Épico I — Monitoramento

### CZ-I01 — Implementar captura de eventos suportados no frontend
- Prioridade: `P1`
- Status: `todo`
- Dependências: CZ-G05
- Entregas:
  - hook `useMonitoring`
  - captura de `visibilitychange`, `blur`, `focus`, `fullscreen_enter`, `fullscreen_exit`
- Critérios de aceite:
  - eventos são capturados apenas no contexto da tentativa

### CZ-I02 — Implementar ingestão de eventos no backend
- Prioridade: `P1`
- Status: `todo`
- Dependências: CZ-B04, CZ-I01
- Entregas:
  - `POST /attempts/{id}/security-events`
  - persistência em `security_events`
- Critérios de aceite:
  - eventos válidos são registrados com `attempt_id`

### CZ-I03 — Criar relatório básico de monitoramento para professor
- Prioridade: `P2`
- Status: `todo`
- Dependências: CZ-I02
- Entregas:
  - listagem de eventos por tentativa
  - resumo básico por prova
- Critérios de aceite:
  - professor consegue visualizar eventos registrados

### CZ-I04 — Exibir aviso de monitoramento ao usuário
- Prioridade: `P1`
- Status: `todo`
- Dependências: CZ-G05
- Entregas:
  - componente de transparência antes e durante a tentativa
- Critérios de aceite:
  - usuário é informado sobre o monitoramento

## 12. Épico J — LGPD

### CZ-J01 — Implementar exportação de dados do usuário
- Prioridade: `P1`
- Status: `todo`
- Dependências: CZ-B04, CZ-C03
- Entregas:
  - `GET /me/data-export`
- Critérios de aceite:
  - usuário obtém seus dados essenciais em formato estruturado

### CZ-J02 — Implementar solicitação de anonimização
- Prioridade: `P2`
- Status: `todo`
- Dependências: CZ-J01
- Entregas:
  - `POST /me/request-anonymization`
  - fluxo inicial de tratamento
- Critérios de aceite:
  - solicitação fica registrada para processamento conforme regra legal

### CZ-J03 — Definir política técnica de retenção
- Prioridade: `P2`
- Status: `todo`
- Dependências: CZ-B04
- Entregas:
  - regras técnicas para retenção de logs, respostas e registros acadêmicos
- Critérios de aceite:
  - política mínima documentada e aplicável ao sistema

### CZ-J04 — Implementar página/endpoint de política de privacidade
- Prioridade: `P1`
- Status: `todo`
- Dependências: CZ-A01
- Entregas:
  - `GET /privacy-policy`
- Critérios de aceite:
  - política de privacidade exibida de forma clara

### CZ-J05 — Implementar registro de consentimento de monitoramento
- Prioridade: `P1`
- Status: `todo`
- Dependências: CZ-B04
- Entregas:
  - `POST /consents/monitoring`
- Critérios de aceite:
  - registro do consentimento do aluno persistido no banco

## 13. Épico K — Qualidade

### CZ-K01 — Implementar testes de autenticação
- Prioridade: `P0`
- Status: `done`
- Dependências: CZ-C03
- Critérios de aceite:
  - login e refresh cobertos por testes automatizados

### CZ-K02 — Implementar testes de autorização
- Prioridade: `P0`
- Status: `done`
- Dependências: CZ-C04
- Critérios de aceite:
  - cenários de permissão e negação cobertos

### CZ-K03 — Implementar testes de entrega da prova
- Prioridade: `P1`
- Status: `todo`
- Dependências: CZ-G02
- Critérios de aceite:
  - teste garante entrega de uma questão por vez

### CZ-K04 — Implementar testes de submissão de resposta
- Prioridade: `P1`
- Status: `todo`
- Dependências: CZ-G03
- Critérios de aceite:
  - teste garante persistência imediata da resposta

### CZ-K05 — Implementar testes de correção
- Prioridade: `P1`
- Status: `todo`
- Dependências: CZ-H01, CZ-H02
- Critérios de aceite:
  - score e correção automática cobertos

### CZ-K06 — Implementar testes de monitoramento
- Prioridade: `P1`
- Status: `todo`
- Dependências: CZ-I02
- Critérios de aceite:
  - ingestão de eventos suportados coberta por testes

## 13.1 Épico L — Módulo OMR

### CZ-L01 — Modelar e criar tabelas de OMR e Notas no banco
- Prioridade: `P0`
- Status: `todo`
- Dependências: CZ-B02
- Entregas:
  - Tabelas `omr_templates`, `omr_scans` e a tabela unificada `grades`
- Critérios de aceite:
  - Schema criado e migrado com sucesso via Alembic
  - `exam_id` é chave estrangeira opcional (nullable) para habilitar modo standalone em `omr_templates`
  - Tabela `grades` criada para armazenar notas unificadas (OMR e ONLINE)

### CZ-L02 — Estruturar layouts versionados em código
- Prioridade: `P0`
- Status: `todo`
- Dependências: nenhuma
- Entregas:
  - Arquivo `backend/app/core/omr_layouts.py` para mapear coordenadas
- Critérios de aceite:
  - Posições geométricas mantidas em código e referenciadas via layout_version string

### CZ-L03 — Implementar gerador de gabarito em PDF
- Prioridade: `P0`
- Status: `todo`
- Dependências: CZ-L02
- Entregas:
  - PDF gerado com ReportLab contendo 4 âncoras e student_code de 5 dígitos preenchido
- Critérios de aceite:
  - Geração de PDF funciona e gera círculos pretos sombreados da matrícula de forma automática

### CZ-L04 — Implementar OpenCV Perspective Correction
- Prioridade: `P1`
- Status: `todo`
- Dependências: CZ-L02
- Entregas:
  - Algoritmo de correção de perspectiva baseado em âncoras
- Critérios de aceite:
  - OpenCV consegue alinhar folhas de respostas JPG/PNG a uma grade padrão

### CZ-L05 — Implementar OMR Bubble & Student Code Detection
- Prioridade: `P1`
- Status: `todo`
- Dependências: CZ-L04
- Entregas:
  - Detetor de densidade relativa de marcação nas bolhas do student_code (5 dígitos) e das questões
- Critérios de aceite:
  - Sistema lê matrícula e respostas com calibração adaptativa e trata casos de dupla marcação

### CZ-L06 — Criar API de upload de scan e processamento em background
- Prioridade: `P1`
- Status: `todo`
- Dependências: CZ-L05, CZ-L01
- Entregas:
  - Endpoint `POST /api/v1/omr/scans/upload` aceitando apenas um arquivo de imagem (JPG/PNG)
  - Processamento assíncrono em background e correção automática
  - Cálculo de notas e gravação na tabela unificada `grades` após confirmação do professor
- Critérios de aceite:
  - Upload processado em segundo plano, resultados salvos no banco, e nota gravada na tabela unificada `grades` após confirmação/revisão.

### CZ-L07 — Criar interface frontend de upload e revisão visual
- Prioridade: `P1`
- Status: `todo`
- Dependências: CZ-L06
- Entregas:
  - Tela de upload de imagens e interface de revisão
- Critérios de aceite:
  - Professor consegue visualizar overlays coloridos em cima das bolhas detectadas e corrigir marcações manualmente

---

## 14. Ordem prática recomendada de execução

1. **Milestone 1 — Fundação & Autenticação (CONCLUÍDO)**
   - CZ-A01, CZ-B01, CZ-B02, CZ-B03 (Fundação & Users)
   - CZ-C01, CZ-C02, CZ-C03, CZ-C04 (Auth & RBAC Backend)
   - CZ-A02, CZ-D01, CZ-D02, CZ-D03, CZ-D04 (Auth Frontend)
   - CZ-A03, CZ-A04, CZ-A05 (Docker/Env/Logs)
   - CZ-K01, CZ-K02 (Testes de Auth & RBAC)

2. **Milestone 2 — COLA-ZERO OMR (MVP) (ALTA PRIORIDADE)**
   - CZ-L01 (Modelagem & Tabelas OMR)
   - CZ-L02 (Registro de Layouts em Código)
   - CZ-L03 (Gerador de PDF OMR)
   - CZ-L04 (OpenCV Perspective Alignment)
   - CZ-L05 (OMR Bubble & Student Code Detection)
   - CZ-L06 (API Upload & Background Grading)
   - CZ-L07 (Interface de Upload & Revisão Visual)

3. **Milestone 3 — Core Domain & Provas Online (POSTERGADO)**
   - CZ-B04 (Tabelas de Questões, Provas, Tentativas, Respostas)
   - CZ-B05 (Índices de Domínio)
   - CZ-E01, CZ-E02, CZ-E03, CZ-E04 (Question Bank Backend/Frontend)
   - CZ-F01, CZ-F02, CZ-F03, CZ-F04 (Exam Engine)
   - CZ-G01, CZ-G02, CZ-G03, CZ-G04, CZ-G05, CZ-G06 (Attempt Engine)
   - CZ-H01, CZ-H02, CZ-H03, CZ-H04 (Correção automática/manual online)
   - CZ-I01, CZ-I02, CZ-I03, CZ-I04 (Monitoramento de tela online)
   - CZ-J01, CZ-J02, CZ-J03, CZ-J04, CZ-J05 (Recursos de LGPD)
   - CZ-K03, CZ-K04, CZ-K05, CZ-K06 (Testes de Prova/Correção/Monitoramento)

---

## 15. Recorte da Primeira Milestone (CONCLUÍDO)

Milestone 1 entregou:
- Fundação técnica dockerizada de backend e frontend.
- Persistência básica e migrations de banco.
- Autenticação e sessão com tokens JWT salvos em cookies seguros HttpOnly.
- Middleware e decorator de autorização (RBAC).

---

## 16. Recorte da Segunda Milestone (PRÓXIMA)

Milestone 2 focará inteiramente no módulo **COLA-ZERO OMR**:
- Definições de layouts OMR geométricos versionados em código.
- Geração de PDF (ReportLab) com folha de respostas e matrícula de 5 dígitos (`student_code`) pré-preenchida.
- OpenCV Engine para deskew e detecção de marcações de bolhas em imagens JPG/PNG individuais.
- API e UI de upload e revisão/correção manual de notas para o professor.

---

## 17. Recorte da Terceira Milestone (POSTERGADA)

Milestone 3 completará o motor online:
- Question Bank, Exam Engine, Attempt Engine dinâmico (uma questão por vez), monitoramento de integridade online e governança base de privacidade (LGPD).
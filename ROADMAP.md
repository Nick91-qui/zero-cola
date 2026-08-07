# COLA-ZERO — Roadmap do Projeto

> **Single Source of Truth** para as fases futuras de desenvolvimento, prioridades, dependências e critérios de aceitação (Definition of Done).

---

## 1. Visão Geral de Prioridades

O desenvolvimento do COLA-ZERO segue uma estratégia incremental orientada a entregas funcionais de alto impacto educacional.

| Fase | Descrição | Status | Prioridade |
|------|-----------|--------|------------|
| **Fase 1** | Autenticação, RBAC & Fundação | ✅ Concluído e validado | P0 |
| **Fase 2** | Módulo OMR Standalone & Integrado (Backend & UI OMR) | ✅ Concluído e validado | P0 |
| **Fase 3** | Backend do Assessment Core & Banco de Questões | ✅ Concluído e validado | P0 |
| **Fase 4** | Modelo Acadêmico de Turmas, Matrículas e Atribuições | ✅ Concluído e validado | P0 |
| **Fase 5** | Interface Frontend para Provas Online (`/exams` + `/attempts/[id]`) | ✅ Concluído e validado | P1 |
| **Fase 6** | Interface Frontend para Analytics & Dashboard (`/dashboard`) | ✅ Concluído no baseline atual | P1 |
| **Fase 7** | Hardening de Segurança, Auditoria & LGPD | ✅ Concluído e validado | P2 |
| **Fase 8** | Produção e Visualização de Provas (`Question Bank` → `Exam Builder` → `OMR personalizado`) | 🛠️ Em implementação | P2 |
| **Fase 9** | Processamento OMR em Lote (PDF multipágina) & Escala | ⏳ Futuro | P3 |

---

## 2. Fases Futuras de Desenvolvimento

### Fase 4 — Modelo Acadêmico de Turmas, Matrículas e Atribuições
- **Status**: concluído no backend e validado com testes e PostgreSQL de desenvolvimento.
- **Objetivo**: estabelecer turmas concretas por período letivo, vínculo explícito entre professores e turmas, histórico de matrícula dos alunos e atribuição multi-turma de exames.
- **Entregas**:
  - `Class` como instância concreta de turma por período.
  - Associação `teacher_classes` para acesso de professores a múltiplas turmas.
  - Associação `class_students` com histórico de matrícula e regra de uma matrícula ativa por período.
  - Associação `exam_classes` para permitir que um mesmo exame seja atribuído a múltiplas turmas.
  - Regras de autorização baseadas em vínculo explícito, não em posse exclusiva da turma.
- **Dependências**: Foundations de autenticação, AnswerKey, tentativa online e OMR.
- **DoD**:
  - professor acessa apenas turmas vinculadas;
  - aluno preserva histórico ao trocar de turma;
  - exame pode ser compartilhado entre turmas sem alterar histórico;
  - regressões cobrem isolamento, integridade e compatibilidade com AnswerKey / Attempt / Grade.

---

### Fase 5 — Interface Frontend para Avaliações Online
- **Status**: concluída e validada no frontend.
- **Objetivo**: disponibilizar no frontend Next.js o fluxo operacional completo para criação de provas por professores e realização sequencial de exames online por estudantes.
- **Entregas**:
  - Painel de gestão de provas (`/exams`) para professores.
  - Tela de realização de prova (`/attempts/[id]`) para estudantes com entrega de uma questão por vez.
  - Autosave incremental e submissão da tentativa.
- **Dependências**: backend consolidado da Fase 4.
- **DoD**:
  - professor monta e publica prova pela interface;
  - estudante realiza prova com navegação sequencial e autosave.

---

### Fase 6 — Interface Frontend para Analytics Pedagógico e Habilidades BNCC/SEDU
- **Status**: concluída no baseline atual.
- **Objetivo**: oferecer dashboards pedagógicos para professores e gestores.
- **Entregas**:
  - painel de desempenho por turma, por exame e por habilidade;
  - visualização gráfica de taxa de acerto por questão e distribuição de notas;
  - suporte ao Workflow B;
  - download de relatórios em PDF e planilhas XLSX.
- **Dependências**: Fase 5.
- **DoD**:
  - professor visualiza gráficos de desempenho por habilidade tanto para exames com questões quanto para exames sem Question Bank.

---

### Fase 7 — Hardening de Segurança, Auditoria & LGPD
- **Status**: concluída e validada.
- **Objetivo**: elevar o nível de governança, conformidade LGPD e auditoria de produção.
- **Entregas**:
  - ingestão automática em `audit_logs` para eventos sensíveis;
  - rotas de LGPD para política de privacidade, exportação de dados e anonimização;
  - registro de consentimento de monitoramento em `consents`;
  - eventos de segurança em `security_events`.
- **Dependências**: Fases 4, 5 e 6.
- **DoD**:
  - eventos sensíveis geram registros de auditoria imutáveis;
  - consentimento e exportação de dados foram validados;
  - o fluxo de monitoramento tem base técnica para evolução futura.

---

### Fase 8 — Produção e Visualização de Provas
- **Status**: em implementação.
- **Objetivo**: separar a criação de questões da montagem da prova, permitir a visualização da prova antes da publicação e gerar folhas OMR personalizadas por aluno.
- **Entregas**:
  - consulta visual do Banco de Questões para montagem da prova;
  - montagem da prova por seleção de questões já existentes;
  - pré-visualização da prova sem exposição do gabarito;
  - geração de folhas OMR por aluno com dados preenchidos automaticamente;
  - integração com turmas e matrículas para produzir o lote correto de folhas.
- **Foco atual**: consolidação da montagem da prova por seleção de questões e da exportação de folhas OMR personalizadas por aluno.
- **Dependências**: Fases 3, 4, 5 e 7.
- **DoD**:
  - professor monta uma prova a partir do Banco de Questões;
  - professor visualiza a prova antes da publicação;
  - sistema gera folhas personalizadas para os alunos elegíveis;
  - Workflow A, Workflow B, online e OMR seguem funcionando.

---

### Fase 9 — Escala OMR e Funcionalidades Avançadas (Pós-MVP)
- **Objetivo**: Expandir as capacidades operacionais do módulo impresso para grandes redes de ensino.
- **Entregas**:
  - Processamento OMR em lote de PDFs multipágina digitalizados em escâneres alimentadores.
  - Suporte a novos layouts de folhas de respostas (ex: 100 questões, formato Simulado ENEM).
  - Abstração de storage OMR compatível com MinIO/Object Storage, preservando o filesystem local como backend de desenvolvimento.
- **Prioridade**: P3 (Futuro).

---

## 3. Critérios de Aceitação Gerais (Definition of Done)

Para qualquer nova funcionalidade ser considerada concluída no COLA-ZERO:
1. **Sem Duplicação**: Nenhuma duplicação de regra de negócio ou modelo de dados.
2. **Testes Automatizados**: Inclusão de testes unitários/integração com 100% de aprovação.
3. **Documentação**: Atualização dos documentos oficiais relevantes em [ARCHITECTURE.md](ARCHITECTURE.md) ou manuais de módulo.
4. **Respeito aos Princípios**: Manutenção da entrega de uma questão por vez em provas online e garantia de funcionamento do dashboard com ou sem banco de questões.
5. **Hardening Pós-MVP**: Migrações de segurança como `Argon2` e outros endurecimentos podem permanecer como débito técnico até a estabilização do MVP, desde que estejam explicitamente documentados.

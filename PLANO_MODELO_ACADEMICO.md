# COLA-ZERO — Plano de Implementação do Modelo Acadêmico de Turmas, Matrículas e Atribuições

> **Single Source of Truth** para a próxima etapa fundacional do COLA-ZERO: redefinição do modelo acadêmico de `Class`, vínculos de professores, matrículas de alunos e atribuição de exames a turmas.
>
> **Status:** Implementado e validado no backend; mantido aqui como referência arquitetural.
>
> **Base de decisão:** auditoria do repositório atual + regras de negócio confirmadas para o produto.

---

## 1. Objetivo do Plano

O objetivo desta etapa é alinhar o modelo acadêmico do sistema com as regras de negócio confirmadas:

1. Um aluno pode pertencer a apenas **uma turma ativa por período acadêmico**.
2. Uma turma pode ter **múltiplos professores**.
3. Um professor pode acessar **múltiplas turmas**.
4. Uma prova/exame pode ser atribuída a **múltiplas turmas**.
5. Turmas, matrículas e atribuições devem preservar **histórico acadêmico**.
6. As avaliações já publicadas não podem ter seu significado histórico alterado.

Este plano existe para evitar que o frontend e as próximas camadas funcionais sejam construídos em cima de um modelo acadêmico incorreto.

---

## 2. Situação Atual Observada no Repositório

### 2.1 Turmas

O estado atual já reflete o modelo alvo:

- `classes` existe como entidade operacional.
- A autorização de professor é baseada em vínculo explícito via `teacher_classes`.
- `Class.teacher_id` permanece como metadado de criação/proveniência, não como dono exclusivo da turma.

### 2.2 Matrículas

- `class_students` existe como tabela de vínculo histórico.
- O vínculo já expressa período acadêmico, ativo/inativo e arquivamento lógico.
- O modelo restringe uma matrícula ativa por período para cada estudante.

### 2.3 Atribuição de Exames

- `Exam.class_id` ainda existe como compatibilidade legada e permanece como string livre.
- A atribuição nativa entre exame e turma é feita por `exam_classes`.
- O mesmo exame pode ser publicado para múltiplas turmas sem alterar o histórico.

### 2.4 Integridade Histórica

- `AnswerKey`, `AnswerKeyItem`, `Attempt`, `AttemptAnswer` e `Grade` já sustentam a integridade avaliativa.
- O risco atual está na camada acadêmica: turmas e vínculos ainda não possuem semântica histórica completa.

---

## 3. Decisão Arquitetural Confirmada

### 3.1 `Class` deve representar uma turma concreta de um período acadêmico

Esta é a decisão recomendada para o COLA-ZERO.

Exemplo:

- `2º Ano A - 2025` = um registro `Class`
- `2º Ano A - 2026` = outro registro `Class`

Motivos:

- preserva histórico de notas e tentativas;
- simplifica troca de turma entre anos letivos;
- evita ambiguidade em transferência de alunos;
- torna o vínculo de professores e provas mais explícito;
- facilita o rollover acadêmico anual.

### 3.2 Não adotar turma “lógica” persistente como entidade primária

Uma “turma lógica” persistente com ano letivo apenas nos vínculos complica:

- autorização;
- manutenção do histórico;
- atribuição de provas;
- consultas pedagógicas;
- troca de turma entre períodos.

Se no futuro for necessário um agrupamento estável entre anos, isso deve ser um conceito adicional e opcional, não a identidade principal de `Class`.

---

## 4. Modelo de Domínio Recomendado

### 4.1 Entidades principais

```text
User
 ├── Teacher
 └── Student

Teacher
  └── TeacherClass
          ├── teacher_id
          ├── class_id
          ├── academic_year / academic_period
          ├── active
          └── timestamps

Student
  └── class_students
          ├── student_id
          ├── class_id
          ├── academic_year / academic_period
          ├── started_at
          ├── ended_at
          ├── active
          └── timestamps

Class
  ├── concrete instance of a school period
  ├── metadata for grade/section/period
  └── no ownership semantics

Exam
  ├── ExamClass
  ├── AnswerKey
  ├── Attempts
  └── lifecycle status

ExamClass
  ├── exam_id
  ├── class_id
  ├── assigned_at / published_at
  └── active
```

### 4.2 Relações pretendidas

- `Teacher ↔ Class = N:N`
- `Student ↔ Class = histórico de matrículas com no máximo uma matrícula ativa por período`
- `Exam ↔ Class = N:N`
- `Exam` continua sendo a unidade de avaliação publicada
- `AnswerKey` continua sendo a fonte canônica de correção

---

## 5. Regras de Negócio que Este Plano Implementa

### 5.1 Turmas

- Uma turma é uma instância concreta de um período/ano letivo.
- Turmas podem ser arquivadas, mas não devem perder histórico.
- Turmas não são “propriedade” exclusiva de um professor.

### 5.2 Professores

- Um professor pode acessar várias turmas.
- Uma turma pode ser acessada por vários professores.
- O acesso do professor deve ser autorizado por vínculo explícito, não por posse da turma.

### 5.3 Alunos

- Um aluno pode ter histórico de várias turmas ao longo do tempo.
- Em um período acadêmico ativo, o aluno deve ter apenas uma matrícula ativa.
- Troca de turma deve preservar histórico.

### 5.4 Exames

- Um exame pode ser associado a múltiplas turmas.
- Um exame publicado deve manter seu significado histórico.
- Reuso de exame em outro ano/período deve ocorrer como nova aplicação, não como mutação silenciosa do passado.

---

## 6. Modelo Alvo de Banco de Dados

### 6.1 Tabelas que devem ser introduzidas ou ajustadas

#### `teacher_classes`
Associação entre professor e turma.

Campos esperados:

- `id` UUID ou PK composta
- `teacher_id`
- `class_id`
- `academic_year` ou `academic_period`
- `active`
- `created_at`
- `updated_at` ou `revoked_at`, se necessário

Regras:

- impede duplicação de vínculo ativo;
- permite histórico de acesso do professor;
- base para autorização backend.

#### `class_students`
Associação histórica entre aluno e turma.

Campos esperados:

- `id` UUID ou PK composta
- `student_id`
- `class_id`
- `academic_year` ou `academic_period`
- `started_at`
- `ended_at`
- `active`
- `created_at`

Regras:

- um aluno só pode ter uma matrícula ativa por período;
- histórico preservado após transferência;
- vínculos antigos permanecem consultáveis.

#### `exam_classes`
Associação entre exame e turma.

Campos esperados:

- `id` UUID ou PK composta
- `exam_id`
- `class_id`
- `assigned_at` ou `published_at`
- `active`

Regras:

- um exame pode ser publicado para várias turmas;
- a elegibilidade do aluno depende da matrícula + atribuição;
- o backend deve consultar essa tabela, não apenas `exams.class_id`.

### 6.2 Campos que devem ser reavaliados

- `classes.teacher_id` como metadado de proveniência;
- `class_students` como vínculo histórico de matrícula;
- `exams.class_id` como campo legado de compatibilidade;

Esses elementos ainda podem existir durante a transição, mas não devem continuar como fonte primária de autorização ou atribuição após a etapa de refatoração.

---

## 7. Estratégia de Migração Incremental

### Fase 1 — Schema novo e coexistência

- adicionar as novas tabelas de associação;
- manter os campos legados funcionando em paralelo;
- preparar os modelos ORM e schemas;
- preservar compatibilidade de leitura.

### Fase 2 — Backfill

- migrar vínculos de professor para `teacher_classes`;
- migrar vínculos de aluno para `class_students`;
- migrar atribuições de exame para `exam_classes` quando aplicável;
- validar duplicidades e relações históricas.

### Fase 3 — Autorização e serviços

- trocar checks de ownership por checks de associação explícita;
- atualizar serviços de turma, exame e elegibilidade do aluno;
- ajustar consultas de listagem e acesso por ID.

### Fase 4 — Consolidação

- descontinuar o uso de campos legados como fonte primária;
- manter apenas como compatibilidade transitória, se necessário;
- reforçar constraints e índices.

### Fase 5 — Validação

- executar testes de isolamento;
- executar regressão de OMR, AnswerKey, Workflow A/B e Attempt Engine;
- validar migrações em PostgreSQL de desenvolvimento.

---

## 8. Impacto Esperado nas APIs

### Endpoints que provavelmente precisarão mudar

- `GET/POST/PATCH/DELETE /api/v1/classes`
- `POST/DELETE /api/v1/classes/{id}/teachers`
- `POST/DELETE /api/v1/classes/{id}/students`
- `GET/POST/PATCH /api/v1/exams`
- `POST /api/v1/exams/{id}/publish`
- `GET /api/v1/exams/{id}`
- `GET /api/v1/exams/{id}/statistics`
- `GET /api/v1/exams/{id}/export/pdf`
- `GET /api/v1/exams/{id}/export/xlsx`
- `GET /api/v1/exams/available`
- `GET /api/v1/attempts/...` para elegibilidade do aluno

### O que deve permanecer compatível durante a transição

- autenticação e RBAC existentes;
- AnswerKey e Attempt Engine;
- OMR;
- consentimento, auditoria e LGPD;
- Workflow A / Workflow B.

---

## 9. Impacto Esperado no Frontend

### Telas que dependem deste redesenho

- gestão de turmas;
- vinculação de professores;
- matrícula de alunos;
- atribuição de exames a turmas;
- listagem de exames disponíveis para o aluno;
- painel do professor com visão por turma;
- dashboards pedagógicos filtrados por turma.

### O que pode aguardar

- front-end completo de analytics avançado;
- anti-cheating visual;
- expansões do OMR em lote.

---

## 10. Critérios de Aceitação da Próxima Etapa

Esta etapa só deve ser considerada pronta quando:

1. professor A não conseguir acessar a turma de professor B sem vínculo explícito;
2. aluno não conseguir manter múltiplas matrículas ativas no mesmo período;
3. um exame puder ser atribuído a múltiplas turmas;
4. histórico de matrículas e tentativas permanecer íntegro após troca de turma;
5. a autorização passar a ser baseada em associação, não em posse;
6. a suíte de testes cobrir:
   - isolamento entre professores;
   - isolamento entre turmas;
   - histórico de matrícula;
   - atribuição multi-turma de exames;
   - regressão de AnswerKey, OMR e Attempt Engine;
7. migrações Alembic forem linearmente válidas em PostgreSQL.

---

## 11. Riscos se Esta Etapa For Postergada

- o frontend novo pode ser construído sobre um modelo de turma incorreto;
- a autorização ficará frágil para cenários de múltiplos professores;
- a troca de turma por período ficará mais cara de modelar depois;
- a atribuição de exames para várias turmas exigirá retrabalho;
- relatórios e filtros por turma podem gerar resultados historicamente imprecisos.

---

## 12. Ordem Recomendada de Implementação

1. **Modelo de associação de professores e turmas**
   - criar `teacher_classes`
   - migrar autorização para vínculo explícito

2. **Modelo histórico de matrícula**
  - criar `class_students`
   - impor uma matrícula ativa por período

3. **Modelo de atribuição de exames**
   - criar `exam_classes`
   - atualizar elegibilidade e publicação

4. **Imutabilidade operacional da prova publicada**
   - reforçar bloqueios de mutação após publicação
   - manter histórico de tentativas e notas

5. **Regressão e validação**
   - testes de backend
   - validação de migrations
   - revisão de autorização e isolamento

---

## 13. Definição de Pronto

Ao final desta etapa:

- o modelo de turmas será compatível com múltiplos professores;
- o histórico de matrícula do aluno será preservado;
- o mesmo exame poderá ser atribuído a múltiplas turmas;
- a autorização refletirá associações explícitas;
- o frontend poderá ser construído sobre uma base acadêmica correta.

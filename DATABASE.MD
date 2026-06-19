# COLA-ZERO — Modelo de Banco de Dados

---

# 1. Visão geral

O modelo de dados do COLA-ZERO é orientado por:

> Question Bank + Attempt Engine

A entidade principal do domínio é a questão. Provas são composições de questões. Tentativas representam a execução da prova por um aluno.

Princípios do banco:

- todas as chaves primárias usam UUID
- não usar IDs incrementais
- preservar histórico acadêmico
- evitar duplicação de conteúdo de questão em provas
- registrar auditoria e eventos de monitoramento
- coletar apenas dados necessários ao produto

---

# 2. Convenções gerais

## 2.1 Identificadores

Todas as tabelas principais devem usar:

```sql
id UUID PRIMARY KEY
```

## 2.2 Datas

Campos temporais recomendados:

- `created_at`
- `updated_at`
- `deleted_at` quando soft delete for aplicável

## 2.3 Histórico

Regras:

- registros acadêmicos importantes não devem ser apagados de forma irreversível
- respostas não devem ser sobrescritas quando a preservação histórica for necessária
- logs e eventos devem ser mantidos conforme política de retenção

---

# 3. Tabelas principais

## 3.1 users

Representa usuários autenticados do sistema.

```sql
id UUID PRIMARY KEY
email TEXT UNIQUE NOT NULL
password_hash TEXT NOT NULL
role TEXT NOT NULL
created_at TIMESTAMP NOT NULL
updated_at TIMESTAMP NOT NULL
```

Valores esperados para `role`:

- `student`
- `teacher`
- `admin`

---

## 3.2 questions

Representa o banco de questões reutilizável.

```sql
id UUID PRIMARY KEY
statement TEXT NOT NULL
type TEXT NOT NULL
options JSONB
correct_answer JSONB
explanation TEXT
subject TEXT
difficulty TEXT
tags TEXT[]
image_url TEXT
created_by UUID NOT NULL
created_at TIMESTAMP NOT NULL
updated_at TIMESTAMP NOT NULL
```

Observações:

- `created_by` referencia `users.id`
- `options` pode armazenar alternativas de questões objetivas
- `correct_answer` deve permitir estrutura compatível com diferentes tipos de questão

---

## 3.3 classes

Representa turmas ou agrupamentos de alunos.

```sql
id UUID PRIMARY KEY
name TEXT NOT NULL
teacher_id UUID NOT NULL
created_at TIMESTAMP NOT NULL
updated_at TIMESTAMP NOT NULL
```

Observações:

- `teacher_id` referencia `users.id`

---

## 3.4 class_students

Relaciona alunos às turmas.

```sql
class_id UUID NOT NULL
student_id UUID NOT NULL
created_at TIMESTAMP NOT NULL
PRIMARY KEY (class_id, student_id)
```

Observações:

- `class_id` referencia `classes.id`
- `student_id` referencia `users.id`

---

## 3.5 exams

Representa a configuração de uma prova.

```sql
id UUID PRIMARY KEY
title TEXT NOT NULL
class_id UUID NOT NULL
status TEXT NOT NULL
total_time_seconds INT
randomization_enabled BOOLEAN NOT NULL DEFAULT FALSE
created_by UUID NOT NULL
created_at TIMESTAMP NOT NULL
updated_at TIMESTAMP NOT NULL
```

Valores esperados para `status`:

- `draft`
- `published`
- `archived`

Observações:

- `class_id` referencia `classes.id`
- `created_by` referencia `users.id`

---

## 3.6 exam_questions

Relaciona provas a questões sem duplicar o conteúdo da questão.

```sql
id UUID PRIMARY KEY
exam_id UUID NOT NULL
question_id UUID NOT NULL
display_order INT NOT NULL
weight NUMERIC(10,2) NOT NULL
created_at TIMESTAMP NOT NULL
```

Observações:

- `exam_id` referencia `exams.id`
- `question_id` referencia `questions.id`
- relacionamento central: `Exam -> ExamQuestion -> Question`

---

## 3.7 attempts

Representa a tentativa de um aluno em uma prova.

```sql
id UUID PRIMARY KEY
exam_id UUID NOT NULL
student_id UUID NOT NULL
status TEXT NOT NULL
started_at TIMESTAMP
ended_at TIMESTAMP
score NUMERIC(10,2)
created_at TIMESTAMP NOT NULL
updated_at TIMESTAMP NOT NULL
```

Valores esperados para `status`:

- `not_started`
- `in_progress`
- `submitted`
- `graded`

Observações:

- `exam_id` referencia `exams.id`
- `student_id` referencia `users.id`

---

## 3.8 answers

Representa respostas submetidas dentro de uma tentativa.

```sql
id UUID PRIMARY KEY
attempt_id UUID NOT NULL
question_id UUID NOT NULL
answer_payload JSONB NOT NULL
is_correct BOOLEAN
answered_at TIMESTAMP NOT NULL
created_at TIMESTAMP NOT NULL
```

Observações:

- `attempt_id` referencia `attempts.id`
- `question_id` referencia `questions.id`
- `answer_payload` deve permitir respostas objetivas ou discursivas
- respostas devem ser persistidas imediatamente após envio

---

## 3.9 monitoring_events

Representa eventos de monitoramento associados à tentativa.

```sql
id UUID PRIMARY KEY
attempt_id UUID NOT NULL
event_type TEXT NOT NULL
metadata JSONB
created_at TIMESTAMP NOT NULL
```

Eventos suportados no MVP:

- `visibilitychange`
- `blur`
- `focus`
- `fullscreen_enter`
- `fullscreen_exit`

Observações:

- `attempt_id` referencia `attempts.id`
- não armazenar dados fora do contexto necessário da tentativa

---

## 3.10 audit_logs

Representa auditoria de ações sensíveis do sistema.

```sql
id UUID PRIMARY KEY
user_id UUID
event_type TEXT NOT NULL
metadata JSONB
created_at TIMESTAMP NOT NULL
```

Exemplos de eventos auditáveis:

- login
- troca de senha
- criação de prova
- publicação de prova
- alteração de nota

Observações:

- `user_id` referencia `users.id`
- alguns eventos podem existir sem usuário autenticado associado, quando aplicável

---

# 4. Relacionamentos principais

```text
User
 ├── Question.created_by
 ├── Exam.created_by
 ├── Class.teacher_id
 ├── Attempt.student_id
 └── AuditLog.user_id

Class
 ├── Exam.class_id
 └── ClassStudent.class_id

Question
 └── ExamQuestion.question_id

Exam
 ├── ExamQuestion.exam_id
 └── Attempt.exam_id

Attempt
 ├── Answer.attempt_id
 └── MonitoringEvent.attempt_id
```

---

# 5. Regras de modelagem

## 5.1 Banco de questões

- questões devem ser reutilizáveis
- uma mesma questão pode estar em várias provas
- não duplicar conteúdo de questão dentro da prova

## 5.2 Tentativas

- a tentativa é a unidade de execução da prova
- o frontend não deve receber a prova inteira de uma vez
- a resposta deve ser salva imediatamente

## 5.3 Histórico

- respostas e eventos devem preservar rastreabilidade
- dados acadêmicos relevantes não devem ser apagados sem política apropriada

## 5.4 Auditoria

- ações sensíveis devem gerar log
- logs devem permitir investigação posterior

---

# 6. Índices recomendados

Sugestões iniciais de índice:

```sql
CREATE UNIQUE INDEX idx_users_email ON users(email);
CREATE INDEX idx_questions_created_by ON questions(created_by);
CREATE INDEX idx_questions_subject ON questions(subject);
CREATE INDEX idx_questions_difficulty ON questions(difficulty);
CREATE INDEX idx_exams_class_id ON exams(class_id);
CREATE INDEX idx_exam_questions_exam_id ON exam_questions(exam_id);
CREATE INDEX idx_exam_questions_question_id ON exam_questions(question_id);
CREATE INDEX idx_attempts_exam_id ON attempts(exam_id);
CREATE INDEX idx_attempts_student_id ON attempts(student_id);
CREATE INDEX idx_answers_attempt_id ON answers(attempt_id);
CREATE INDEX idx_monitoring_events_attempt_id ON monitoring_events(attempt_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
```

---

# 7. LGPD

Princípios aplicados ao banco:

- minimização de dados
- finalidade explícita
- retenção controlada
- suporte a exportação de dados
- suporte a anonimização quando legalmente permitida

Evitar armazenar:

- arquivos pessoais
- conteúdo do dispositivo
- histórico de navegação
- qualquer dado sem finalidade clara

---

# 8. Escopo do MVP

O modelo de banco do MVP deve sustentar:

- autenticação de usuários
- banco de questões reutilizável
- criação e publicação de provas
- tentativas com uma questão por vez
- persistência de respostas
- registro de eventos de monitoramento
- auditoria de ações sensíveis
- capacidades básicas de LGPD
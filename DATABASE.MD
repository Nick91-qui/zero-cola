# COLA-ZERO — Modelo de Banco de Dados

---

# 1. Visão geral

O modelo de dados do COLA-ZERO é orientado por:

> Question Bank + Attempt Engine

O banco de questões (Question Bank) é o repositório central de conteúdo. As provas (Exams) são configurações de entrega compostas por questões reutilizáveis. O histórico acadêmico é representado por tentativas (Attempts) e respostas (Answers).

Fluxo do domínio: Question -> Exam -> Attempt -> Answer

Princípios do banco:

- todas as chaves primárias usam UUID
- não usar IDs incrementais
- preservar histórico acadêmico
- evitar duplicação de conteúdo de questão em provas
- registrar auditoria e eventos de segurança (security_events)
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

## 3.1 users (IMPLEMENTADO ✅)

Representa usuários autenticados do sistema.

```sql
id UUID PRIMARY KEY
email TEXT UNIQUE NOT NULL
password_hash TEXT NOT NULL
role TEXT NOT NULL (Enum: STUDENT, TEACHER, ADMIN)
is_active BOOLEAN NOT NULL DEFAULT TRUE
created_at TIMESTAMP NOT NULL DEFAULT NOW()
updated_at TIMESTAMP NOT NULL DEFAULT NOW()
```

**Status**: ✅ Implementado em `app/models/user.py`
- Python model com SQLAlchemy
- Migration: `0001_create_users` (testada upgrade/downgrade)
- Repository pattern em `app/repositories/user.py`
- Tests: 7 auth tests passando

**Índices**:
- `users_email_key` (UNIQUE)

**Regras de negócio**:
- Email único por usuário
- Senha hasheada com bcrypt
- Role controlado por Enum
- is_active permite deativação sem hard delete

## 3.2 questions

Representa o banco de questões reutilizável.

```sql
id UUID PRIMARY KEY
parent_id UUID REFERENCES questions(id) ON DELETE SET NULL -- Aponta para a versão inicial (agrupador)
version INT NOT NULL DEFAULT 1 -- Contador de versão (1, 2, 3...)
is_active BOOLEAN NOT NULL DEFAULT TRUE -- Indica se é a versão atual ativa para novas provas
statement TEXT NOT NULL
type TEXT NOT NULL
options JSONB
correct_answer JSONB
explanation TEXT
subject TEXT
difficulty TEXT
tags TEXT[]
image_url TEXT
created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT -- Impede exclusão do criador
created_at TIMESTAMP NOT NULL DEFAULT NOW()
updated_at TIMESTAMP NOT NULL DEFAULT NOW()
```

Observações:

- `created_by` referencia `users.id`
- `options` pode armazenar alternativas de questões objetivas
- `correct_answer` deve permitir estrutura compatível com diferentes tipos de questão
- **Versionamento e Imutabilidade**: Questões publicadas são **imutáveis**. Qualquer edição gera um novo registro com o mesmo `parent_id`, uma `version` incremental e a versão anterior marcada como `is_active = FALSE`. As provas (`exams`) e os escaneamentos OMR (`omr_scans`) sempre referenciam o UUID da versão específica (`questions.id`), garantindo rastreabilidade acadêmica histórica mesmo se a questão for alterada no futuro.

---

## 3.3 classes

Representa turmas ou agrupamentos de alunos.

```sql
id UUID PRIMARY KEY
name TEXT NOT NULL
teacher_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT -- Impede exclusão do professor ativo
created_at TIMESTAMP NOT NULL DEFAULT NOW()
updated_at TIMESTAMP NOT NULL DEFAULT NOW()
```

Observações:

- `teacher_id` referencia `users.id`

---

## 3.4 class_students

Relaciona alunos às turmas.

```sql
class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE -- Remove vínculo se a turma for excluída
student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE -- Remove vínculo se o aluno for excluído
created_at TIMESTAMP NOT NULL DEFAULT NOW()
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
class_id UUID NOT NULL REFERENCES classes(id) ON DELETE RESTRICT -- Impede exclusão da turma com prova
status TEXT NOT NULL (Enum: draft, published, archived)
total_time_seconds INT
max_attempts INT NOT NULL DEFAULT 1
randomization_enabled BOOLEAN NOT NULL DEFAULT FALSE
created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT -- Impede exclusão do criador da prova
created_at TIMESTAMP NOT NULL DEFAULT NOW()
updated_at TIMESTAMP NOT NULL DEFAULT NOW()
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
exam_id UUID NOT NULL REFERENCES exams(id) ON DELETE CASCADE -- Cascade se a prova for excluída
question_id UUID NOT NULL REFERENCES questions(id) ON DELETE RESTRICT -- Impede exclusão da questão vinculada
display_order INT NOT NULL
weight NUMERIC(10,2) NOT NULL
created_at TIMESTAMP NOT NULL DEFAULT NOW()
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
exam_id UUID NOT NULL REFERENCES exams(id) ON DELETE RESTRICT -- Histórico: impede exclusão de prova realizada
student_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT -- Histórico: impede exclusão de aluno com histórico
attempt_number INT NOT NULL
status TEXT NOT NULL (Enum: not_started, in_progress, submitted, graded)
started_at TIMESTAMP
ended_at TIMESTAMP
score NUMERIC(10,2)
created_at TIMESTAMP NOT NULL DEFAULT NOW()
updated_at TIMESTAMP NOT NULL DEFAULT NOW()
```

Valores esperados para `status`:

- `not_started`
- `in_progress`
- `submitted`
- `graded`

Observações:

- `exam_id` referencia `exams.id`
- `student_id` referencia `users.id`
- `attempt_number` indica a ordem da tentativa para o aluno no exame (começa em 1)
- a quantidade máxima de tentativas é configurada em `exams.max_attempts`

---

## 3.8 answers

Representa respostas submetidas dentro de uma tentativa.

```sql
id UUID PRIMARY KEY
attempt_id UUID NOT NULL REFERENCES attempts(id) ON DELETE CASCADE -- Respostas caem se a tentativa cair (tentativa tem RESTRICT)
question_id UUID NOT NULL REFERENCES questions(id) ON DELETE RESTRICT -- Histórico: impede exclusão de questão respondida
answer_payload JSONB NOT NULL
is_correct BOOLEAN
answered_at TIMESTAMP NOT NULL DEFAULT NOW()
created_at TIMESTAMP NOT NULL DEFAULT NOW()
```

Observações:

- `attempt_id` referencia `attempts.id`
- `question_id` referencia `questions.id`
- `answer_payload` deve permitir respostas objetivas ou discursivas
- respostas devem ser persistidas imediatamente após envio

---

## 3.9 security_events

Representa eventos de segurança associados à tentativa.

```sql
id UUID PRIMARY KEY
attempt_id UUID NOT NULL REFERENCES attempts(id) ON DELETE CASCADE -- Eventos caem se a tentativa cair
event_type TEXT NOT NULL (Enum: visibilitychange, blur, focus, fullscreen_enter, fullscreen_exit)
metadata JSONB
created_at TIMESTAMP NOT NULL DEFAULT NOW()
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
user_id UUID REFERENCES users(id) ON DELETE SET NULL -- Mantém registro mesmo se o usuário for excluído (LGPD)
event_type TEXT NOT NULL
metadata JSONB
created_at TIMESTAMP NOT NULL DEFAULT NOW()
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

## 3.11 omr_templates

Representa o gabarito físico/standalone configurado no sistema.

```sql
id UUID PRIMARY KEY
exam_id UUID REFERENCES exams(id) ON DELETE SET NULL -- Opcional (NULL em modo standalone)
layout_version VARCHAR(50) NOT NULL -- Identifica o layout geométrico em código
total_questions INT NOT NULL
options_per_question INT NOT NULL DEFAULT 5
correct_answers JSONB -- Chaves corretas em formato de mapa (obrigatório se exam_id for NULL)
created_at TIMESTAMP NOT NULL DEFAULT NOW()
updated_at TIMESTAMP NOT NULL DEFAULT NOW()
```

---

## 3.12 omr_scans

Representa as folhas de respostas digitalizadas e corrigidas pelo OMR.

```sql
id UUID PRIMARY KEY
omr_template_id UUID NOT NULL REFERENCES omr_templates(id) ON DELETE CASCADE
student_code VARCHAR(5) -- Código numérico de 5 dígitos lido no OMR do aluno
student_id UUID REFERENCES users(id) ON DELETE SET NULL -- Resolvido via student_code
status TEXT NOT NULL (Enum: processing, success, review_needed, failed)
image_url TEXT NOT NULL -- Caminho para a foto individual salva (JPG/PNG)
detected_answers JSONB -- Respostas lidas OMR
raw_confidence JSONB -- Níveis de cor de preenchimento obtidos
score NUMERIC(5,2) -- Pontuação gerada
error_message TEXT -- Registra falhas na engine OpenCV
processed_at TIMESTAMP
created_at TIMESTAMP NOT NULL DEFAULT NOW()
updated_at TIMESTAMP NOT NULL DEFAULT NOW()
```

---

## 3.13 grades

Representa as notas finais consolidadas obtidas pelos alunos, independentemente da origem da avaliação (provas online ou gabaritos OMR físicos). É a entidade unificada de notas compartilhada por todas as fontes de avaliação do sistema.

```sql
id UUID PRIMARY KEY
student_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT -- Impede remoção de aluno com notas registradas
source_type VARCHAR(50) NOT NULL -- Enum/valores: 'ONLINE', 'OMR'
source_id UUID NOT NULL -- Vínculo lógico para attempts.id ou omr_scans.id
score NUMERIC(5,2) NOT NULL -- Nota consolidada final
teacher_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT -- Professor que aplicou/revisou/confirmou a nota
created_at TIMESTAMP NOT NULL DEFAULT NOW()
updated_at TIMESTAMP NOT NULL DEFAULT NOW()
```

Observações:
- `source_id` é uma chave estrangeira lógica (polimórfica). Não possui restrição física de FK (Foreign Key constraint) no Postgres, mas aponta logicamente para `attempts.id` (quando `source_type` = 'ONLINE') ou `omr_scans.id` (quando `source_type` = 'OMR').
- Como as tentativas de exames (`attempts`) e leituras de gabarito (`omr_scans`) são registros históricos de alta integridade, a tabela `grades` garante a rastreabilidade acadêmica unificada.

---

# 4. Relacionamentos principais

```text
User
 ├── Question.created_by (RESTRICT)
 ├── Exam.created_by (RESTRICT)
 ├── Class.teacher_id (RESTRICT)
 ├── Attempt.student_id (RESTRICT)
 ├── AuditLog.user_id (SET NULL)
 ├── OMRScan.student_id (SET NULL, via student_code resolution)
 ├── Grade.student_id (RESTRICT)
 └── Grade.teacher_id (RESTRICT)

Class
 ├── Exam.class_id (RESTRICT)
 └── ClassStudent.class_id (CASCADE)

Question
 ├── ExamQuestion.question_id (RESTRICT)
 ├── Answer.question_id (RESTRICT)
 └── Question.parent_id (SET NULL)

Exam
 ├── ExamQuestion.exam_id (CASCADE)
 ├── Attempt.exam_id (RESTRICT)
 └── OMRTemplate.exam_id (SET NULL)

Attempt
 ├── Answer.attempt_id (CASCADE)
 ├── SecurityEvent.attempt_id (CASCADE)
 └── Grade.source_id (Logical link, source_type = 'ONLINE')

OMRTemplate
 └── OMRScan.omr_template_id (CASCADE)

OMRScan
 └── Grade.source_id (Logical link, source_type = 'OMR')
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
CREATE INDEX idx_questions_parent_id ON questions(parent_id);
CREATE INDEX idx_questions_subject ON questions(subject);
CREATE INDEX idx_questions_difficulty ON questions(difficulty);
CREATE INDEX idx_exams_class_id ON exams(class_id);
CREATE INDEX idx_exam_questions_exam_id ON exam_questions(exam_id);
CREATE INDEX idx_exam_questions_question_id ON exam_questions(question_id);
CREATE INDEX idx_attempts_exam_id ON attempts(exam_id);
CREATE INDEX idx_attempts_student_id ON attempts(student_id);
CREATE INDEX idx_answers_attempt_id ON answers(attempt_id);
CREATE INDEX idx_security_events_attempt_id ON security_events(attempt_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_grades_student_id ON grades(student_id);
CREATE INDEX idx_grades_source ON grades(source_type, source_id);
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
- registro de eventos de segurança (security_events)
- auditoria de ações sensíveis
- capacidades básicas de LGPD
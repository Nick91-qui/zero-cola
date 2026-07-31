# COLA-ZERO — Target Domain Model Specification

> **Status:** Design specification — approved for implementation and used as the architectural reference for the delivered milestones.
> **Basis:** Consistency audit dated 2026-07-27
> **Scope:** Domain model and database architecture refactor
> **Implementation status:** Core milestones 1-9 implemented; later roadmap items remain deferred.
> **Note:** references to legacy fields and transitional steps are preserved in the document as migration context and historical traceability.
> **Constraint:** This document is the design artifact that guides implementation. It does not itself modify code or documentation.

---

## 0. Design Principles

The following principles govern the target domain model.

### 0.1 AnswerKey is the common denominator

Every assessment — online or printed, internal or external — has exactly one `AnswerKey`.

The dashboard and grading systems operate on answer keys. Questions are optional.

### 0.2 Workflow B is a first-class path

Workflow B, in which an assessment has no Question Bank questions, is not a degraded mode.

Nothing in grading, statistics, skill analytics, or dashboard functionality may require a `Question` row.

### 0.3 Single source of truth for correct answers

The current implementation duplicates correct answers between:

* `omr_templates.correct_answers` (`JSONB`);
* exam-bound `questions.correct_option`.

These sources can drift.

The target model eliminates this duplication.

Correct answers live exclusively in:

```text
AnswerKeyItem.correct_answer
```

### 0.4 OMR consumes answer keys

OMR is a consumer of answer keys, never their definition.

`OMRTemplate` describes the physical sheet geometry and links the physical assessment to an `Exam` and its `AnswerKey`.

`OMRTemplate` does not store correct answers.

### 0.5 Attempt is the unit of assessment execution

`Attempt` represents one student's execution of one assessment.

The same entity must support:

* OMR-confirmed printed assessments;
* future online assessment sessions.

No second Attempt entity should be introduced for online assessments.

### 0.6 No destructive renames without migration

Existing academic data, including test data, must be preserved through explicit Alembic data migrations.

No destructive schema transformation may silently discard existing records.

---

# 1. Workflow Definitions

The model must support two canonical workflows.

---

## 1.1 Workflow A — Question Bank → AnswerKey

```text
Teacher creates Question
(reusable, versioned, optional Skills)
        │
        ├── Question may be linked to 0..N Skills
        │
        ▼
Teacher assembles Exam from bank Questions
        │
        ├── Each ExamQuestion assigns display_order + weight
        │
        ▼
On publish, system projects ExamQuestions into AnswerKeyItems
        │
        ├── AnswerKeyItem.correct_answer ← Question.correct_answer
        ├── AnswerKeyItem.question_id ← bank Question version
        └── AnswerKeyItem.skills ← snapshot of Question.skills
        │
        ▼
Exam is now gradable
(online or printed)
```

### Workflow A invariant

Every `AnswerKeyItem` created through Workflow A has a non-null `question_id`.

Editing the Question Bank after publication does not mutate the AnswerKey.

The published AnswerKey is immutable.

---

## 1.2 Workflow B — Manual AnswerKey

Workflow B is used when the assessment does not originate from the Question Bank.

Typical examples include:

* externally authored assessments;
* Word documents;
* PDFs;
* printed assessments created outside the Question Bank.

```text
Teacher creates Exam
(external assessment)
        │
        ▼
Teacher creates AnswerKey directly
        │
        ├── item_number
        ├── correct_answer
        ├── optional Skills
        └── statement intentionally absent
        │
        ▼
Exam is gradable
(typically printed → OMR)
```

### Workflow B invariant

Every `AnswerKeyItem` created through Workflow B has:

```text
question_id = NULL
```

The following capabilities must work identically to Workflow A:

* grading;
* per-question statistics;
* per-skill analytics;
* dashboard rendering;
* exports;
* OMR processing.

---

## 1.3 Canonical Workflow Intersection

| Capability                     | Workflow A |      Workflow B |
| ------------------------------ | ---------: | --------------: |
| `AnswerKey` exists             |          ✔ |               ✔ |
| `AnswerKeyItem.correct_answer` |          ✔ |               ✔ |
| `AnswerKeyItem.skills`         |          ✔ |               ✔ |
| `AnswerKeyItem.statement`      |          ✔ | Optional/absent |
| Grading                        |          ✔ |               ✔ |
| Per-question statistics        |          ✔ |               ✔ |
| Per-skill analytics            |          ✔ |               ✔ |
| Dashboard rendering            |          ✔ |               ✔ |
| OMR sheet generation           |          ✔ |               ✔ |

---

# 2. Entity Responsibilities

---

## 2.1 Exam

**Responsibility:** Assessment configuration container.

Contains:

* title;
* owner;
* class reference;
* scoring policy;
* delivery mode;
* lifecycle status.

### Relationships

Owns exactly one `AnswerKey`.

References:

* `teacher_id`;
* `class_id` — currently a free string; target is a future FK to `classes`;
* optional `omr_template_id`.

### Does not

* own correct answers directly;
* own Questions directly.

Question composition occurs through:

```text
Exam
  └── ExamQuestion
        └── Question
```

The resulting composition is projected into:

```text
AnswerKey
  └── AnswerKeyItem
```

---

## 2.2 AnswerKey

**Status:** New entity.

**Responsibility:** Canonical record of correct answers for an Exam.

It is the single source of truth for:

* grading;
* OMR;
* statistics;
* dashboard data;
* exports.

### Relationships

* 1:1 with `Exam`;
* owns 1..N `AnswerKeyItem`.

### Lifecycle

Created:

* at Exam publication for Workflow A;
* manually for Workflow B.

An AnswerKey becomes immutable once it is published and is fully locked once an Attempt has been graded against it.

---

## 2.3 AnswerKeyItem

**Status:** New entity.

**Responsibility:** One graded slot within an AnswerKey.

### Fields

* `item_number`;
* `correct_answer`;
* `weight`;
* `statement` — nullable;
* `question_id` — nullable;
* `answer_key_id`.

### Relationships

* N:1 → `AnswerKey`;
* N:0..1 → `Question`;
* N:N → `Skill`.

### Workflow behavior

Workflow A:

```text
question_id IS NOT NULL
```

Workflow B:

```text
question_id IS NULL
```

This entity replaces the answer-key role currently played by the exam-bound `questions` table.

It also replaces:

```text
omr_templates.correct_answers
```

as the canonical source of correct answers.

---

## 2.4 Question

**Status:** Refactored into the reusable Question Bank entity.

**Responsibility:** Reusable, versioned, immutable-once-published question.

Workflow A only.

Contains:

* statement;
* type;
* options;
* correct answer;
* explanation;
* image;
* subject;
* difficulty;
* tags.

### Relationships

* optional `parent_id` for versioning;
* `created_by`;
* 0..N Skills through `question_skills`.

### Does not

* reference an Exam directly;
* contain exam-specific `question_number`;
* contain exam-specific `weight`.

Exam composition occurs through `ExamQuestion`.

---

## 2.5 ExamQuestion

**Status:** New entity.

**Responsibility:** Composition join between a bank Question and an Exam.

Exists only in Workflow A.

### Fields

* `exam_id`;
* `question_id`;
* `display_order`;
* `weight`.

### Behavior

At publication:

```text
ExamQuestion
      │
      ▼
AnswerKeyItem
```

The `ExamQuestion` remains as provenance after publication.

Grading does not use `ExamQuestion`.

---

## 2.6 Skill

**Status:** Preserved with light refactor.

**Responsibility:** SEDU/BNCC competency or skill code.

Can be attached independently to:

* Question Bank questions;
* AnswerKeyItems.

### Relationships

```text
Question
  └── question_skills
        └── Skill

AnswerKeyItem
  └── answer_key_item_skills
        └── Skill
```

The AnswerKeyItem relationship is intentionally a publication-time snapshot.

---

## 2.7 Attempt

**Status:** Refactored.

**Responsibility:** One student's execution of one Exam.

Supports:

* OMR execution;
* future online execution.

### Relationships

References:

* `exam_id`;
* `student_id`;
* `answer_key_id`;
* optional `omr_scan_id`.

### Lifecycle

Online:

```text
not_started
    │
    ▼
in_progress
    │
    ▼
submitted
    │
    ▼
graded
```

OMR:

```text
OMR confirmation
    │
    ▼
graded
```

The OMR path may skip intermediate online states because the scanned sheet represents completed evidence.

---

## 2.8 AttemptAnswer

**Status:** Refactored.

**Responsibility:** One student's response to one AnswerKeyItem.

### References

* `attempt_id`;
* `answer_key_item_id`;
* optional `question_id` for provenance.

The `answer_key_item_id` replaces positional grading based on:

```text
question_number
```

This is what allows Workflow B to operate without Question Bank rows.

---

## 2.9 OMRScan

**Status:** Preserved with behavior changes.

**Responsibility:** Scanned answer sheet and OMR engine output.

The scan is evidence of what the student marked.

It is not the source of truth for correct answers.

### Important distinction

```text
OMRScan.detected_answers
```

means:

> What the OMR engine detected on the student's sheet.

It does not mean:

> What the correct answer is.

Correct answers come exclusively from `AnswerKeyItem`.

---

## 2.10 OMRTemplate

**Status:** Refactored.

**Responsibility:** Physical sheet geometry and linkage to an Exam.

Contains:

* layout information;
* question count;
* options per question;
* title;
* active/deleted state.

Does not contain correct answers.

### Removed

```text
correct_answers JSONB
```

OMR grading resolves correct answers through:

```text
OMRScan
    ↓
OMRTemplate
    ↓
Exam
    ↓
AnswerKey
    ↓
AnswerKeyItem
```

In External Mode, creating an OMRTemplate first creates:

```text
Exam
AnswerKey
AnswerKeyItems
OMRTemplate
```

---

## 2.11 Grade

**Status:** Preserved.

**Responsibility:** Consolidated final score.

Uses polymorphic source references.

Possible sources:

```text
OMR
ONLINE
```

The existing shape is preserved.

---

## 2.12 User

**Status:** Preserved.

No target model changes.

---

## 2.13 Class / ClassStudent

**Status:** New, deferred.

The target model defines:

* `classes`;
* `class_students`.

However, their implementation is deferred.

Until Phase 4:

```text
Exam.class_id
```

remains a free string.

---

# 3. Target Entity Relationship Model

```text
                       ┌──────────────┐
                       │     User     │
                       │  (preserved) │
                       └──────┬───────┘
                              │
        ┌─────────────────────┼──────────────────────┐
        │                     │                      │
        ▼                     ▼                      ▼
  ┌──────────┐         ┌──────────┐           ┌──────────────┐
  │  Exam    │◄────────│ Teacher  │           │    Skill     │
  │          │  owns   │  (role)  │           │  (preserved) │
  └────┬─────┘         └──────────┘           └──────┬───────┘
       │ 1                                          │
       │                                            │
       │ 1                                          │
       ▼                                            │
  ┌──────────────┐    1     ┌──────────────────┐    │
  │  AnswerKey   │◄─────────│   ExamQuestion   │    │
  │    (NEW)     │ projects │   (NEW, WF-A)    │    │
  └──────┬───────┘          └────────┬─────────┘    │
         │ 1                         │ N             │
         │                           │               │
         │ N                         ▼               │
         ▼                  ┌──────────────────┐     │
  ┌──────────────────┐      │    Question      │◄────┤
  │ AnswerKeyItem    │─────►│  (Question Bank) │     │
  │      (NEW)       │ 0..1 │   (REFACTORED)   │     │
  └──────┬───────────┘      └────────┬─────────┘     │
         │                           │               │
         │ 0..N                      │ 0..N           │
         │                           │               │
         ▼                           ▼               │
  answer_key_item_skills       question_skills       │
         │                           │               │
         └───────────────┬───────────┘               │
                         ▼                           │
                       Skill ◄───────────────────────┘


  ┌──────────────────────────────────────────────────────────┐
  │              Execution / Grading Axis                   │
  │                                                          │
  │  Exam ──< Attempt ──< AttemptAnswer ──► AnswerKeyItem   │
  │            │                  │                          │
  │            │                  ├── answer_key_item_id     │
  │            │                  └── question_id (optional)│
  │            │                                             │
  │            ▼                                             │
  │         OMRScan                                           │
  │            ▲                                             │
  │            │                                             │
  │       OMRTemplate                                         │
  │            │                                             │
  │            └─► Exam ──► AnswerKey                         │
  │                                                          │
  │  Attempt / OMRScan ──► Grade                             │
  └──────────────────────────────────────────────────────────┘
```

## 3.1 Key Relationships

| From            | To            | Type            | Meaning                                  |
| --------------- | ------------- | --------------- | ---------------------------------------- |
| Exam            | AnswerKey     | 1:1             | Every Exam has exactly one canonical key |
| AnswerKey       | AnswerKeyItem | 1:N             | Key's graded slots                       |
| AnswerKeyItem   | Question      | N:0..1          | Optional back-reference to bank Question |
| AnswerKeyItem   | Skill         | N:N             | Direct skill attachment                  |
| Question        | Skill         | N:N             | Bank skill attachment                    |
| Exam            | ExamQuestion  | 1:N             | Workflow A composition                   |
| ExamQuestion    | Question      | N:1             | Selected bank Question                   |
| Exam            | Attempt       | 1:N             | Student executions                       |
| Attempt         | AttemptAnswer | 1:N             | Per-item responses                       |
| AttemptAnswer   | AnswerKeyItem | N:1             | Graded slot being answered               |
| Attempt         | OMRScan       | 1:0..1          | OMR evidence                             |
| OMRTemplate     | Exam          | 1:0..1          | Physical sheet linked to Exam            |
| Attempt/OMRScan | Grade         | via `source_id` | Consolidated score                       |

---

# 4. Elimination of Answer-Key Duplication

## 4.1 Current defect

The current model has two possible sources for correct answers:

```text
OMRTemplate.correct_answers
    JSONB
        │
        └── source A

Question.correct_option
    per-row
        │
        └── source B
```

This creates a synchronization problem.

The current grading and statistics paths can read from different representations.

For example:

```text
OMRService._calculate_score
    → OMRTemplate.correct_answers

ExamService.get_exam_statistics
    → Question.correct_option
```

These values can diverge.

---

## 4.2 Target model

The only canonical source is:

```text
AnswerKeyItem.correct_answer
```

Consumers read from:

```text
AnswerKeyItem.correct_answer
```

### OMR grading

```text
OMRScan
 → OMRTemplate
 → Exam
 → AnswerKey
 → AnswerKeyItem
```

### Online grading

```text
Attempt
 → Exam
 → AnswerKey
 → AnswerKeyItem
```

### Statistics

```text
Exam
 → AnswerKey
 → AnswerKeyItem
```

### Exports

```text
Exam
 → AnswerKey
 → AnswerKeyItem
```

---

## 4.3 Removed sources

The following are removed as canonical answer sources:

* `OMRTemplate.correct_answers`;
* exam-bound `questions.correct_option`.

---

## 4.4 Preserved evidence

The following remain, but are not answer-key sources:

```text
OMRScan.detected_answers
```

This represents the OMR engine's detected student responses.

```text
AttemptAnswer.selected_answer
```

This represents the student's selected response.

---

# 5. Existing Data Migration

For each existing `Exam`:

1. Create one `AnswerKey`.
2. For each existing exam-bound `questions` row, ordered by `question_number`, create one `AnswerKeyItem`.

The canonical answer during migration is:

```sql
COALESCE(
    omr_templates.correct_answers[question_number],
    questions.correct_option
)
```

The OMR template value is preferred because it was the grading source in the existing implementation.

### Migration mapping

```text
item_number
    ← questions.question_number

correct_answer
    ← COALESCE(
         omr_templates.correct_answers[question_number],
         questions.correct_option
       )

weight
    ← questions.weight

statement
    ← questions.statement

question_id
    ← NULL
```

Legacy exam-bound Questions are not considered Question Bank entities.

Their data is migrated into AnswerKeyItems.

For existing `AttemptAnswer` rows:

```text
attempt
    → exam
    → answer_key
    → answer_key_item
```

The matching `AnswerKeyItem` is found by:

```text
answer_key_item.item_number
    =
attempt_answers.question_number
```

The resulting `AnswerKeyItem.id` becomes:

```text
attempt_answers.answer_key_item_id
```

---

# 6. Entity Disposition Matrix

Classification:

* **Preserved** — keep as-is;
* **Refactored** — same table, schema changes;
* **New** — create;
* **Renamed** — same data, new name;
* **Replaced** — old table migrated/recreated;
* **Deferred** — defined but not implemented in the first migration batch.

| Entity                   | As-built table         | Disposition           | Target table             | Notes                                  |
| ------------------------ | ---------------------- | --------------------- | ------------------------ | -------------------------------------- |
| User                     | `users`                | Preserved             | `users`                  | No change                              |
| Skill                    | `skills`               | Preserved             | `skills`                 | SEDU structure in Phase 2              |
| `question_skills`        | `question_skills`      | Preserved             | `question_skills`        | References refactored bank Question    |
| Exam                     | `exams`                | Refactored            | `exams`                  | Add lifecycle and online-target fields |
| AnswerKey                | None                   | New                   | `answer_keys`            | 1:1 with Exam                          |
| AnswerKeyItem            | None                   | New                   | `answer_key_items`       | Canonical answer source                |
| `answer_key_item_skills` | None                   | New                   | `answer_key_item_skills` | N:N skill relationship                 |
| Question                 | Exam-bound `questions` | Replaced → Refactored | `questions`              | Legacy rows preserved separately       |
| ExamQuestion             | None                   | New                   | `exam_questions`         | Workflow A composition                 |
| Attempt                  | `attempts`             | Refactored            | `attempts`               | Add AnswerKey and lifecycle references |
| AttemptAnswer            | `attempt_answers`      | Refactored            | `attempt_answers`        | Add AnswerKeyItem reference            |
| OMRTemplate              | `omr_templates`        | Refactored            | `omr_templates`          | Remove `correct_answers`               |
| OMRScan                  | `omr_scans`            | Preserved             | `omr_scans`              | Behavior changes only                  |
| Grade                    | `grades`               | Preserved             | `grades`                 | No change                              |
| Class                    | None                   | New, deferred         | `classes`                | Phase 4                                |
| ClassStudent             | None                   | New, deferred         | `class_students`         | Phase 4                                |
| SecurityEvent            | None                   | New, deferred         | `security_events`        | Phase 7                                |
| AuditLog                 | None                   | New, deferred         | `audit_logs`             | Phase 7 or earlier if required         |

---

# 7. Target Field-Level Schemas

Only entities that change or are introduced are defined here.

---

## 7.1 `exams`

```text
id                    UUID PK
title                 VARCHAR(255) NOT NULL
description           TEXT
teacher_id            UUID FK users(id) RESTRICT
class_id              VARCHAR(100)
omr_template_id       UUID FK omr_templates(id) SET NULL
status                VARCHAR(20) NOT NULL DEFAULT 'draft'
total_time_seconds    INTEGER
max_attempts          INTEGER NOT NULL DEFAULT 1
randomization_enabled BOOLEAN NOT NULL DEFAULT FALSE
max_score             NUMERIC(5,2) NOT NULL DEFAULT 10.00
is_active             BOOLEAN NOT NULL DEFAULT TRUE
deleted_at            TIMESTAMPTZ
created_at            TIMESTAMPTZ
updated_at            TIMESTAMPTZ
```

Valid `status` values:

```text
draft
published
archived
```

---

## 7.2 `answer_keys`

```text
id            UUID PK
exam_id       UUID FK exams(id) RESTRICT UNIQUE
is_published  BOOLEAN NOT NULL DEFAULT FALSE
published_at  TIMESTAMPTZ
created_at    TIMESTAMPTZ
updated_at    TIMESTAMPTZ
```

`exam_id UNIQUE` enforces the 1:1 relationship.

---

## 7.3 `answer_key_items`

```text
id              UUID PK
answer_key_id   UUID FK answer_keys(id) CASCADE
item_number     INTEGER NOT NULL
correct_answer  VARCHAR(50) NOT NULL
weight          NUMERIC(5,2) NOT NULL DEFAULT 1.00
statement       TEXT
question_id     UUID FK questions(id) SET NULL
created_at      TIMESTAMPTZ
updated_at      TIMESTAMPTZ
```

Constraint:

```text
UNIQUE(answer_key_id, item_number)
```

`correct_answer` may represent values such as:

```text
A
C
TRUE
```

The field may later accommodate structured answer types such as matching or essay responses.

---

## 7.4 `answer_key_item_skills`

```text
answer_key_item_id  UUID FK answer_key_items(id) CASCADE
skill_id            UUID FK skills(id) CASCADE

PRIMARY KEY (
    answer_key_item_id,
    skill_id
)
```

---

## 7.5 `questions`

The new `questions` table represents the Question Bank.

```text
id              UUID PK
parent_id       UUID FK questions(id) SET NULL
version         INTEGER NOT NULL DEFAULT 1
is_active       BOOLEAN NOT NULL DEFAULT TRUE
statement       TEXT NOT NULL
type            VARCHAR(30) NOT NULL
options         JSONB
correct_answer  JSONB NOT NULL
explanation     TEXT
image_url       TEXT
subject         VARCHAR(100)
difficulty      VARCHAR(30)
tags            TEXT[]
created_by      UUID FK users(id) RESTRICT
created_at      TIMESTAMPTZ
updated_at      TIMESTAMPTZ
```

Supported initial `type` values:

```text
multiple_choice
true_false
matching
essay
```

Removed from the legacy exam-bound model:

```text
exam_id
question_number
correct_option
weight
```

---

## 7.6 `exam_questions`

```text
id             UUID PK
exam_id        UUID FK exams(id) CASCADE
question_id    UUID FK questions(id) RESTRICT
display_order  INTEGER NOT NULL
weight         NUMERIC(5,2) NOT NULL
created_at     TIMESTAMPTZ
```

Constraint:

```text
UNIQUE(exam_id, question_id)
```

---

## 7.7 `attempts`

```text
id                   UUID PK
exam_id              UUID FK exams(id) RESTRICT
answer_key_id        UUID FK answer_keys(id) RESTRICT
student_id           UUID FK users(id) SET NULL
student_code         VARCHAR(5)
omr_scan_id          UUID FK omr_scans(id) SET NULL
attempt_number       INTEGER NOT NULL
status               VARCHAR(20) NOT NULL DEFAULT 'not_started'
source               VARCHAR(10) NOT NULL DEFAULT 'OMR'
total_questions      INTEGER NOT NULL DEFAULT 0
correct_answers      INTEGER NOT NULL DEFAULT 0
incorrect_answers    INTEGER NOT NULL DEFAULT 0
accuracy_percentage  NUMERIC(5,2) NOT NULL DEFAULT 0.00
raw_score            NUMERIC(5,2) NOT NULL DEFAULT 0.00
final_score          NUMERIC(5,2) NOT NULL DEFAULT 0.00
started_at           TIMESTAMPTZ
completed_at         TIMESTAMPTZ
created_at           TIMESTAMPTZ
updated_at           TIMESTAMPTZ
```

Valid `source` values:

```text
OMR
ONLINE
```

---

## 7.8 `attempt_answers`

```text
id                  UUID PK
attempt_id          UUID FK attempts(id) CASCADE
answer_key_item_id  UUID FK answer_key_items(id) RESTRICT
question_id         UUID FK questions(id) SET NULL
selected_answer     VARCHAR(50)
correct_option      VARCHAR(50)
is_correct          BOOLEAN NOT NULL DEFAULT FALSE
answered_at         TIMESTAMPTZ
created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
```

`question_number` is removed as the primary grading reference.

`answer_key_item_id` is the canonical grading reference.

`question_id` is retained only as optional provenance.

`correct_option` is an optional denormalized snapshot and may be removed if the implementation determines that the AnswerKeyItem is always safely available.

---

## 7.9 `omr_templates`

```text
id                    UUID PK
exam_id               UUID FK exams(id) SET NULL
title                 VARCHAR(255)
layout_version        VARCHAR(50) NOT NULL
total_questions       INTEGER NOT NULL
options_per_question  INTEGER NOT NULL DEFAULT 5
is_active             BOOLEAN NOT NULL DEFAULT TRUE
deleted_at            TIMESTAMPTZ
created_at            TIMESTAMPTZ
updated_at            TIMESTAMPTZ
```

Removed:

```text
correct_answers JSONB
```

---

# 8. Migration Strategy

Each migration must be independently verifiable and, where practical, independently reversible.

Data migrations should be separated from schema changes where practical.

Academic data must be preserved.

---

## Migration Batch 1 — Introduce AnswerKey Layer

Migration:

```text
XXXX_introduce_answer_keys.py
```

### Actions

1. Create `answer_keys`.
2. Create `answer_key_items`.
3. Create `answer_key_item_skills`.
4. Create `exam_questions`.
5. Backfill existing Exams.
6. Create one AnswerKey per existing Exam.
7. Create AnswerKeyItems from existing exam-bound Questions.

Existing Exams with graded Attempts receive:

```text
is_published = TRUE
```

### Safety

This batch is additive.

Existing application behavior remains unchanged.

The legacy paths continue to operate temporarily:

```text
omr_templates.correct_answers
questions.correct_option
```

The new tables are populated but not yet authoritative.

---

## Migration Batch 2 — Refactor Attempts

Migration:

```text
XXXX_refactor_attempts_to_answer_key.py
```

### Actions

Add:

```text
attempts.answer_key_id
attempts.attempt_number
attempts.source
attempt_answers.answer_key_item_id
attempt_answers.answered_at
```

Change:

```text
attempts.status
```

default to:

```text
not_started
```

Existing rows remain explicitly:

```text
graded
```

### Data migration

For every Attempt:

```text
attempt
 → exam
 → answer_key
```

Populate:

```text
attempts.answer_key_id
```

For every AttemptAnswer:

```text
attempt
 → answer_key
 → answer_key_item
```

Match:

```text
answer_key_item.item_number
=
attempt_answers.question_number
```

Populate:

```text
attempt_answers.answer_key_item_id
```

---

## Migration Batch 3 — Application Code Switch

No schema migration.

Update application code to:

* write `AnswerKey` and `AnswerKeyItem`;
* read correct answers from `AnswerKeyItem`;
* calculate OMR scores from `AnswerKeyItem`;
* calculate statistics from `AnswerKeyItem`;
* write `attempt_answers.answer_key_item_id`;
* stop using `omr_templates.correct_answers` for grading;
* stop using legacy `questions.correct_option` for grading.

The legacy columns remain temporarily but become stale and unread.

---

## Migration Batch 4 — Remove OMR Answer Duplication

Migration:

```text
XXXX_drop_omr_template_correct_answers.py
```

### Pre-check

Before dropping the column, verify that:

```text
omr_templates.correct_answers
```

does not disagree with:

```text
AnswerKeyItem.correct_answer
```

If disagreement exists:

* abort the migration;
* report the conflicting records.

Only after consistency is confirmed:

```text
DROP COLUMN omr_templates.correct_answers
```

---

## Migration Batch 5 — Repurpose Question Table

Migration:

```text
XXXX_repurpose_questions_to_bank.py
```

This is the highest-risk migration.

### Strategy

1. Rename:

```text
questions
→ questions_legacy
```

2. Preserve all legacy rows.
3. Create a new `questions` table using the Question Bank schema.
4. Do not automatically migrate legacy exam-bound rows into the new Question Bank.

Legacy exam-bound rows were answer-key items, not reusable Questions.

Their relevant data has already been migrated to:

```text
answer_key_items
```

### Optional future action

If a legacy row contains meaningful question content, a separate one-off migration or administrative process may seed the Question Bank.

This is not part of the core migration.

---

## Migration Batch 6 — Exam Lifecycle Fields

Migration:

```text
XXXX_add_exam_lifecycle_fields.py
```

Add:

```text
status
total_time_seconds
max_attempts
randomization_enabled
```

Existing Exams receive:

```text
status = published
```

because they are already in use.

Online-related fields remain inert until the online engine exists.

---

## Deferred Migrations

Not included in the first refactor:

* `classes`;
* `class_students`;
* `security_events`;
* `audit_logs`;
* SEDU skill structure refinement.

---

# 9. Recommended Implementation Order

---

## Step 1 — AnswerKey Foundation

Implement:

* `answer_keys`;
* `answer_key_items`;
* `answer_key_item_skills`;
* `exam_questions`.

Backfill existing data.

No behavior change.

### Definition of Done

* tables exist;
* existing Exams have AnswerKeys;
* existing answer-key data is migrated;
* tests remain green.

---

## Step 2 — Attempt References

Add:

* `attempts.answer_key_id`;
* `attempts.attempt_number`;
* `attempts.source`;
* `attempt_answers.answer_key_item_id`;
* `attempt_answers.answered_at`.

Backfill existing OMR attempts.

### Definition of Done

All graded Attempts resolve their AnswerKey.

All graded AttemptAnswers resolve their AnswerKeyItem.

---

## Step 3 — Switch Grading and Statistics

Update:

* OMR grading;
* OMR confirmation;
* statistics;
* exports;
* dashboard.

All must use `AnswerKeyItem`.

### Definition of Done

No active grading or statistics path depends on:

```text
omr_templates.correct_answers
questions.correct_option
```

---

## Step 4 — Remove OMR Answer Duplication

Drop:

```text
omr_templates.correct_answers
```

Only after consistency verification.

---

## Step 5 — Repurpose Question Bank

Rename:

```text
questions
→ questions_legacy
```

Create the new reusable Question Bank.

### Definition of Done

* bank table exists;
* legacy data remains preserved;
* legacy exam-bound Questions are not incorrectly treated as bank Questions.

---

## Step 6 — Workflow A

Implement:

```text
Question
  ↓
ExamQuestion
  ↓
Exam publish
  ↓
AnswerKeyItem
```

At publication:

* copy `correct_answer`;
* copy `statement`;
* preserve `question_id`;
* snapshot Skills.

Workflow B must continue working independently.

---

## Step 7 — Exam Lifecycle

Implement:

```text
draft
  ↓
published
  ↓
archived
```

Implement publication and immutability rules.

---

## Step 8 — Online Attempt Engine

Deferred until Steps 1–7 are complete and the product decision confirms that the online engine is in scope.

Use the existing unified model:

```text
Attempt
AttemptAnswer
AnswerKeyItem
Grade
```

Do not create a separate online grading model.

### Target behavior

* one-question-at-a-time delivery;
* autosave;
* `source = ONLINE`;
* `Grade.source_type = ONLINE`.

---

## Step 9 — Classes, Monitoring, Audit, LGPD

Deferred according to the broader roadmap.

Includes:

* `classes`;
* `class_students`;
* `security_events`;
* `audit_logs`;
* monitoring;
* LGPD-related infrastructure.

---

# 10. Invariants

The following invariants must be enforced through database constraints, service-layer validation, or both.

| #      | Invariant                                                                  | Enforcement                            |
| ------ | -------------------------------------------------------------------------- | -------------------------------------- |
| INV-1  | Every Exam has exactly one AnswerKey                                       | `answer_keys.exam_id UNIQUE` + service |
| INV-2  | Every AnswerKey has ≥1 AnswerKeyItem                                       | Publish validation                     |
| INV-3  | `AnswerKeyItem.correct_answer` is the only canonical correct-answer source | Remove duplicate answer fields         |
| INV-4  | A key used by a graded Attempt is immutable                                | Service validation + publication state |
| INV-5  | Workflow B uses `question_id = NULL`                                       | Service validation                     |
| INV-6  | Workflow A requires non-null `question_id`                                 | Publish/projection validation          |
| INV-7  | Graded AttemptAnswers have non-null `answer_key_item_id`                   | DB constraint                          |
| INV-8  | AttemptAnswer's AnswerKeyItem belongs to Attempt's AnswerKey               | Service validation                     |
| INV-9  | `OMRTemplate.correct_answers` does not exist after migration               | Migration                              |
| INV-10 | `attempts.source ∈ {'OMR', 'ONLINE'}`                                      | CHECK constraint or enum               |
| INV-11 | Grade source resolves correctly according to `source_type`                 | Service validation                     |
| INV-12 | Question versions follow parent/version rules                              | Service versioning                     |
| INV-13 | Inactive Questions cannot be added to new Exams                            | Service filter                         |
| INV-14 | Published AnswerKeyItems preserve their original Question version          | Immutable `question_id`                |
| INV-15 | Dashboard and statistics work with zero Question rows                      | Queries use AnswerKeyItem              |

---

# 11. Lifecycle Contracts

---

## 11.1 AnswerKey Lifecycle

```text
Exam created
    │
    ▼
AnswerKey created
is_published = FALSE
    │
    ├── Items mutable
    │
    ▼
publish
    │
    ├── validate ≥1 item
    ├── validate publication rules
    └── set is_published = TRUE
    │
    ▼
Published
    │
    ├── Items immutable
    └── Attempts may use the key
    │
    ▼
First graded Attempt
    │
    ▼
Locked
    ├── no item edits
    └── no unpublish
```

---

## 11.2 Attempt Lifecycle

### Online

```text
not_started
    ↓
in_progress
    ↓
submitted
    ↓
graded
```

### OMR

```text
OMR confirmation
    ↓
Attempt(status = graded)
```

The OMR flow may skip intermediate states because the scan represents completed evidence.

---

## 11.3 Exam Lifecycle

```text
draft
    ↓ publish
published
    ↓ archive
archived
```

An Exam may return to `draft` only if no Attempt exists.

An Exam with any Attempt cannot return to `draft`.

`archived` is a soft terminal state.

Historical data is preserved.

---

## 11.4 OMRScan Lifecycle

```text
processing
    ├──► success
    ├──► review_needed
    │       └──► success
    └──► failed
```

The existing OMRScan lifecycle is otherwise preserved.

---

# 12. Read-Path Contracts

After the refactor, the following are the canonical read paths.

| Consumer                | Reads                                        | Path                                                       |
| ----------------------- | -------------------------------------------- | ---------------------------------------------------------- |
| OMR grading             | `AnswerKeyItem.correct_answer`               | `OMRScan → OMRTemplate → Exam → AnswerKey → AnswerKeyItem` |
| OMR confirmation        | `AnswerKeyItem.id` and answer                | Same path                                                  |
| Per-question statistics | `AnswerKeyItem` + `AttemptAnswer`            | `Exam → AnswerKey → AnswerKeyItem`                         |
| Per-skill statistics    | `AnswerKeyItem` + `answer_key_item_skills`   | `AnswerKeyItem → Skill`                                    |
| Exports                 | AnswerKey and Attempt data                   | `Exam → AnswerKey → AnswerKeyItem`                         |
| Dashboard               | AnswerKeyItem, Skill, Attempt, AttemptAnswer | AnswerKey-centered queries                                 |
| Online grading          | `AnswerKeyItem.correct_answer`               | `Attempt → Exam → AnswerKey → AnswerKeyItem`               |
| Workflow A projection   | Question data                                | `ExamQuestion → Question`                                  |

### Critical rule

No grading, statistics, export, or dashboard query may read the Question Bank.

The `questions` table is consulted only for:

1. Question Bank management;
2. Workflow A publication-time projection.

---

# 13. Workflow A — End-to-End Data Flow

```text
1. Teacher creates Question

questions
  ├── parent_id = NULL
  ├── version = 1
  ├── is_active = TRUE
  ├── statement
  ├── type
  ├── options
  ├── correct_answer
  └── skills via question_skills

2. Teacher creates Exam

exams
  ├── status = draft
  └── teacher_id

3. Teacher composes Exam

exam_questions
  ├── exam_id
  ├── question_id
  ├── display_order
  └── weight

4. Teacher publishes Exam

Validate publication rules.

Create AnswerKey.

For each ExamQuestion:

  Question.correct_answer
      ↓
  AnswerKeyItem.correct_answer

  Question.statement
      ↓
  AnswerKeyItem.statement

  Question.id
      ↓
  AnswerKeyItem.question_id

  Question.skills
      ↓
  answer_key_item_skills

5. Printed path

AnswerKey
    ↓
OMRTemplate
    ↓
PDF
    ↓
Student fills sheet
    ↓
OMRScan
    ↓
confirm
    ↓
Attempt(graded, source=OMR)
    ↓
AttemptAnswers
    ↓
Grade

6. Future online path

Attempt
    ↓
AttemptAnswer
    ↓
AnswerKeyItem
    ↓
Grade(source_type=ONLINE)
```

---

# 14. Workflow B — End-to-End Data Flow

```text
1. Teacher creates external Exam

Exam
  └── status = draft

2. Teacher creates AnswerKey manually

AnswerKey
  └── is_published = FALSE

3. Teacher creates AnswerKeyItems

item 1:
  correct_answer = A
  question_id = NULL

item 2:
  correct_answer = C
  question_id = NULL

item 3:
  correct_answer = B
  question_id = NULL

item 4:
  correct_answer = E
  question_id = NULL

4. Optional skill assignment

answer_key_item_skills
  ├── item 1 → Skill Z
  └── item 3 → Skill Z

5. Teacher publishes Exam

Validate publication rules.

Set:

AnswerKey.is_published = TRUE

6. Printed path

AnswerKey
    ↓
OMRTemplate
    ↓
PDF
    ↓
Student fills sheet
    ↓
OMRScan
    ↓
confirm
    ↓
Attempt
    ↓
AttemptAnswers
    ↓
Grade

7. Dashboard

Statistics use:

AnswerKeyItem
AttemptAnswer
answer_key_item_skills

No Question Bank rows are required.
```

---

# 15. Verification Requirements

## Workflow B

An Exam with:

* one AnswerKey;
* one or more AnswerKeyItems;
* zero Question rows;

must support:

* correct OMR grading;
* per-question statistics;
* per-skill statistics;
* exports;
* dashboard rendering.

---

## Workflow A

An Exam composed from:

* Question Bank;
* ExamQuestion;

must successfully project into:

* AnswerKey;
* AnswerKeyItems;
* AnswerKeyItem Skills.

It must support:

* grading;
* statistics;
* exports;
* dashboard rendering.

---

# 16. Summary of Changes

## Preserved

* `users`;
* `skills`;
* `question_skills`;
* `omr_scans`;
* `grades`;
* OMR engine pipeline;
* authentication;
* RBAC;
* JWT cookie strategy;
* unified Grade model.

---

## Refactored

### `exams`

Add:

* lifecycle fields;
* online-target fields.

### `attempts`

Add:

* `answer_key_id`;
* `attempt_number`;
* `source`.

### `attempt_answers`

Add:

* `answer_key_item_id`;
* `answered_at`.

### `omr_templates`

Remove:

```text
correct_answers
```

---

## Newly Created

* `answer_keys`;
* `answer_key_items`;
* `answer_key_item_skills`;
* `exam_questions`;
* new reusable `questions` Question Bank table.

---

## Deferred

* `classes`;
* `class_students`;
* `security_events`;
* `audit_logs`;
* SEDU skill structure refinement;
* online attempt engine.

---

# 17. Risk Register

| Risk                                                               | Severity | Mitigation                                                                                               |
| ------------------------------------------------------------------ | -------- | -------------------------------------------------------------------------------------------------------- |
| `grades.source_id` is polymorphic and may dangle                   | Medium   | Periodic integrity checks                                                                                |
| Legacy AnswerKeyItem loses Question provenance                     | Low      | Legacy data is test data; acceptable                                                                     |
| Repurposing `questions` is risky                                   | High     | Perform last; preserve `questions_legacy`                                                                |
| Attempt status default changes                                     | Low      | Existing rows explicitly remain `graded`                                                                 |
| Removing `omr_templates.correct_answers` breaks integrations       | Low      | No known external integrations in MVP; document breaking change                                          |
| Online fields are inert before online engine                       | Low      | Additive migration                                                                                       |
| `answer_key_item_skills` duplicates `question_skills` conceptually | Medium   | Intentional: Question skills are live bank metadata; AnswerKeyItem skills are publication-time snapshots |

---

# 18. Definition of Done

The domain-model refactor is complete when all conditions below are satisfied.

1. `AnswerKey` and `AnswerKeyItem` tables exist and are populated for all existing Exams.
2. `omr_templates.correct_answers` has been removed.
3. No application code references `omr_templates.correct_answers`.
4. The legacy exam-bound `questions` table has been preserved as `questions_legacy`.
5. A new reusable Question Bank `questions` table exists.
6. `attempt_answers.answer_key_item_id` is populated for all graded Attempts.
7. `answer_key_item_id` is the sole grading reference for AttemptAnswers.
8. `exam_questions` exists.
9. Workflow A projection is implemented.
10. Workflow B works with zero Question Bank rows.
11. Workflow B supports grading, statistics, skill analytics, exports, and dashboard rendering.
12. Workflow A supports grading, statistics, skill analytics, exports, and dashboard rendering.
13. INV-1 through INV-15 are enforced and covered by tests.
14. No grading, statistics, export, or dashboard query depends on `questions` or `questions_legacy`.
15. The existing OMR end-to-end flow continues to work.
16. Regression tests remain green.

---

# 19. Implementation Guardrails

The implementation agent must follow these rules.

### 19.1 Do not redesign the model

This document is the authoritative target domain model unless a concrete implementation contradiction is discovered.

If an unavoidable contradiction is found:

1. stop the affected implementation step;
2. report the contradiction;
3. identify the affected entities/migrations;
4. propose the smallest necessary design decision;
5. do not silently change the architecture.

### 19.2 Implement incrementally

Do not implement the entire refactor in one uncontrolled migration.

Follow the implementation order in Section 9.

Each step must be:

* independently testable;
* migration-safe;
* verifiable;
* documented in the implementation report.

### 19.3 Preserve existing data

No academic or test data may be silently deleted.

Legacy exam-bound Question rows must be preserved as:

```text
questions_legacy
```

before the new Question Bank table is created.

### 19.4 Preserve OMR functionality

The existing OMR pipeline must continue to work throughout the migration.

The target architecture changes where correct answers are stored, not the physical OMR processing engine.

### 19.5 Do not implement deferred features prematurely

The following remain outside the immediate domain-model refactor:

* online attempt delivery;
* classes;
* class membership;
* security event monitoring;
* audit logs;
* expanded SEDU skill structure.

They may consume the target model later but should not expand the current migration scope.

---

# 20. Final Target Architecture

The target domain model establishes the following central principle:

```text
                         ┌───────────────┐
                         │     Exam      │
                         └───────┬───────┘
                                 │ 1:1
                                 ▼
                         ┌───────────────┐
                         │   AnswerKey   │
                         │ SOURCE OF     │
                         │ TRUTH         │
                         └───────┬───────┘
                                 │ 1:N
                                 ▼
                       ┌───────────────────┐
                       │  AnswerKeyItem    │
                       │                   │
                       │ correct_answer    │
                       │ weight            │
                       │ statement         │
                       │ question_id?      │
                       └─────────┬─────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
                 ▼                               ▼
       Workflow A provenance              Workflow B
                 │                               │
                 ▼                               ▼
            Question                        No Question
          Question Bank                    Bank required
                 │                               │
                 └───────────────┬───────────────┘
                                 │
                                 ▼
                         Unified Grading
                                 │
                 ┌───────────────┼───────────────┐
                 ▼               ▼               ▼
               OMR            ONLINE         Statistics
                 │               │               │
                 └───────────────┼───────────────┘
                                 ▼
                              Grade
```

The architectural invariant is:

> **Every assessment is graded against exactly one AnswerKey, and every correct answer used for grading is stored in exactly one canonical location: `AnswerKeyItem.correct_answer`.**

Questions are optional.

The Question Bank is a producer of AnswerKeys in Workflow A.

Manual AnswerKeys are a first-class producer in Workflow B.

OMR and future online delivery are consumers of the same AnswerKey-centered grading model.

This is the target architecture that subsequent implementation work must follow.

# Step 1 Post-Implementation Audit

**Audit date:** 2026-07-27
**Auditor:** Lead Software Architect (independent audit)
**Implementation reviewed:** Step 1 — AnswerKey Foundation
**Method:** Direct inspection of all implementation files, git diffs, migration code, tests, and test execution

---

## 1. Executive Summary

The Step 1 implementation is **structurally sound and scope-compliant**. Four new tables (`answer_keys`, `answer_key_items`, `answer_key_item_skills`, `exam_questions`) were created with correct schemas matching `TARGET_DOMAIN_MODEL.md`. No existing application code (services, routes, schemas, repositories, or existing models) was modified. The existing OMR flow remains untouched. The 20 new tests pass, and all 40 collectible existing tests pass (6 pre-existing collection errors due to missing `openpyxl` are unrelated).

However, the audit identified **two critical divergences** between the Alembic migration (raw SQL, production path) and the ORM backfill module (tested path). These divergences mean the passing tests do **not** fully prove the production migration is correct. The most serious issue: the migration's Scenario B can crash with a UNIQUE constraint violation if an exam has multiple OMR templates with `correct_answers` — a scenario the ORM backfill handles safely but the migration does not.

Additionally, the **Alembic migration has never been executed against PostgreSQL**. The tests verify the backfill *logic* (via ORM on SQLite) but not the migration *SQL* (raw SQL on PostgreSQL). This is a known limitation (Phase 0 issue P-11) that was correctly documented by the implementation agent.

**Verdict: APPROVED WITH CONDITIONS.** The implementation is safe to commit and proceed to Step 2 *after* the two critical migration divergences (A-01, A-02) are fixed. The PostgreSQL execution gap is a non-blocking limitation for this step but must be addressed before Step 3's code switch.

---

## 2. Implementation Reviewed

| Artifact | Path | Status |
|---|---|---|
| AnswerKey model | `backend/app/models/answer_key.py` | NEW — untracked |
| ExamQuestion model | `backend/app/models/exam_question.py` | NEW — untracked |
| Backfill service | `backend/app/services/backfill.py` | NEW — untracked |
| Alembic migration | `backend/alembic/versions/a1b2c3d4e5f6_introduce_answer_keys.py` | NEW — untracked |
| Backfill tests | `backend/tests/test_answer_key_backfill.py` | NEW — untracked |
| Models `__init__` | `backend/app/models/__init__.py` | MODIFIED — tracked |
| DB meta | `backend/app/db/meta.py` | MODIFIED — tracked |

No git commit was made by the implementation agent. All files are in the working tree (untracked + modified).

---

## 3. Files and Git Changes Inspected

### Modified tracked files (2)

| File | Change | Scope compliant? |
|---|---|---|
| `backend/app/models/__init__.py` | Added imports for `AnswerKey`, `AnswerKeyItem`, `answer_key_item_skills`, `ExamQuestion` | ✔ Yes |
| `backend/app/db/meta.py` | Expanded imports to include all models (was stale — only had 4 models) | ✔ Yes |

### New untracked files (5)

| File | Purpose |
|---|---|
| `backend/app/models/answer_key.py` | `AnswerKey`, `AnswerKeyItem`, `answer_key_item_skills` table |
| `backend/app/models/exam_question.py` | `ExamQuestion` model |
| `backend/app/services/backfill.py` | ORM-based backfill logic (testable mirror of migration) |
| `backend/alembic/versions/a1b2c3d4e5f6_introduce_answer_keys.py` | Alembic migration (schema + raw SQL backfill) |
| `backend/tests/test_answer_key_backfill.py` | 20 tests covering backfill logic, model structure, and regression |

### Files NOT modified (verified)

| File | Verified untouched? |
|---|---|
| `backend/app/models/exam.py` | ✔ |
| `backend/app/models/question.py` | ✔ |
| `backend/app/models/attempt.py` | ✔ |
| `backend/app/models/omr.py` | ✔ |
| `backend/app/models/skill.py` | ✔ |
| `backend/app/models/user.py` | ✔ |
| `backend/app/models/grade.py` | ✔ |
| `backend/app/services/omr.py` | ✔ |
| `backend/app/services/exam.py` | ✔ |
| `backend/app/services/export.py` | ✔ |
| `backend/app/services/omr_engine.py` | ✔ |
| `backend/app/api/routes/*` | ✔ |
| `backend/app/schemas/*` | ✔ |
| `backend/app/repositories/*` | ✔ |
| Existing migrations (`0001`, `8c7e7c2e4e00`, `9a8f7b6c5d4e`) | ✔ |

---

## 4. Definition of Done Verification

| # | Requirement | Status | Evidence | Risk |
|---|---|---|---|---|
| 1 | `answer_keys`, `answer_key_items`, `answer_key_item_skills`, `exam_questions` exist with intended schema | **PASS** | Migration creates all 4 tables with correct columns, FKs, unique constraints. Models match migration. Tests verify table existence via `inspect()`. | Low |
| 2 | Existing Exams receive exactly one AnswerKey where required | **PASS WITH LIMITATION** | ORM backfill tested (idempotency test passes). Migration's raw SQL has a potential duplicate-key issue (A-01) if multiple templates exist per exam. | Medium |
| 3 | AnswerKeys receive correct AnswerKeyItems | **PASS** | Tests verify item count, item_number, correct_answer values for all scenarios. | Low |
| 4 | OMR Templates with `correct_answers` are correctly migrated | **PASS WITH LIMITATION** | ORM backfill tested. Migration uses `IS NOT NULL` which diverges from Python truthiness for empty dicts `{}` (A-02). | Medium |
| 5 | Orphan OMR Templates without Exam are materialized into Exam + AnswerKey | **PASS** | Tests verify materialization, teacher_id inference, template linking, AnswerKey creation. Error case (no teacher) tested. | Low |
| 6 | Correct-answer precedence is correct (OMR template preferred over questions) | **PASS** | Test `test_exam_with_omr_uses_template_correct_answers` verifies OMR template wins over `questions.correct_option`. | Low |
| 7 | Legacy `questions` data remains untouched | **PASS** | `question.py` not modified; migration only reads from `questions`, never writes or deletes. | None |
| 8 | `omr_templates.correct_answers` remains available | **PASS** | `omr.py` not modified; migration does not drop column; tests verify `correct_answers` still works. | None |
| 9 | Existing OMR grading behavior remains unchanged | **PASS** | No service/route/schema modified. Legacy read paths untouched. Regression tests in `TestExistingOMRFlowUnchanged` pass. | None |
| 10 | No Step 2/Step 3 behavior accidentally introduced | **PASS** | No attempt columns added; no grading switch; no `correct_answers` removal; no `questions` repurpose. | None |
| 11 | Alembic migration ordering and FKs are correct | **PASS** | Revision `a1b2c3d4e5f6` → `down_revision: 9a8f7b6c5d4e`. Linear chain. FKs verified. Single head. | Low |
| 12 | Migration is safe for PostgreSQL | **NOT VERIFIED** | Migration never executed against PostgreSQL. Raw SQL uses standard SQL (`INSERT`, `UPDATE`, `SELECT`) compatible with PostgreSQL. `sa.UUID()` is valid for PostgreSQL. | Medium |
| 13 | Downgrade behavior is understood and safe | **PASS WITH LIMITATION** | Downgrade drops 4 new tables. Materialized Exams for orphan templates are NOT removed (documented in migration docstring). `omr_templates.exam_id` links remain valid (Exams not dropped). | Low |
| 14 | Test strategy provides meaningful coverage | **PASS** | 20 tests cover model structure, all 4 backfill scenarios, idempotency, completeness, regression, and edge cases. | Low |
| 15 | SQLite-specific test behavior not treated as PostgreSQL proof | **PASS** | Test file explicitly documents the P-11 limitation. Tests verify ORM backfill logic, not migration SQL. | Low |

---

## 5. Migration Audit

### 5.1 Revision chain

```
0001_create_users → 8c7e7c2e4e00 → 9a8f7b6c5d4e → a1b2c3d4e5f6 (HEAD)
```

✔ Linear, single head, correct `down_revision`.

### 5.2 Table creation order

1. `answer_keys` (depends on `exams`) ✔
2. `answer_key_items` (depends on `answer_keys`, `questions`) ✔
3. `answer_key_item_skills` (depends on `answer_key_items`, `skills`) ✔
4. `exam_questions` (depends on `exams`, `questions`) ✔

✔ Order is correct — all dependency tables exist before dependents.

### 5.3 Schema verification

| Table | Column | Type | Nullable | FK / Constraint | Matches model? |
|---|---|---|---|---|---|
| `answer_keys` | `id` | UUID | NO | PK | ✔ |
| | `exam_id` | UUID | NO | FK→exams RESTRICT, UNIQUE | ✔ |
| | `is_published` | Boolean | NO | default false | ✔ |
| | `published_at` | DateTime(tz) | YES | — | ✔ |
| | `created_at` | DateTime(tz) | NO | server_default now() | ✔ |
| | `updated_at` | DateTime(tz) | NO | server_default now() | ✔ |
| `answer_key_items` | `id` | UUID | NO | PK | ✔ |
| | `answer_key_id` | UUID | NO | FK→answer_keys CASCADE | ✔ |
| | `item_number` | Integer | NO | — | ✔ |
| | `correct_answer` | String(50) | NO | — | ✔ |
| | `weight` | Numeric(5,2) | NO | server_default 1.00 | ✔ |
| | `statement` | String | YES | — | ✔ |
| | `question_id` | UUID | YES | FK→questions SET NULL | ✔ |
| | `created_at`, `updated_at` | DateTime(tz) | NO | server_default now() | ✔ |
| | — | — | — | UNIQUE(answer_key_id, item_number) | ✔ |
| `answer_key_item_skills` | `answer_key_item_id` | UUID | NO | FK→answer_key_items CASCADE, PK | ✔ |
| | `skill_id` | UUID | NO | FK→skills CASCADE, PK | ✔ |
| `exam_questions` | `id` | UUID | NO | PK | ✔ |
| | `exam_id` | UUID | NO | FK→exams CASCADE | ✔ |
| | `question_id` | UUID | NO | FK→questions RESTRICT | ✔ |
| | `display_order` | Integer | NO | — | ✔ |
| | `weight` | Numeric(5,2) | NO | — | ✔ |
| | `created_at`, `updated_at` | DateTime(tz) | NO | server_default now() | ✔ |
| | — | — | — | UNIQUE(exam_id, question_id) | ✔ |

### 5.4 Downgrade

Drops tables in reverse dependency order: `exam_questions` → `answer_key_item_skills` → `answer_key_items` → `answer_keys`. ✔ Correct order.

Materialized Exams (from orphan templates) are NOT dropped — documented in migration docstring. This is acceptable: the Exams are valid records, and dropping them would require tracking which Exams were created by the migration. The `omr_templates.exam_id` links remain valid because the Exams still exist.

### 5.5 PostgreSQL compatibility

| Aspect | Compatible? | Notes |
|---|---|---|
| `sa.UUID()` | ✔ | PostgreSQL native UUID type |
| `sa.text("now()")` | ✔ | PostgreSQL `now()` function |
| `sa.Boolean()` server_default `"false"` | ✔ | PostgreSQL boolean literal |
| Raw SQL `INSERT`/`UPDATE`/`SELECT` | ✔ | Standard SQL, no PostgreSQL-specific syntax |
| `correct_answers IS NOT NULL` | ✔ | Works on JSON column in PostgreSQL |
| `str(uuid)` for UUID parameters | ✔ | PostgreSQL accepts string UUID representation |
| Transaction safety | ✔ | Alembic wraps `upgrade()` in a transaction; partial failure rolls back |

### 5.6 Migration NOT executed against PostgreSQL

The migration file exists and is syntactically correct, but it has **never been run** against a PostgreSQL database in this environment. The `alembic.ini` points to `localhost:5432` but no PostgreSQL instance is running in this session. This is a **verification gap**, not a code defect.

---

## 6. Backfill Logic Audit

### 6.1 Algorithm overview

The backfill handles four scenarios in order:

| Scenario | Source | Condition | Action |
|---|---|---|---|
| A | `omr_templates.correct_answers` | `exam_id IS NULL` | Materialize Exam + AnswerKey + Items |
| B | `omr_templates.correct_answers` | `exam_id IS NOT NULL`, no existing AnswerKey | Create AnswerKey + Items from template |
| C | `questions.correct_option` | Exam has questions, no AnswerKey yet | Create AnswerKey + Items from questions (COALESCE with template if available) |
| D | `attempts.status = 'graded'` | Any AnswerKey for exams with graded attempts | Set `is_published = TRUE` |

### 6.2 Precedence rule

**OMR template `correct_answers` is preferred over `questions.correct_option`.** This is correct per Phase 0 analysis — the OMR template was the grading truth.

Verified by test `test_exam_with_omr_uses_template_correct_answers`: template says Q1=A, questions says Q1=B → AnswerKeyItem gets A. ✔

### 6.3 Idempotency

Both the migration and the ORM backfill check `NOT EXISTS (SELECT 1 FROM answer_keys ...)` before creating. Running twice does not create duplicates. Test `test_backfill_is_idempotent` verifies this. ✔

### 6.4 Key format handling

Both migration and ORM backfill handle keys in both `"1"` and `"q1"` formats via `int(str(key).replace("q", "").replace("Q", ""))`. ✔ Matches the defensive code in `omr.py:263` and `exam.py:156`.

### 6.5 Items with NULL correct answers

Both migration and ORM backfill skip items where `correct_answer` cannot be determined (both template and question have no answer). ✔ Safe behavior.

---

## 7. Orphan OMR Template Audit (P-01 / P-03)

### 7.1 Materialization flow

```
Orphan OMRTemplate (correct_answers exists, exam_id IS NULL)
    ↓
Resolve teacher_id: first active TEACHER, fallback first active ADMIN
    ↓
If no teacher/admin found: ABORT with RuntimeError (safe)
    ↓
Create Exam (title, teacher_id, omr_template_id, total_questions, max_score=10.00)
    ↓
UPDATE omr_templates SET exam_id = new_exam.id
    ↓
Create AnswerKey (exam_id, is_published=FALSE)
    ↓
Create AnswerKeyItems from correct_answers dict
```

### 7.2 teacher_id inference

| Aspect | Status | Notes |
|---|---|---|
| Strategy | ✔ | First active TEACHER by `created_at`; fallback first active ADMIN |
| NULL teacher_id | ✔ Prevented | `Exam.teacher_id` is NOT NULL; migration aborts if no user found |
| Deterministic? | ⚠ Partially | Deterministic within a single run (ORDER BY created_at). But if multiple teachers exist, the "first" one may not be the intended owner. This is an acceptable limitation for a data migration — the Exam can be re-assigned later. |
| Production safety | ✔ | Aborts cleanly with descriptive error if no teacher exists. No silent failure. |

### 7.3 P-03 compatibility

The materialization ensures that every orphan template with `correct_answers` will have an Exam + AnswerKey after this migration. This is the prerequisite for Step 3's removal of implicit Exam creation from `confirm_scan`. ✔ Compatible.

### 7.4 Edge case: orphan template with `correct_answers = {}` (empty dict)

- **ORM backfill:** `if t.correct_answers` → `{}` is falsy → **skipped**. No Exam materialized.
- **Migration:** `WHERE correct_answers IS NOT NULL` → `{}` is NOT NULL → **picked up**. Exam materialized with empty AnswerKey (0 items).

This is a **divergence** (see Issue A-02). The migration would create an Exam + AnswerKey with zero items for a template with `correct_answers = {}`. While unlikely in practice (the OMR template creation flow always populates `correct_answers` with at least one entry), it is a behavioral difference between tested and production code.

---

## 8. PostgreSQL vs SQLite Verification

| Verification level | Status | Evidence |
|---|---|---|
| ORM backfill logic verified on SQLite | ✔ DONE | 20 tests pass on SQLite in-memory |
| Alembic migration structure statically inspected | ✔ DONE | Revision chain, table schemas, FKs, constraints all verified by reading the migration file |
| Alembic migration executed against PostgreSQL | ❌ NOT DONE | No PostgreSQL instance available in this session |
| Upgrade successfully executed on PostgreSQL | ❌ NOT DONE | — |
| Downgrade successfully executed on PostgreSQL | ❌ NOT DONE | — |
| Production-like data migration verified | ❌ NOT DONE | — |
| Raw SQL syntax reviewed for PostgreSQL compatibility | ✔ DONE | Standard SQL, no PostgreSQL-specific operators, `sa.UUID()` valid |

**Conclusion:** The backfill *algorithm* is verified. The migration *SQL* is inspected but not executed. This is a known limitation (P-11) correctly documented by the implementation agent.

---

## 9. Test Coverage Audit

### 9.1 Test inventory (20 tests)

| Class | Test | Scenario | Passes? |
|---|---|---|---|
| `TestAnswerKeyModelStructure` | `test_answer_key_table_exists` | Table creation | ✔ |
| | `test_answer_key_items_table_exists` | Table creation | ✔ |
| | `test_answer_key_item_skills_table_exists` | Table creation | ✔ |
| | `test_exam_questions_table_exists` | Table creation | ✔ |
| | `test_answer_key_has_unique_exam_id` | 1:1 constraint | ✔ |
| | `test_answer_key_item_unique_constraint` | UNIQUE(item_number) | ✔ |
| `TestBackfillOrphanTemplates` | `test_orphan_template_gets_materialized_exam` | Scenario A | ✔ |
| | `test_orphan_template_answer_key_has_items` | Scenario A items | ✔ |
| | `test_orphan_template_without_teacher_raises` | Scenario A error | ✔ |
| `TestBackfillExamWithOMR` | `test_exam_with_omr_template_gets_answer_key` | Scenario B | ✔ |
| | `test_exam_with_omr_uses_template_correct_answers` | Precedence | ✔ |
| `TestBackfillExamWithQuestionsOnly` | `test_exam_with_questions_no_template_gets_answer_key` | Scenario C | ✔ |
| | `test_exam_with_questions_and_template_without_correct_answers` | Scenario C fallback | ✔ |
| `TestBackfillPublishedFlag` | `test_graded_attempt_marks_key_as_published` | Scenario D | ✔ |
| `TestBackfillIdempotency` | `test_backfill_is_idempotent` | Idempotency | ✔ |
| `TestBackfillCompleteness` | `test_every_exam_with_data_gets_answer_key` | Completeness | ✔ |
| `TestExistingOMRFlowUnchanged` | `test_omr_template_creation_still_works` | Regression | ✔ |
| | `test_exam_creation_with_questions_still_works` | Regression | ✔ |
| | `test_answer_key_item_skills_relationship_works` | Skill attachment | ✔ |
| | `test_exam_question_table_works` | ExamQuestion | ✔ |

### 9.2 Coverage gaps

| Gap | Severity | Notes |
|---|---|---|
| No test for multiple OMR templates per exam | High | This is the scenario that causes migration Issue A-01 |
| No test for `correct_answers = {}` (empty dict) | Medium | This is the divergence A-02 |
| No test for the actual Alembic migration SQL | Medium | P-11 limitation — known and documented |
| No test for transaction rollback on migration failure | Low | Alembic handles this; not testable in SQLite |
| No test for `question_id` provenance on AnswerKeyItem | Low | All items are created with `question_id=NULL` (correct for Step 1) |
| No test verifying `answer_key_items.question_id` FK to `questions` | Low | FK exists in schema; not tested because Step 1 sets it to NULL |

---

## 10. Data Integrity Assessment

| Check | Status | Notes |
|---|---|---|
| Duplicate AnswerKeys | ✔ Prevented | UNIQUE(exam_id) constraint + idempotency logic |
| Empty AnswerKeys | ⚠ Possible in migration | If `correct_answers = {}`, migration creates AnswerKey with 0 items. ORM backfill skips this case. (A-02) |
| Missing AnswerKeyItems | ✔ Prevented | Items created from `correct_answers` dict or `questions` rows |
| Incorrect item numbering | ✔ Prevented | `int(str(key).replace("q","").replace("Q",""))` handles both formats |
| Invalid correct_answers keys | ✔ Handled | Non-parseable keys are skipped (try/except) |
| NULL correct answers | ✔ Handled | Items with no determinable correct answer are skipped |
| Mismatch total_questions vs items | ⚠ Not checked | Migration does not verify that item count matches `total_questions`. Acceptable — `total_questions` is the sheet capacity, not the key item count. |
| Duplicate item numbers | ✔ Prevented | UNIQUE(answer_key_id, item_number) constraint |
| Existing Attempts/Grades affected | ✔ Not affected | Migration only creates new rows; reads existing data but does not modify it |
| Teacher ownership for materialized Exams | ⚠ Inferred | First teacher by created_at. May not be the intended owner. Acceptable for migration. |
| Transaction safety | ✔ Safe | Alembic wraps in transaction; partial failure rolls back |

---

## 11. Scope Compliance

| Scope rule | Status | Evidence |
|---|---|---|
| No OMR grading switch to AnswerKeyItem | ✔ | `omr.py` not modified |
| No `omr_templates.correct_answers` removal | ✔ | `omr.py` not modified; migration does not drop column |
| No `questions` table rename/repurpose | ✔ | `question.py` not modified |
| No Attempt/AttemptAnswer structure change | ✔ | `attempt.py` not modified |
| No Workflow A implementation | ✔ | `exam_questions` table created but empty; no projection logic |
| No Exam lifecycle behavior | ✔ | No `status` field added to `exams`; no publish action |
| No service/route/schema modifications | ✔ | Verified by `git diff --name-only` — only `__init__.py` and `meta.py` modified in backend |

**Scope compliance: PASS.**

---

## 12. Issues Found

### A-01 — Migration Scenario B can crash on multiple templates per exam

| Field | Value |
|---|---|
| **ID** | A-01 |
| **Severity** | Critical |
| **File** | `backend/alembic/versions/a1b2c3d4e5f6_introduce_answer_keys.py` |
| **Location** | `_backfill_answer_keys()`, Scenario B (line ~259) |
| **Problem** | The SQL query `SELECT e.id, ... FROM exams e JOIN omr_templates t ON t.exam_id = e.id WHERE t.correct_answers IS NOT NULL AND NOT EXISTS (SELECT 1 FROM answer_keys ak WHERE ak.exam_id = e.id)` fetches all matching rows at once. If an exam has 2+ OMR templates with `correct_answers`, the loop processes both rows. The first creates an AnswerKey; the second attempts to create another AnswerKey for the same `exam_id`, violating the UNIQUE constraint. |
| **Impact** | Migration crashes with `IntegrityError: duplicate key value violates unique constraint "uq_answer_keys_exam_id"`. The entire migration rolls back. |
| **Recommendation** | Add a Python-side deduplication in the migration loop: track processed `exam_id`s in a set, skip if already processed. This mirrors the ORM backfill's `existing_ak_set` pattern. |

### A-02 — Migration and ORM backfill diverge on `correct_answers = {}` (empty dict)

| Field | Value |
|---|---|
| **ID** | A-02 |
| **Severity** | Critical |
| **File** | `backend/alembic/versions/a1b2c3d4e5f6_introduce_answer_keys.py` |
| **Location** | `_backfill_answer_keys()`, Scenarios A and B SQL queries |
| **Problem** | The migration uses `WHERE correct_answers IS NOT NULL` which is true for `{}` (empty JSON object). The ORM backfill uses `if t.correct_answers` which is false for `{}`. This means: (1) the migration picks up templates with `correct_answers = {}` and creates AnswerKeys with 0 items; (2) the tested ORM backfill skips them. The tests therefore do not prove the migration's behavior for this case. |
| **Impact** | In production, if any `omr_templates.correct_answers` contains `{}`, the migration creates an empty AnswerKey (0 items). This is not catastrophic (the AnswerKey exists but is empty), but it is a behavioral difference from what was tested. More importantly, it violates the spirit of "tests prove the migration." |
| **Recommendation** | Change the migration SQL to also filter out empty dicts. In PostgreSQL, this can be done with: `WHERE correct_answers IS NOT NULL AND correct_answers::text != '{}'::text`. Alternatively, add a Python-side check in the migration loop: `if not correct_answers: continue`. |

### A-03 — `answer_key_items.statement` type mismatch: model uses `String`, migration uses `String`

| Field | Value |
|---|---|
| **ID** | A-03 |
| **Severity** | Low |
| **File** | `backend/app/models/answer_key.py` line 87; migration line 86 |
| **Location** | `statement` column definition |
| **Problem** | The model defines `statement: Mapped[Optional[str]] = mapped_column(String, nullable=True)` and the migration uses `sa.Column("statement", sa.String(), nullable=True)`. Both use `String` without a length. In PostgreSQL, `String` without length maps to `TEXT`, which is fine. In the existing `questions` table, `statement` is also `String` (migration `9a8f7b6c5d4e`). This is consistent. No actual issue. |
| **Impact** | None. |
| **Recommendation** | No action needed. Documented for completeness. |

### A-04 — `ExamQuestion` model has `updated_at` from `BaseModel` but the entity is immutable in practice

| Field | Value |
|---|---|
| **ID** | A-04 |
| **Severity** | Low |
| **File** | `backend/app/models/exam_question.py` |
| **Location** | Class definition inherits `BaseModel` |
| **Problem** | `ExamQuestion` inherits `BaseModel` which provides `created_at` and `updated_at`. The `updated_at` column has `onupdate=func.now()`. For an immutable composition join, `updated_at` is unnecessary. However, this is consistent with all other models in the project and matches the migration. |
| **Impact** | None — cosmetic concern only. |
| **Recommendation** | No action needed. Consistent with project conventions. |

### A-05 — No PostgreSQL migration execution verification

| Field | Value |
|---|---|
| **ID** | A-05 |
| **Severity** | Medium (non-blocking for Step 1) |
| **File** | N/A (environment limitation) |
| **Location** | N/A |
| **Problem** | The Alembic migration has never been executed against PostgreSQL. The tests verify the ORM backfill logic on SQLite, not the migration SQL on PostgreSQL. |
| **Impact** | Migration SQL bugs (like A-01) cannot be caught by the current test suite. |
| **Recommendation** | Execute `alembic upgrade head` and `alembic downgrade -1` against a PostgreSQL instance (Docker) before Step 3. For Step 1, the static inspection is sufficient given the additive-only nature. |

### A-06 — No git commit was made

| Field | Value |
|---|---|
| **ID** | A-06 |
| **Severity** | Low (process) |
| **File** | N/A |
| **Location** | N/A |
| **Problem** | The implementation agent did not create a git commit. All files are in the working tree as untracked/modified. |
| **Impact** | The implementation is not persisted. A clean checkout would lose the work. |
| **Recommendation** | Commit the implementation with a descriptive message after fixing A-01 and A-02. |

---

## 13. Required Fixes Before Step 2

### Blockers (must fix before commit and Step 2)

1. **A-01 — Migration Scenario B duplicate-key crash:** Add Python-side deduplication in the migration's Scenario B loop. Track processed `exam_id`s in a set; skip if already processed. This is a 3-line fix in the migration's `_backfill_answer_keys()` function.

2. **A-02 — Migration `correct_answers = {}` divergence:** Add a Python-side check `if not correct_answers: continue` in the migration's Scenario A and B loops, OR change the SQL to filter empty dicts. This ensures the migration matches the tested ORM backfill behavior.

### Recommended fixes (should fix but non-blocking)

3. **A-05 — PostgreSQL migration execution:** Execute the migration against a PostgreSQL instance (Docker Compose) to verify the raw SQL works. This can be done after the commit but before Step 3.

4. **A-06 — Git commit:** Commit the implementation after fixing A-01 and A-02.

### Non-blocking observations

5. **A-03, A-04** — No action needed. Documented for completeness.

---

## 14. Final Verdict

### **APPROVED WITH CONDITIONS**

The Step 1 implementation is structurally correct, scope-compliant, and well-tested for the ORM backfill logic. The new tables match `TARGET_DOMAIN_MODEL.md`. No existing behavior was modified.

However, **two critical fixes (A-01, A-02) must be applied to the Alembic migration** before committing and before proceeding to Step 2. These fixes ensure the production migration SQL matches the tested backfill logic.

**Conditions for proceeding to Step 2:**
1. Fix A-01 (add deduplication in migration Scenario B loop).
2. Fix A-02 (add empty-dict check in migration Scenarios A and B).
3. Commit the implementation.
4. (Recommended but not blocking) Execute the migration against PostgreSQL to verify.

---

## 15. Recommended Next Action

The implementation agent should:

1. **Fix A-01 and A-02** in `backend/alembic/versions/a1b2c3d4e5f6_introduce_answer_keys.py`:
   - In Scenario A loop: add `if not correct_answers: continue` after fetching `correct_answers`.
   - In Scenario B loop: add `if not correct_answers: continue` after fetching `correct_answers`, and add a `processed_exam_ids = set()` to skip exams already processed.
   - In Scenario B loop: add `if exam_id in processed_exam_ids: continue` and `processed_exam_ids.add(exam_id)` after creating each AnswerKey.
2. **Add a test** for the multiple-templates-per-exam scenario in `test_answer_key_backfill.py`.
3. **Run the full test suite** to confirm no regressions.
4. **Commit** with message `feat: introduce answer key foundation (Step 1)`.
5. **(Recommended)** Execute `alembic upgrade head` and `alembic downgrade -1` against the Docker PostgreSQL instance.
6. **Stop** — do not proceed to Step 2 without explicit instruction.

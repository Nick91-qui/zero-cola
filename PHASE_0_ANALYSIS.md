# COLA-ZERO — Phase 0 Pre-Implementation Analysis & Execution Plan

**Date:** 2026-07-27
**Basis:** Direct inspection of `backend/app/`, `backend/alembic/versions/`, `backend/tests/` against `TARGET_DOMAIN_MODEL.md`
**Scope:** Analysis only. No files modified.

---

## 1. Executive Summary

The as-built COLA-ZERO backend is a working OMR answer-key + grading + statistics system with 44 pytest functions (SQLite-backed) and 3 Alembic migrations (PostgreSQL). It is functionally coherent for Workflow B (external exam → answer key → OMR → grade), but the domain model is **structurally wrong** for the target: correct answers are duplicated across `omr_templates.correct_answers` (JSONB) and `questions.correct_option` (per-row), the `questions` table is an exam-bound answer-key item (not a reusable bank), and `AttemptAnswer` grades by positional `question_number` rather than by a stable key-item reference.

`TARGET_DOMAIN_MODEL.md` is technically sound and its 6-batch migration strategy is feasible, but it contains **5 concrete problems** that would cause migration failures or OMR breakage if implemented as written. The most serious: (1) Batch 1 backfills `answer_key_items` from `questions` but ignores `omr_templates.correct_answers` rows that exist for OMR-only exams with **zero** `questions` rows — producing empty answer keys and breaking grading; (2) the Batch 5 `questions → questions_legacy` rename will break `attempt_answers.question_id` (FK to `questions`) and the `question_skills` join unless both are detached first; (3) the 1:1 `Exam ↔ AnswerKey` cannot be enforced by `UNIQUE(exam_id)` alone if `answer_keys` is created *before* the `exam_id` FK target is stable.

The recommended first milestone is **narrow and safe**: introduce `answer_keys`, `answer_key_items`, `answer_key_item_skills`, and `exam_questions` as additive tables, backfill them from **both** `questions` and `omr_templates.correct_answers` (preferring the OMR source), wire no reads yet, and keep all existing OMR flows untouched. This is independently shippable, reversible, and leaves the OMR pipeline 100% functional.

---

## 2. Dependency Map

Every reference to the entities/fields that the refactor touches, verified by global grep across `app/` and `tests/`.

| # | Component | File | Current Usage | Affected Entity/Field | Refactoring Impact | Required Action |
|---|---|---|---|---|---|---|
| 1 | `OMRTemplate.correct_answers` | `app/models/omr.py:31` | Column definition (JSON, nullable) | `omr_templates.correct_answers` | Removed in Batch 4 | Add to legacy model until drop |
| 2 | `OMRTemplate.correct_answers` | `app/schemas/omr.py:18` | Pydantic field `OMRTemplateBase.correct_answers` | `omr_templates.correct_answers` | Schema changes | Make optional → remove after Batch 4 |
| 3 | `OMRTemplate.correct_answers` | `app/repositories/omr.py:19` | `create()` writes `correct_answers=template_in.correct_answers` | `omr_templates.correct_answers` | Write path changes | Stop writing; write to `AnswerKeyItem` instead |
| 4 | `OMRTemplate.correct_answers` | `app/services/omr.py:155,161` | `_calculate_score` reads `template.correct_answers` | `omr_templates.correct_answers` | **Core grading read** | Switch to `AnswerKeyItem` via `template→exam→answer_key` |
| 5 | `OMRTemplate.correct_answers` | `app/services/omr.py:262-263` | `confirm_scan` reads `template.correct_answers.get(q_str_i) or .get(q_key_i)` | `omr_templates.correct_answers` | **Core confirm read** | Switch to `AnswerKeyItem` |
| 6 | `OMRTemplate.correct_answers` | `app/services/exam.py:156` | `get_exam_statistics` fallback `template.correct_answers.get(f"q{i}")` | `omr_templates.correct_answers` | Statistics fallback | Switch to `AnswerKeyItem` only |
| 7 | `OMRTemplate.correct_answers` | `tests/test_omr_models.py:15,24` | Creates/asserts `correct_answers={"1":"A"}` | `omr_templates.correct_answers` | Test breakage | Update tests to use `AnswerKeyItem` |
| 8 | `OMRTemplate.correct_answers` | `tests/test_omr_service.py:22,32,54,93` | Creates templates with `correct_answers` | `omr_templates.correct_answers` | Test breakage | Update tests |
| 9 | `OMRTemplate.correct_answers` | `tests/test_omr_api.py:68,137` | API payload `correct_answers` | `omr_templates.correct_answers` | Test breakage | Update tests |
| 10 | `Question.correct_option` | `app/models/question.py:20` | Column (String(10), nullable) | `questions.correct_option` | Migrated to `answer_key_items.correct_answer` | Remove from bank `Question` |
| 11 | `Question.correct_option` | `app/schemas/exam.py:14,73` | `QuestionBase.correct_option`, `QuestionStatistic.correct_option` | `questions.correct_option` | Schema changes | Replace with `AnswerKeyItem.correct_answer` |
| 12 | `Question.correct_option` | `app/repositories/exam.py:91` | `create_questions_bulk` writes `correct_option=correct_opt` | `questions.correct_option` | Write path changes | Write to `AnswerKeyItem` instead |
| 13 | `Question.correct_option` | `app/services/exam.py:154-155` | `get_exam_statistics` reads `q_model.correct_option` | `questions.correct_option` | **Core stats read** | Switch to `AnswerKeyItem` |
| 14 | `Question.correct_option` | `app/services/exam.py:189` | Stats dict key `"correct_option"` | `questions.correct_option` | Output shape | Rename to `correct_answer` (cosmetic) |
| 15 | `Question.exam_id` | `app/models/question.py:15-17` | FK `exams.id` CASCADE, NOT NULL | `questions.exam_id` | Removed in bank model | Migrate to `answer_key_items.answer_key_id` |
| 16 | `Question.exam_id` | `app/services/exam.py:147` | `Question.exam_id == exam_id` filter | `questions.exam_id` | **Core stats query** | Switch to `AnswerKey→AnswerKeyItem` |
| 17 | `Question.question_number` | `app/models/question.py:18` | Column (Integer, NOT NULL) | `questions.question_number` | Migrated to `answer_key_items.item_number` | Remove from bank model |
| 18 | `Question.question_number` | `app/services/exam.py:147,152` | `order_by(question_number)`, `q.question_number == i` | `questions.question_number` | Stats loop | Switch to `AnswerKeyItem.item_number` |
| 19 | `Question` (model import) | `app/models/__init__.py:6` | Re-exported | `Question` | Repurposed | Keep name; schema changes |
| 20 | `Question` (model import) | `app/repositories/exam.py:9` | Imported for `create_questions_bulk` | `Question` | Repo changes | Replace with `AnswerKeyItem` repo |
| 21 | `Question` (model import) | `app/services/exam.py:12` | Imported for stats query | `Question` | Service changes | Replace with `AnswerKeyItem` |
| 22 | `Question.skills` | `app/models/question.py:24` | `relationship("Skill", secondary="question_skills")` | `question_skills` | Preserved for bank | Add `answer_key_item_skills` parallel |
| 23 | `Question.skills` | `app/services/exam.py:185-189` | Stats reads `q_model.skills` | `question_skills` | Stats reads bank skills | Switch to `answer_key_item_skills` |
| 24 | `Exam.questions` | `app/models/exam.py:30` | `relationship("Question", back_populates="exam")` | `Exam↔Question` | Removed | Add `Exam.answer_key` relationship |
| 25 | `Exam.questions` | `tests/test_exam_service.py:34` | `assert len(exam.questions) == 3` | `Exam↔Question` | Test breakage | Assert on `answer_key.items` |
| 26 | `ExamDetailResponse.questions` | `app/schemas/exam.py:67` | Response includes `questions: List[QuestionResponse]` | `Exam↔Question` | Schema changes | Replace with `answer_key_items` |
| 27 | `ExamDetailResponse.questions` | `app/api/routes/exams.py:42` | `get_exam` returns detail with questions | `Exam↔Question` | Route changes | Update response model |
| 28 | `Exam.total_questions` | `app/models/exam.py:26` | Column (Integer, default 20) | `exams.total_questions` | Duplicated on Attempt/Template | Keep but derive from `AnswerKeyItem` count |
| 29 | `Exam.total_questions` | `app/services/exam.py:141` | `range(1, exam.total_questions + 1)` | `exams.total_questions` | Stats loop bound | Derive from `AnswerKeyItem` count |
| 30 | `Exam.omr_template_id` | `app/models/exam.py:22-24` | FK `omr_templates.id` SET NULL | `Exam↔OMRTemplate` circular | Circular FK (Issue P-04) | Keep; document |
| 31 | `Attempt.question_number` | `app/models/attempt.py:51` | Column (Integer, NOT NULL) | `attempt_answers.question_number` | Replaced by `answer_key_item_id` | Add new col, backfill, then remove |
| 32 | `Attempt.question_number` | `app/repositories/attempt.py:53` | `create_answers_bulk` writes `question_number=item["question_number"]` | `attempt_answers.question_number` | Write path | Write `answer_key_item_id` instead |
| 33 | `Attempt.question_number` | `app/services/omr.py:270` | `confirm_scan` builds `{"question_number": i}` | `attempt_answers.question_number` | Confirm write | Resolve `AnswerKeyItem` by `item_number` |
| 34 | `Attempt.question_number` | `app/services/exam.py:163` | `AttemptAnswer.question_number == i` filter | `attempt_answers.question_number` | Stats query | Switch to `answer_key_item_id` |
| 35 | `Attempt.correct_option` | `app/models/attempt.py:57` | Column (String(10), nullable) | `attempt_answers.correct_option` | Denormalized snapshot | Keep as snapshot or drop per spec |
| 36 | `Attempt.correct_option` | `app/repositories/attempt.py:56` | `create_answers_bulk` writes `correct_option=item.get("correct_option")` | `attempt_answers.correct_option` | Write path | Snapshot from `AnswerKeyItem` |
| 37 | `Attempt.correct_option` | `app/services/omr.py:272` | `confirm_scan` builds `{"correct_option": correct_opt}` | `attempt_answers.correct_option` | Confirm write | Snapshot from `AnswerKeyItem` |
| 38 | `Attempt.selected_option` | `app/models/attempt.py:56` | Column (String(10), nullable) | `attempt_answers.selected_option` | Renamed `selected_answer` per spec | Rename or keep alias |
| 39 | `Attempt.selected_option` | `app/repositories/attempt.py:55` | `create_answers_bulk` writes | `attempt_answers.selected_option` | Write path | Rename |
| 40 | `Attempt.selected_option` | `app/services/omr.py:271` | `confirm_scan` builds `{"selected_option": selected_opt}` | `attempt_answers.selected_option` | Confirm write | Rename |
| 41 | `Attempt.selected_option` | `app/services/export.py:310` | PDF export reads `ans.get("selected_option")` | `attempt_answers.selected_option` | Export read | Rename |
| 42 | `Attempt.question_id` | `app/models/attempt.py:53-54` | FK `questions.id` SET NULL (provenance) | `attempt_answers.question_id` | Breaks on Batch 5 rename | Set NULL before rename |
| 43 | `Attempt.question_id` | `app/repositories/attempt.py:54` | `create_answers_bulk` writes `question_id=item.get("question_id")` | `attempt_answers.question_id` | Write path | Keep as provenance |
| 44 | `Attempt.status` default | `app/models/attempt.py:27` | `default="graded"` | `attempts.status` | Changes to `not_started` | Backfill existing as `graded` |
| 45 | `ExamCreate.correct_answers` | `app/schemas/exam.py:42` | Input field for exam creation | `omr_templates.correct_answers` | Input shape changes | Accept answer-key items instead |
| 46 | `ExamCreate.correct_answers` | `app/services/exam.py:37,45,62,65` | `create_exam` creates template+questions from `correct_answers` | `omr_templates.correct_answers` + `questions` | **Core creation flow** | Create `AnswerKey`+`AnswerKeyItem` instead |
| 47 | `ExamCreate.correct_answers` | `app/repositories/exam.py:82-91` | `create_questions_bulk` parses `correct_answers` dict | `questions` | Repo method | Replace with `AnswerKeyItem` creation |
| 48 | `ExamCreate.correct_answers` | `tests/test_exam_service.py:25,50` | Tests pass `correct_answers` | `omr_templates.correct_answers` | Test breakage | Update |
| 49 | `ExamCreate.correct_answers` | `tests/test_exam_api.py:15` | API test payload | `omr_templates.correct_answers` | Test breakage | Update |
| 50 | `question_skills` (table) | `app/models/skill.py:9-13` | `Table("question_skills", ...)` | `question_skills` | FK to `questions` | Will break on Batch 5 rename |
| 51 | `question_skills` | `app/models/question.py:24` | `secondary="question_skills"` | `question_skills` | Relationship | Re-point to new bank `questions` |
| 52 | `question_skills` | `app/models/skill.py:26` | `secondary=question_skills` | `question_skills` | Relationship | Re-point |
| 53 | `meta.py` | `app/db/meta.py:3` | Imports `Grade, OMRScan, OMRTemplate, User` only | metadata | Stale (missing Exam, Question, etc.) | Update imports |
| 54 | `BaseModel` PGUUID | `app/db/models.py:14` | `PGUUID(as_uuid=True)` PostgreSQL-specific | All models | SQLite tests rely on fallback | Flag — works but fragile |

**Summary of blast radius:** 14 source files + 6 test files reference the affected fields. The OMR flow has **4 critical read points** (rows 4, 5, 6, 13, 16) that must all switch atomically in Step 3.

---

## 3. End-to-End OMR Flow Audit

### 3.1 As-built flow (traced file-by-file)

```
[1] Exam creation
    File: app/api/routes/exams.py:13 (POST /exams)
    Service: app/services/exam.py:32 create_exam()
    Flow:
      - If exam_in.correct_answers provided AND no omr_template_id:
          creates OMRTemplate(layout_version, total_questions,
                              correct_answers=exam_in.correct_answers)   ← WRITE A
          [app/repositories/omr.py:19]
      - Creates Exam (teacher_id, class_id, omr_template_id, total_questions)
          [app/repositories/exam.py:13]
      - Links OMRTemplate.exam_id = exam.id (circular)                    ← CIRCULAR FK
      - If exam_in.correct_answers:
          create_questions_bulk(exam_id, correct_answers)                ← WRITE B (DUPLICATE)
          [app/repositories/exam.py:82]
          For each {"1":"A",...}: Question(exam_id, question_number=int("1"),
                                            correct_option="A", weight=1.00)
    Fields written: omr_templates.correct_answers, questions.correct_option,
                    questions.question_number, questions.exam_id, questions.weight
    DEPENDENCY: correct_answers is the input; both omr_templates and questions store it.

[2] OMRTemplate creation (standalone)
    File: app/api/routes/omr.py:18 (POST /omr/templates)
    Service: app/services/omr.py:43 create_template()
    Repo: app/repositories/omr.py:13 create()
    Writes: omr_templates.correct_answers (standalone, no exam)
    NOTE: This path creates NO questions rows. Only omr_templates.correct_answers exists.

[3] PDF generation
    File: app/api/routes/omr.py:54 (GET /omr/templates/{id}/pdf)
    Service: app/services/omr.py:62 get_template_pdf()
    Engine: app/services/omr_pdf.py generate_omr_pdf(layout_version, student_code)
    DEPENDENCY: Uses layout_version + student_code only. Does NOT read correct_answers.
    IMPACT: Unaffected by refactor.

[4] OMRScan upload
    File: app/api/routes/omr.py:74 (POST /omr/scans/upload)
    Service: app/services/omr.py:91 process_scan_upload()
    Flow:
      - Saves image to disk
      - Creates OMRScan(omr_template_id, image_url, status=processing)
      - OMREngine.process_image(file_bytes, layout_version)
          [app/services/omr_engine.py:131]
          → provider.detect(aligned) [app/core/omr_layouts.py:198]
          → returns {"student_code": "10234",
                      "detected_answers": {"1":"A","2":"B",...},   ← STRING KEYS
                      "raw_confidence": {...}}
      - Resolves student_id from student_code (User query)
      - _calculate_score(template, detected_answers)                     ← READ A (CRITICAL)
          [app/services/omr.py:153]
          Reads template.correct_answers, compares to detected_answers
      - Updates OMRScan with student_code, student_id, status, detected_answers,
        raw_confidence, score, error_message, processed_at
    DEPENDENCY: template.correct_answers is the grading truth here.

[5] OMRScan manual review
    File: app/api/routes/omr.py:107 (PATCH /omr/scans/{id})
    Service: app/services/omr.py:174 update_scan_manual()
    Flow:
      - If detected_answers updated: _calculate_score(template, answers)  ← READ B (CRITICAL)
      - Updates scan
    DEPENDENCY: template.correct_answers again.

[6] confirm_scan
    File: app/api/routes/omr.py:131 (POST /omr/scans/{id}/confirm)
    Service: app/services/omr.py:216 confirm_scan()
    Flow:
      - Validates scan.student_id and scan.score exist
      - Updates scan.status = SUCCESS
      - Finds Exam via template.exam_id; if none, CREATES Exam implicitly  ← SIDE EFFECT
          (Exam(title=template.title, teacher_id, omr_template_id, total_questions,
                max_score=10.00))
      - Loops i=1..template.total_questions:
          selected_opt = scan.detected_answers.get(str(i)) or .get(f"q{i}")
          correct_opt = template.correct_answers.get(str(i)) or .get(f"q{i}")  ← READ C (CRITICAL)
          is_correct = selected_opt == correct_opt
      - Creates Attempt(exam_id, student_id, student_code, omr_scan_id,
                        total_questions, correct_answers, incorrect_answers,
                        accuracy_percentage, raw_score, final_score, status="graded")
          [app/repositories/attempt.py:13]
      - Creates AttemptAnswer per item:
          {attempt_id, question_number=i, question_id=None,
           selected_option=selected_opt, correct_option=correct_opt, is_correct}
          [app/repositories/attempt.py:46]
          NOTE: question_id is ALWAYS None here (never set in confirm_scan)
      - Updates scan.score = final_score
      - Creates Grade(student_id, source_type=OMR, source_id=scan.id, score, teacher_id)
          [app/repositories/grade.py:13 create_or_update]
    DEPENDENCY: template.correct_answers is the grading truth. question_number is positional.

[7] Statistics
    File: app/api/routes/exams.py:84 (GET /exams/{id}/statistics)
    Service: app/services/exam.py:137 get_exam_statistics()
    Flow:
      - Queries Question.filter(exam_id).order_by(question_number)         ← READ D (CRITICAL)
      - Gets template via exam.omr_template_id
      - Loops i=1..exam.total_questions:
          q_model = questions where question_number==i
          correct_opt = q_model.correct_option OR
                        template.correct_answers.get(f"q{i}") or .get(str(i))  ← READ E (CRITICAL, DUAL SOURCE)
          answers_for_q = AttemptAnswer.join(Attempt)
                          .filter(exam_id, question_number==i)              ← READ F (CRITICAL)
          q_skills = q_model.skills                                         ← READ G (question_skills)
      - Returns per-question stats
    DEPENDENCY: reads BOTH questions.correct_option AND template.correct_answers
                with a fallback. This is the duplication in action.

[8] Export PDF
    File: app/api/routes/exams.py:101 (GET /exams/{id}/export/pdf)
    Service: app/services/exam.py:211 export_exam_pdf()
    Export: app/services/export.py:23 generate_exam_pdf_report()
    Flow: calls get_exam_statistics() then renders. Reads question_stats dict.
    DEPENDENCY: indirect via statistics.

[9] Export XLSX
    File: app/api/routes/exams.py:116 (GET /exams/{id}/export/xlsx)
    Service: app/services/exam.py:244 export_exam_xlsx()
    Export: app/services/export.py:168 generate_exam_xlsx_report()
    DEPENDENCY: indirect via statistics.
```

### 3.2 Target flow (after refactor)

```
[1] Exam creation
    Input: correct_answers dict (Workflow B) OR exam_questions (Workflow A)
    Flow:
      - Create Exam (status='draft')
      - Create AnswerKey(exam_id, is_published=FALSE)
      - For each correct_answer {"1":"A",...}:
          Create AnswerKeyItem(answer_key_id, item_number=1, correct_answer="A",
                                weight=1.00, statement=NULL, question_id=NULL)
      - Create OMRTemplate(exam_id, layout_version, total_questions) — NO correct_answers
    Single source: AnswerKeyItem.correct_answer

[2] OMRTemplate creation (standalone → External Mode)
    Flow:
      - Create Exam (implicit)
      - Create AnswerKey + AnswerKeyItems from input
      - Create OMRTemplate(exam_id, layout_version, total_questions)
    Single source: AnswerKeyItem.correct_answer

[3] PDF generation — UNCHANGED (layout + student_code only)

[4] OMRScan upload
    Flow:
      - Create OMRScan (unchanged)
      - OMREngine.process_image → detected_answers (unchanged, string keys)
      - Resolve student_id (unchanged)
      - _calculate_score: resolve AnswerKeyItems via
            template → exam → answer_key → answer_key_items (ordered by item_number)
            Compare detected_answers[str(item_number)] == answer_key_item.correct_answer
      - Update OMRScan (unchanged)

[5] Manual review — _calculate_score via AnswerKeyItem (same path as [4])

[6] confirm_scan
    Flow:
      - Find Exam via template.exam_id (no implicit creation if Exam already exists from [1]/[2])
      - Resolve AnswerKeyItems via exam → answer_key → answer_key_items
      - Loop over AnswerKeyItems (not range(1..total_questions)):
          item = answer_key_items[i]
          selected = scan.detected_answers.get(str(item.item_number))
          correct = item.correct_answer
          is_correct = selected == correct
          Create AttemptAnswer(attempt_id, answer_key_item_id=item.id,
                               question_id=item.question_id (provenance, may be NULL),
                               selected_answer=selected, correct_option=correct,
                               is_correct, answered_at=now)
      - Create Attempt (with answer_key_id, attempt_number, source='OMR', status='graded')
      - Create Grade (unchanged)

[7] Statistics
    Flow:
      - Resolve AnswerKeyItems via exam → answer_key → answer_key_items (ordered by item_number)
      - For each AnswerKeyItem:
          correct = item.correct_answer
          answers = AttemptAnswer.filter(answer_key_item_id == item.id)
          skills = item.skills via answer_key_item_skills
      - NO Question table read. NO omr_templates.correct_answers read.

[8][9] Exports — indirect via [7]. Question_stats dict shape unchanged (cosmetic renames only).
```

### 3.3 Flow continuity assessment

The OMR flow can remain continuous throughout migration **if and only if**:
- Steps 1–2 (additive tables) and Step 2 (attempt columns) are nullable-additive;
- Step 3 (code switch) updates **all 6 critical read points** (A–F above) in a single commit;
- `confirm_scan` resolves `AnswerKeyItem` by `item_number` matching `detected_answers` string keys (confirmed compatible — both use string integers);
- The `question_number` → `answer_key_item_id` backfill in Batch 2 uses `item_number` matching (confirmed: `questions.question_number` is an int, `detected_answers` keys are `str(int)`).

---

## 4. Migration Batch Validation

### Batch 1 — Introduce AnswerKey Layer

| Criterion | Assessment |
|---|---|
| Technically feasible | ⚠ **Yes, but incomplete as specified.** The spec backfills from `questions` only. As-built has OMR-only exams (created via `POST /omr/templates` without an Exam) where `omr_templates.correct_answers` exists but `questions` rows do NOT. These exams would get an empty `AnswerKey`, breaking grading after Step 3. |
| Ordering correct | ✔ Yes — additive, no reads yet. |
| Dependencies to change first | None. |
| Data-loss risk | None (additive). |
| OMR break risk | None (legacy paths still active). |
| FK issues | `answer_key_items.question_id` FK to `questions` — fine while legacy `questions` exists. `answer_keys.exam_id` FK to `exams` — fine. |
| Reversibility | ✔ Drop new tables. |
| Adjustment needed | **YES — see Issue P-01.** Backfill must handle two source patterns: (a) exams with `questions` rows; (b) `omr_templates` with `correct_answers` but no exam/questions. The canonical COALESCE must also cover the case where `questions` rows are absent and only `omr_templates.correct_answers` exists. |

### Batch 2 — Refactor Attempts

| Criterion | Assessment |
|---|---|
| Technically feasible | ✔ Yes. |
| Ordering correct | ✔ After Batch 1 (needs `answer_keys` and `answer_key_items` to exist for backfill). |
| Dependencies | Needs Batch 1's `answer_key_items` populated. |
| Data-loss risk | None (additive columns + backfill). |
| OMR break risk | None (new columns nullable, old code ignores them). |
| FK issues | `attempts.answer_key_id` FK to `answer_keys` — fine. `attempt_answers.answer_key_item_id` FK to `answer_key_items` — fine. |
| Reversibility | ✔ Drop columns. |
| Adjustment needed | **Minor — see Issue P-02.** `attempts.attempt_number` has no `NOT NULL` default for existing rows. Spec says "default 1 for existing rows" — the migration must `UPDATE attempts SET attempt_number = 1 WHERE attempt_number IS NULL` before adding `NOT NULL`. Also, `attempts.status` default change to `not_started` must not rewrite existing rows (they stay `graded`); only the column default changes. |

### Batch 3 — Application Code Switch

| Criterion | Assessment |
|---|---|
| Technically feasible | ✔ Yes. |
| Ordering correct | ✔ After Batch 2 (needs `answer_key_id` and `answer_key_item_id` populated). |
| Dependencies | All 6 critical read points must switch atomically. |
| Data-loss risk | None. |
| OMR break risk | **HIGH if any read point is missed.** The dependency map (§2) identifies all of them. |
| FK issues | None. |
| Reversibility | Code revert (no migration). |
| Adjustment needed | **See Issue P-03.** `confirm_scan` currently creates an Exam implicitly if `template.exam_id` is null. After refactor, the Exam + AnswerKey must already exist (created at template creation). The implicit-Exam-creation side-effect must be removed or adapted — otherwise Workflow B standalone templates will have no `AnswerKey` to grade against. |

### Batch 4 — Remove OMR Answer Duplication

| Criterion | Assessment |
|---|---|
| Technically feasible | ✔ Yes, after Step 3 verified. |
| Ordering correct | ✔ After Step 3. |
| Dependencies | No code reads `omr_templates.correct_answers`. |
| Data-loss risk | The column is dropped — data lost, but `AnswerKeyItem` is now truth. |
| OMR break risk | None if Step 3 complete. |
| FK issues | None. |
| Reversibility | ⚠ Downgrade re-adds column but data is gone. Acceptable per spec. |
| Adjustment needed | None. Pre-check for disagreement is good practice. |

### Batch 5 — Repurpose Question Table

| Criterion | Assessment |
|---|---|
| Technically feasible | ⚠ **No, not as specified.** Renaming `questions` → `questions_legacy` will break: (1) `attempt_answers.question_id` FK to `questions`; (2) `question_skills.question_id` FK to `questions`; (3) `answer_key_items.question_id` FK to `questions` (created in Batch 1). All three FKs point at `questions` and will dangle after rename. |
| Ordering correct | ✔ Last (after all code switched). |
| Dependencies | All FKs to `questions` must be neutralized first. |
| Data-loss risk | Low (legacy preserved as `questions_legacy`). |
| OMR break risk | None (OMR doesn't read `questions` after Step 3). |
| FK issues | **CRITICAL — see Issue P-05.** Three FKs break. |
| Reversibility | ✔ Rename back. |
| Adjustment needed | **YES.** Before renaming: (1) set `attempt_answers.question_id = NULL` for all rows (already NULL in practice — confirm_scan never sets it); (2) drop `question_skills` table or recreate it pointing at the new `questions`; (3) set `answer_key_items.question_id = NULL` for all legacy rows (already NULL per Batch 1 migration). Then rename `questions` → `questions_legacy`, then create new `questions`. |

### Batch 6 — Exam Lifecycle Fields

| Criterion | Assessment |
|---|---|
| Technically feasible | ✔ Yes. |
| Ordering correct | ✔ Anytime (additive, inert). Could even be Batch 1.5. |
| Dependencies | None. |
| Data-loss risk | None. |
| OMR break risk | None (fields inert until code uses them). |
| FK issues | None. |
| Reversibility | ✔ Drop columns. |
| Adjustment needed | None. |

---

## 5. Issues Found in TARGET_DOMAIN_MODEL.md

```
ID: P-01
Section: §5 (Existing Data Migration) and §8 Batch 1
Problem: The migration backfills AnswerKeyItems exclusively from the exam-bound
  `questions` table. However, the as-built system has a second creation path:
  `POST /omr/templates` (OMRService.create_template) creates an OMRTemplate with
  `correct_answers` but NO Exam and NO `questions` rows. Additionally, confirm_scan
  can create an Exam implicitly with NO `questions` rows (only the template has
  `correct_answers`). For these exams, the Batch 1 backfill produces an AnswerKey
  with zero items. After Step 3 switches grading to AnswerKeyItem, these exams
  become ungradable (score=0 for all scans).
Impact: OMR exams created via standalone template creation break silently after
  the code switch. Existing graded data is safe (Grade rows persist), but new
  scans against these templates produce zero scores.
Recommendation: Batch 1 backfill must enumerate `omr_templates.correct_answers`
  as a first-class source, not only `questions`. For each OMRTemplate with
  `correct_answers`:
    - If no Exam exists, create Exam + AnswerKey from the template.
    - If Exam exists but has no AnswerKey, create AnswerKey + items from
      COALESCE(template.correct_answers, questions.correct_option).
  The canonical COALESCE in §5 should be applied per-template, not per-question,
  with `omr_templates.correct_answers` as the preferred source (as the spec
  already states, but the procedure must explicitly cover the no-questions case).
```

```
ID: P-02
Section: §8 Batch 2 (attempts.attempt_number)
Problem: The spec adds `attempts.attempt_number INTEGER NOT NULL` but existing
  rows have no value. The spec says "default 1 for existing rows" in prose, but
  the field-level schema in §7.7 declares it `NOT NULL` with no default. Adding
  a NOT NULL column without a default to a non-empty table fails in PostgreSQL.
Impact: Batch 2 migration fails on existing data.
Recommendation: The migration must: (1) add the column nullable; (2) run
  `UPDATE attempts SET attempt_number = 1 WHERE attempt_number IS NULL`;
  (3) alter to NOT NULL. Same pattern for any other new NOT NULL column on a
  populated table (e.g., `attempts.source` should default 'OMR' via server_default
  + backfill, not just Python default).
```

```
ID: P-03
Section: §8 Batch 3 (Application Code Switch) and §2.10 OMRTemplate
Problem: The spec states that in External Mode, "creating an OMRTemplate first
  creates Exam, AnswerKey, AnswerKeyItems, OMRTemplate." The as-built
  `confirm_scan` (omr.py:230-242) creates an Exam lazily IF `template.exam_id`
  is null. After the refactor, grading reads `template → exam → answer_key →
  items`. If a standalone template was created (pre-refactor) and has no Exam,
  the refactored `confirm_scan` cannot grade. The spec's Batch 1 (per P-01) must
  create Exams for orphan templates, but the spec does not state this explicitly
  for the code-switch step.
Impact: Standalone templates created before the refactor, whose Exam was never
  materialized (because confirm_scan was never called), will have no AnswerKey
  after Batch 1 if P-01 is not addressed. The code switch then fails for them.
Recommendation: Make the Exam-materialization step explicit in Batch 1: every
  `omr_templates` row with `correct_answers` and null `exam_id` gets an Exam +
  AnswerKey materialized during backfill. The refactored `confirm_scan` may then
  assume `template.exam_id` is non-null.
```

```
ID: P-04
Section: §3.1 Key Relationships and §7.1/§7.9
Problem: The circular FK between `exams.omr_template_id` (FK → `omr_templates.id`,
  SET NULL) and `omr_templates.exam_id` (FK → `exams.id`, SET NULL) is preserved
  by the spec (§7.1 keeps `omr_template_id`, §7.9 keeps `exam_id`). The spec does
  not flag this as a problem or call for its removal. While circular FKs are a
  modeling smell, this one is currently functional (both nullable, both SET NULL)
  and the spec correctly preserves it to avoid a breaking change. This is **not
  a defect in the spec**, but the spec should document the deletion-ordering
  implication: deleting an Exam with `omr_template_id` set will SET NULL the
  exam's reference, but the template's `exam_id` still points back — both go
  null, which is consistent. No action required, but worth a note in the spec's
  risk register.
Impact: None — the circular FK is functional and preserved.
Recommendation: Add a note to the spec's risk register documenting the circular
  FK and its deletion semantics. No schema change needed.
```

```
ID: P-05
Section: §8 Batch 5 (Repurpose Question Table)
Problem: Renaming `questions` → `questions_legacy` breaks three foreign keys that
  reference `questions(id)`:
    (1) `attempt_answers.question_id` FK → `questions(id)` ON DELETE SET NULL
        [migration 9a8f7b6c5d4e, line creating attempt_answers]
    (2) `question_skills.question_id` FK → `questions(id)` ON DELETE CASCADE
        [migration 9a8f7b6c5d4e, question_skills table]
    (3) `answer_key_items.question_id` FK → `questions(id)` ON DELETE SET NULL
        [created in Batch 1]
  PostgreSQL will refuse the rename or, worse, leave dangling FK metadata. Even
  if the rename succeeds, the new `questions` table created afterward has
  different columns, so the FKs would point at the wrong schema.
Impact: Batch 5 migration fails or corrupts FK constraints. The application may
  crash on any query joining through these FKs.
Recommendation: Batch 5 must be split into sub-steps:
  (5a) Drop FK constraints: `attempt_answers_question_id_fkey`,
       `question_skills_question_id_fkey`, `answer_key_items_question_id_fkey`.
  (5b) Set `attempt_answers.question_id = NULL` (already NULL in practice —
       confirm_scan never sets it; verify with a pre-check).
  (5c) Drop `question_skills` table (it will be recreated pointing at the new
       bank `questions`, or left empty until Workflow A).
  (5d) Set `answer_key_items.question_id = NULL` for all legacy rows (already
       NULL per Batch 1 migration — verify).
  (5e) Rename `questions` → `questions_legacy`.
  (5f) Create new `questions` table (bank schema).
  (5g) Recreate FKs: `answer_key_items.question_id` → `questions(id)` SET NULL
       (now points at bank); `question_skills.question_id` → `questions(id)`
       CASCADE (recreated for bank). Do NOT recreate `attempt_answers.question_id`
       FK until the bank has rows, OR recreate it as SET NULL (safe since it's
       provenance-only and nullable).
```

```
ID: P-06
Section: §7.3 (answer_key_items) and §7.5 (questions)
Problem: `answer_key_items.question_id` is declared `UUID FK questions(id) SET NULL`.
  In Batch 1, this FK is created pointing at the legacy exam-bound `questions`
  table. In Batch 5, that table is renamed to `questions_legacy` and a new
  `questions` table is created. The spec does not specify whether the FK is
  dropped and recreated to point at the new table. If left as-is after the rename,
  the FK either dangles or PostgreSQL has already rejected the rename (per P-05).
Impact: FK integrity failure or migration rejection.
Recommendation: Addressed by P-05 sub-steps (5a) and (5g). The spec should
  explicitly state that `answer_key_items.question_id` FK is dropped before the
  rename and recreated against the new `questions` table after creation.
```

```
ID: P-07
Section: §10 INV-7 ("Graded AttemptAnswers have non-null answer_key_item_id")
Problem: INV-7 is enforced by "DB constraint" per the table. However, the Batch 2
  migration adds `answer_key_item_id` as nullable and backfills it. If any
  `attempt_answers` row cannot be matched (e.g., `question_number` out of range
  of the AnswerKeyItem's `item_number`), the backfill leaves it NULL. Adding a
  NOT NULL constraint afterward would fail.
Impact: Either the constraint cannot be added, or data is lost by deleting
  unmatched rows.
Recommendation: The Batch 2 migration must include a pre-check: count
  `attempt_answers` rows where no matching `answer_key_item` exists (by
  `attempt → exam → answer_key → item where item_number = question_number`).
  If any exist, abort and report. Only proceed to NOT NULL if zero unmatched.
  This is the same pattern the spec already proposes for Batch 4's
  `correct_answers` consistency check — apply it here too.
```

```
ID: P-08
Section: §7.8 (attempt_answers) — `correct_option` field
Problem: The spec retains `correct_option VARCHAR(50)` as "an optional
  denormalized snapshot and may be removed if the implementation determines that
  the AnswerKeyItem is always safely available." This is ambiguous. The as-built
  `ExportService.generate_student_pdf_report` (export.py:311) reads
  `ans.get("correct_option")` from a dict — meaning the snapshot is currently
  consumed by exports. If the field is dropped, the student PDF export breaks.
  If kept, it duplicates `AnswerKeyItem.correct_answer` (the very duplication the
  refactor aims to eliminate, albeit as a snapshot).
Impact: Either a broken export or a residual duplication.
Recommendation: Decide explicitly. Recommend: keep `correct_option` as a
  grade-time snapshot (written once at confirm, never updated) and document it
  as "denormalized snapshot for export resilience, not a source of truth." This
  matches the existing `is_correct` boolean pattern (also a snapshot). The spec
  should state this decision rather than deferring it.
```

```
ID: P-09
Section: §7.7 (attempts) — `source` field and §11.2 Attempt Lifecycle
Problem: The spec adds `attempts.source VARCHAR(10) NOT NULL DEFAULT 'OMR'` and
  defines an online lifecycle (`not_started → in_progress → submitted → graded`).
  But the OMR path creates attempts directly as `graded`. The spec does not
  define what `status` value standalone OMR templates (no Exam) should produce
  if confirm_scan is called before the Exam is materialized. After P-01/P-03,
  the Exam is materialized in Batch 1, so this is resolved — but the spec's
  §11.2 OMR lifecycle ("OMR confirmation → graded") does not mention that the
  Exam + AnswerKey must pre-exist.
Impact: Minor ambiguity; resolved by P-01/P-03 fixes.
Recommendation: Add a note to §11.2: "OMR confirmation requires a pre-existing
  Exam + AnswerKey (materialized at template creation or during Batch 1
  backfill). confirm_scan does not create Exams."
```

```
ID: P-10
Section: §6 (Entity Disposition Matrix) — `question_skills`
Problem: The matrix says `question_skills` is "Preserved" and "References
  refactored bank Question." But Batch 5 renames `questions` to `questions_legacy`
  and creates a new `questions` table. The `question_skills` table's FK points at
  the old `questions`. If preserved as-is, the FK dangles after rename. If dropped
  and recreated, it's not "preserved" — it's recreated.
Impact: Contradiction between the disposition matrix and the Batch 5 procedure.
Recommendation: Reclassify `question_skills` as "Recreated" (or "Preserved with
  FK re-pointing") in the matrix. The data (skill links) is lost for legacy
  exam-bound questions, which is acceptable since legacy questions are not bank
  entities. The new `question_skills` starts empty and is populated as bank
  questions are created with skills.
```

```
ID: P-11
Section: §0.6 and §19.3 (No destructive renames / Preserve existing data)
Problem: The spec mandates preserving legacy data in `questions_legacy`. However,
  the as-built tests (conftest.py) use SQLite in-memory with
  `BaseModel.metadata.create_all` — NOT Alembic migrations. The tests will
  create the NEW model schema (after code changes), not the legacy schema. There
  is no mechanism to test the migration path (legacy → new) in the test suite.
Impact: Migration bugs (like P-01, P-05) cannot be caught by the existing test
  suite. The tests verify the target schema works, not that the migration from
  the as-built schema works.
Recommendation: Add a migration-test strategy: either (a) a dedicated test that
  applies migrations 0001 → 8c7e7c2e4e00 → 9a8f7b6c5d4e → new batches on a
  throwaway PostgreSQL (or SQLite with migration compatibility) and asserts data
  integrity; or (b) a fixture that seeds legacy-shaped data and runs the
  backfill logic. This is a test-infrastructure gap, not a spec defect, but the
  spec should note it as a prerequisite.
```

```
ID: P-12
Section: §7.1 (exams) — `status` field
Problem: The spec adds `exams.status VARCHAR(20) NOT NULL DEFAULT 'draft'` and
  Batch 6 sets existing rows to `published`. But the as-built `ExamService` has
  no publish action — exams are created directly as active (`is_active=True`).
  The spec's §11.3 Exam Lifecycle defines `draft → published → archived` with
  the rule "An Exam may return to draft only if no Attempt exists." This rule
  is not enforceable by the schema alone; it requires service validation. The
  spec lists this under invariants but the enforcement column for the
  corresponding INV is "Service validation" — which is correct, but the spec
  does not call out that this is a behavior change from the as-built (which has
  no status transitions at all).
Impact: Without service validation, `status` is a cosmetic field. The spec's
  lifecycle contract is unenforceable by the model alone.
Recommendation: Acknowledge in §11.3 that `status` enforcement is entirely
  service-layer and is out of scope for the immediate migration (Batch 6 adds
  the field but does not implement transitions). Transitions are Step 7 of the
  implementation order. This is consistent with the spec but should be explicit.
```

---

## 6. Revised Implementation Plan

Based on the as-built audit and the issues found, the safe implementation sequence. Each step is independently shippable.

### Step 1 — AnswerKey Foundation (Additive Tables + Backfill)

| Attribute | Detail |
|---|---|
| **Objective** | Create `answer_keys`, `answer_key_items`, `answer_key_item_skills`, `exam_questions`. Backfill from BOTH `questions` and `omr_templates.correct_answers` (addressing P-01). No behavior change. |
| **Files to modify** | `backend/app/models/` (new: `answer_key.py`); `backend/app/models/__init__.py`; `backend/app/db/meta.py`; `backend/alembic/versions/` (new migration) |
| **Files NOT to modify** | All services, routes, repositories, schemas, existing tests |
| **Migration** | `XXXX_introduce_answer_keys.py` — creates 4 tables; backfills AnswerKey per Exam (and per orphan OMRTemplate per P-01); backfills AnswerKeyItems from `COALESCE(omr_templates.correct_answers, questions.correct_option)`; sets `is_published=TRUE` for exams with existing graded attempts |
| **Data affected** | New tables populated; no existing data touched |
| **Tests** | New test: `test_answer_key_backfill.py` — verifies every Exam has an AnswerKey, every AnswerKey has items, item count matches `total_questions` or `len(correct_answers)` |
| **DoD** | Tables exist; all existing Exams have AnswerKeys with items; orphan templates have materialized Exams + AnswerKeys; existing tests green; legacy paths unchanged |
| **Risk** | Low — additive only. P-01 fix is the key adjustment. |

### Step 2 — Attempt/AttemptAnswer Reference Refactor

| Attribute | Detail |
|---|---|
| **Objective** | Add `attempts.answer_key_id`, `attempts.attempt_number`, `attempts.source`, `attempt_answers.answer_key_item_id`, `attempt_answers.answered_at`. Backfill all (addressing P-02, P-07). |
| **Files to modify** | `backend/app/models/attempt.py`; `backend/alembic/versions/` (new migration) |
| **Files NOT to modify** | Services, routes, repositories, schemas, tests |
| **Migration** | `XXXX_refactor_attempts.py` — adds nullable columns; backfills `answer_key_id` (from `attempt → exam → answer_key`); backfills `attempt_number = 1`; backfills `source = 'OMR'`; backfills `answer_key_item_id` (from `attempt → answer_key → item where item_number = question_number`); pre-check for unmatched rows (P-07); then alters to NOT NULL where applicable |
| **Data affected** | New columns populated on all existing rows |
| **Tests** | New test: `test_attempt_backfill.py` — verifies every graded Attempt has `answer_key_id`, every AttemptAnswer has `answer_key_item_id`, no NULLs after backfill |
| **DoD** | All columns populated; pre-check passes (zero unmatched); NOT NULL constraints added where safe; existing tests green |
| **Risk** | Medium — P-07 pre-check is critical. If unmatched rows exist, migration aborts. |

### Step 3 — Switch Grading and Statistics to AnswerKeyItem

| Attribute | Detail |
|---|---|
| **Objective** | Switch all 6 critical read points (Dependency Map rows 4, 5, 6, 13, 16, 34) to read from `AnswerKeyItem`. Switch write paths to write `AnswerKey`/`AnswerKeyItem` instead of `omr_templates.correct_answers`/`questions`. Address P-03 (remove implicit Exam creation in confirm_scan). |
| **Files to modify** | `backend/app/services/omr.py` (`_calculate_score`, `confirm_scan`, `update_scan_manual`); `backend/app/services/exam.py` (`create_exam`, `get_exam_statistics`, `export_exam_pdf`, `export_exam_xlsx`); `backend/app/repositories/exam.py` (`create_questions_bulk` → `create_answer_key_items`); `backend/app/repositories/attempt.py` (`create_answers_bulk` writes `answer_key_item_id`); `backend/app/schemas/exam.py` (response models); `backend/app/schemas/omr.py` (make `correct_answers` optional, then unused); `backend/app/schemas/attempt.py` (add `answer_key_item_id`); `backend/app/models/exam.py` (add `answer_key` relationship); `backend/app/models/__init__.py` |
| **Files NOT to modify** | `omr_engine.py`, `omr_pdf.py`, `omr_layouts.py`, `omr_sheet_image.py` (OMR engine unchanged); `models/user.py`, `models/grade.py`, `models/skill.py` (preserved); existing migrations |
| **Migration** | None (code only) |
| **Data affected** | New writes go to `AnswerKeyItem`; legacy columns go stale |
| **Tests** | Update: `test_omr_service.py`, `test_omr_api.py`, `test_exam_service.py`, `test_exam_api.py`, `test_omr_models.py` — switch from `correct_answers` to `AnswerKeyItem` assertions. New: `test_answer_key_grading.py` — verifies OMR grading reads from AnswerKeyItem; `test_workflow_b.py` — verifies grading with zero `questions` rows |
| **DoD** | No grading/statistics/export path reads `omr_templates.correct_answers` or `questions.correct_option`; OMR end-to-end flow works via AnswerKeyItem; Workflow B (no questions) grades correctly; all tests green |
| **Risk** | High — largest change; must be atomic. P-03 (implicit Exam creation) must be resolved. |

### Step 4 — Remove OMR Answer Duplication

| Attribute | Detail |
|---|---|
| **Objective** | Drop `omr_templates.correct_answers` column after consistency verification. |
| **Files to modify** | `backend/app/models/omr.py` (remove `correct_answers` field); `backend/app/schemas/omr.py` (remove `correct_answers` from `OMRTemplateBase`); `backend/alembic/versions/` (new migration) |
| **Files NOT to modify** | Services (already switched in Step 3), routes, repositories |
| **Migration** | `XXXX_drop_omr_correct_answers.py` — pre-check: `SELECT COUNT(*) FROM omr_templates t JOIN answer_keys ak ON ... WHERE disagreement`; if zero, `DROP COLUMN correct_answers` |
| **Data affected** | `omr_templates.correct_answers` column removed |
| **Tests** | Update `test_omr_models.py` — remove `correct_answers` assertions |
| **DoD** | Column dropped; no code references it; tests green |
| **Risk** | Low — after Step 3, nothing reads it. Downgrade loses data (acceptable). |

### Step 5 — Repurpose Question Table (Split into Sub-steps per P-05)

| Attribute | Detail |
|---|---|
| **Objective** | Rename legacy `questions` → `questions_legacy`; create new bank `questions` table. |
| **Files to modify** | `backend/app/models/question.py` (rewrite as bank entity); `backend/app/models/skill.py` (`question_skills` re-pointed); `backend/app/models/__init__.py`; `backend/alembic/versions/` (new migration) |
| **Files NOT to modify** | Services, routes (already switched in Step 3) |
| **Migration** | `XXXX_repurpose_questions.py` — sub-steps per P-05: (5a) drop FKs; (5b) NULL out `attempt_answers.question_id`; (5c) drop `question_skills`; (5d) NULL out `answer_key_items.question_id`; (5e) rename `questions` → `questions_legacy`; (5f) create new `questions` (bank schema); (5g) recreate `answer_key_items.question_id` FK → new `questions`; recreate `question_skills` → new `questions` |
| **Data affected** | Legacy `questions` preserved as `questions_legacy`; new `questions` empty |
| **Tests** | New: `test_questions_legacy_preserved.py` — verifies legacy data intact; `test_bank_question_model.py` — verifies new bank schema |
| **DoD** | `questions_legacy` exists with all legacy rows; new `questions` exists (empty); all FKs valid; `answer_key_items.question_id` points at new `questions`; tests green |
| **Risk** | High — most delicate migration. P-05 sub-steps are mandatory. |

### Step 6 — Workflow A (ExamQuestion + Projection)

| Attribute | Detail |
|---|---|
| **Objective** | Implement `ExamQuestion` composition and publish-time projection into `AnswerKeyItem`. |
| **Files to modify** | `backend/app/models/exam.py` (add `exam_questions` relationship); `backend/app/services/exam.py` (publish action); new: `backend/app/repositories/question.py` (bank CRUD); new: `backend/app/api/routes/questions.py`; `backend/app/schemas/question.py` (bank schemas) |
| **Migration** | None (`exam_questions` created in Step 1) |
| **Data affected** | New bank Questions and ExamQuestions |
| **Tests** | New: `test_workflow_a.py` — create bank Question → compose Exam → publish → verify AnswerKeyItem projected with `question_id` set, `correct_answer` copied, skills snapshotted |
| **DoD** | Workflow A produces AnswerKeyItems from bank Questions; Workflow B still works independently; tests green |
| **Risk** | Medium — new functionality; doesn't touch OMR. |

### Step 7 — Exam Lifecycle (Deferred per P-12)

| Attribute | Detail |
|---|---|
| **Objective** | Implement `draft → published → archived` transitions with service validation. |
| **Files to modify** | `backend/app/services/exam.py` (publish/archive actions); `backend/app/api/routes/exams.py` (publish endpoint); `backend/app/schemas/exam.py` |
| **Migration** | `XXXX_add_exam_lifecycle_fields.py` (Batch 6 — can be done earlier, inert) |
| **DoD** | Publish validates rules; transitions enforced; archived is soft-terminal |
| **Risk** | Low — additive. |

---

## 7. Recommended First Milestone

```
Milestone: AnswerKey Foundation (Step 1)
Objective: Introduce AnswerKey, AnswerKeyItem, answer_key_item_skills, and
  exam_questions as additive tables. Backfill from BOTH questions and
  omr_templates.correct_answers (addressing P-01). Zero behavior change.
  All existing OMR flows remain 100% functional on legacy paths.

Files to be modified:
  - backend/app/models/answer_key.py          (NEW — AnswerKey, AnswerKeyItem,
                                               answer_key_item_skills table)
  - backend/app/models/exam_question.py       (NEW — ExamQuestion, exam_questions)
  - backend/app/models/__init__.py            (add imports/exports)
  - backend/app/db/meta.py                    (update imports)
  - backend/alembic/versions/XXXX_introduce_answer_keys.py  (NEW migration)

Files that must NOT be modified:
  - backend/app/services/*          (all services unchanged)
  - backend/app/api/routes/*        (all routes unchanged)
  - backend/app/repositories/*      (all repos unchanged)
  - backend/app/schemas/*           (all schemas unchanged)
  - backend/app/models/omr.py       (OMRTemplate.correct_answers stays)
  - backend/app/models/question.py  (legacy Question stays)
  - backend/app/models/attempt.py   (Attempt/AttemptAnswer unchanged)
  - backend/app/models/exam.py      (Exam unchanged — no answer_key relationship yet)
  - backend/app/services/omr_engine.py, omr_pdf.py, omr_layouts.py, omr_sheet_image.py
  - All existing tests
  - TARGET_DOMAIN_MODEL.md, ARCHITECTURE.md, STATUS_ATUAL.md, AGENTS.md,
    all PLANO_*.md, ROADMAP.md

Migration: XXXX_introduce_answer_keys.py
  - Create answer_keys (id, exam_id UNIQUE FK→exams RESTRICT, is_published BOOL
    DEFAULT FALSE, published_at TIMESTAMPTZ, created_at, updated_at)
  - Create answer_key_items (id, answer_key_id FK→answer_keys CASCADE,
    item_number INT, correct_answer VARCHAR(50) NOT NULL, weight NUMERIC(5,2)
    DEFAULT 1.00, statement TEXT, question_id FK→questions SET NULL,
    created_at, updated_at, UNIQUE(answer_key_id, item_number))
  - Create answer_key_item_skills (answer_key_item_id FK→answer_key_items CASCADE,
    skill_id FK→skills CASCADE, PRIMARY KEY(answer_key_item_id, skill_id))
  - Create exam_questions (id, exam_id FK→exams CASCADE, question_id FK→questions
    RESTRICT, display_order INT, weight NUMERIC(5,2), created_at,
    UNIQUE(exam_id, question_id))
  - Backfill (addressing P-01):
    FOR EACH omr_template WHERE correct_answers IS NOT NULL:
      IF template.exam_id IS NULL:
        — Create Exam (title=template.title, teacher_id=...,
          omr_template_id=template.id, total_questions=template.total_questions,
          max_score=10.00, is_active=TRUE)
        — UPDATE template.exam_id = new_exam.id
      END IF
      IF no answer_key exists for template.exam_id:
        — Create AnswerKey (exam_id, is_published=TRUE if graded attempts exist)
        — FOR EACH (key, value) IN template.correct_answers:
            item_number = int(key.replace("q","").replace("Q",""))
            Create AnswerKeyItem (answer_key_id, item_number, correct_answer=value,
              weight=1.00, statement=NULL, question_id=NULL)
          END FOR
      END IF
    END FOR
    FOR EACH exam WHERE no answer_key exists AND has questions rows:
      — Create AnswerKey (exam_id)
      — FOR EACH question WHERE exam_id = exam.id ORDER BY question_number:
          correct = COALESCE(
            (SELECT correct_answers->>question_number FROM omr_templates
             WHERE id = exam.omr_template_id),
            question.correct_option
          )
          Create AnswerKeyItem (answer_key_id, item_number=question.question_number,
            correct_answer=correct, weight=question.weight,
            statement=question.statement, question_id=NULL)
        END FOR
    END FOR

Data affected:
  - New tables created and populated.
  - Orphan OMRTemplates (no exam_id) get a materialized Exam (P-01/P-03 fix).
  - No existing rows modified or deleted (except omr_templates.exam_id set on
    orphan templates, which is currently NULL — safe).

Tests:
  - NEW: backend/tests/test_answer_key_backfill.py
    - test_every_exam_has_answer_key
    - test_every_answer_key_has_items
    - test_item_count_matches_template_total_questions
    - test_orphan_template_gets_materialized_exam
    - test_correct_answer_matches_omr_template_source
    - test_correct_answer_matches_questions_source_when_no_template
    - test_existing_omr_flow_unchanged (regression: create template, upload,
      confirm — all still work via legacy paths)

Definition of Done:
  1. answer_keys, answer_key_items, answer_key_item_skills, exam_questions exist.
  2. Every existing Exam has exactly one AnswerKey with ≥1 AnswerKeyItem.
  3. Every OMRTemplate with correct_answers has a materialized Exam + AnswerKey.
  4. AnswerKeyItem.correct_answer matches the COALESCE of template/questions sources.
  5. No service, route, or schema file is modified.
  6. All 44 existing pytest functions pass unchanged.
  7. New backfill tests pass.
  8. Migration is reversible (downgrade drops new tables; materialized Exams
     for orphan templates are removed or left orphaned — documented).

Risks:
  - P-01: If backfill misses orphan templates, they become ungradable after
    Step 3. Mitigated by explicit orphan-materialization in the migration.
  - P-11: Existing test suite (SQLite, metadata.create_all) cannot test the
    migration path. The new backfill tests must use a fixture that seeds
    legacy-shaped data (omr_templates with correct_answers, questions rows)
    and then invokes the backfill logic directly (not via Alembic) to verify
    correctness. A separate PostgreSQL-based migration test is recommended
    but may be out of scope for this milestone.
  - Orphan template materialization creates Exams with inferred teacher_id
    (unknown for pre-existing standalone templates). The migration must either
    pick a default admin/teacher or leave teacher_id nullable temporarily.
    Recommend: query for any TEACHER user and use their ID; if none, abort
    with a clear error. This is a data-quality decision that should be
    documented in the migration's docstring.
```

---

## 8. Risk Assessment by Stage

| Stage | Risk Level | Key Risks | Mitigations |
|---|---|---|---|
| **Step 1 — AnswerKey Foundation** | **Low** | P-01 (orphan templates); P-11 (untestable migration path); orphan-template `teacher_id` inference | Explicit orphan materialization in migration; direct backfill-logic tests; documented teacher_id inference |
| **Step 2 — Attempt Refactor** | **Medium** | P-02 (NOT NULL on populated table); P-07 (unmatched AttemptAnswers) | Nullable-add-then-backfill-then-constrain pattern; pre-check aborts on unmatched rows |
| **Step 3 — Code Switch** | **High** | 6 critical read points must switch atomically; P-03 (implicit Exam creation in confirm_scan); test breakage across 6 test files | Atomic single-commit switch; remove implicit Exam creation (Exams pre-exist from Step 1); update all tests in same commit |
| **Step 4 — Drop correct_answers** | **Low** | Residual references missed | Pre-check for disagreement; global grep verification before drop |
| **Step 5 — Repurpose Questions** | **High** | P-05 (3 FKs break on rename); P-06 (answer_key_items FK re-pointing); P-10 (question_skills disposition) | Split into 7 sub-steps (5a–5g); drop FKs before rename; recreate after new table; verify with FK integrity query |
| **Step 6 — Workflow A** | **Medium** | New functionality; projection correctness; skill snapshot vs. live link distinction | Dedicated Workflow A test; verify projection copies (not references) skills |
| **Step 7 — Exam Lifecycle** | **Low** | P-12 (status enforcement is service-only); behavior change from as-built | Additive field; transitions implemented as service validation; document that as-built had no transitions |

### Cross-cutting risks (apply to all stages)

| Risk | Severity | Notes |
|---|---|---|
| **SQLite/PostgreSQL divergence** (P-11) | Medium | Tests use SQLite + `metadata.create_all`; production uses PostgreSQL + Alembic. `PGUUID` in `BaseModel` silently falls back in SQLite but is PostgreSQL-specific. JSONB vs JSON differences (SQLite has no JSONB). Migration logic cannot be tested in the existing suite. **Recommendation:** add at least one PostgreSQL-backed migration integration test, or document this as a known gap. |
| **`test.db` committed artifact** | Low | `test.db` (SQLite file) is tracked in git but referenced by no code. Should be untracked before any migration work to avoid confusion. Not a blocker. |
| **`alembic.ini` URL points to `localhost:5432`** | Low | Migrations run from host (not container). The app runs in Docker with `DATABASE_URL=postgresql+psycopg://colazero:colazero@postgres:5432/colazero`. This is a known dev-setup quirk; migrations work when run from host with PostgreSQL exposed on 5432. Not a blocker but document. |
| **`meta.py` is stale** | Low | `app/db/meta.py` imports only `Grade, OMRScan, OMRTemplate, User` — missing `Exam, Question, Skill, Attempt, AttemptAnswer`. Likely unused (no grep hits for `from app.db.meta import`), but should be updated or removed to avoid confusion. |
| **`ExportService.generate_student_pdf_report`** (P-08) | Low | A third export method exists (`export.py:251`) that reads `ans["question_number"]` and `ans["correct_option"]` from a dict. It is not called by any route (no grep hits in routes). It's either dead code or planned for a future student-facing report. It must be updated when `question_number`/`correct_option` are renamed/removed, or confirmed as dead code and deleted. **Recommendation:** verify whether any frontend or planned feature calls it before the refactor touches those fields. |

---

*End of Phase 0 pre-implementation analysis. No files were modified. This document, together with `TARGET_DOMAIN_MODEL.md`, defines the safe execution path for the domain-model refactor.*

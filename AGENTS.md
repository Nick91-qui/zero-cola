# AGENTS.md

# COLA-ZERO

Secure Online Assessment Platform

---

# Purpose

This document defines the development rules, architecture principles, priorities, and implementation constraints for all AI agents working on the COLA-ZERO codebase.

Agents must follow this document before making architectural, database, security, or UI decisions.

---

# Project Vision

COLA-ZERO is an online assessment platform designed for schools and educational institutions.

The system focuses on:

- Question bank management
- Dynamic exam delivery
- Exam integrity monitoring
- Teacher workflow optimization
- Student usability
- Security by design
- LGPD compliance

COLA-ZERO is NOT a surveillance platform.

Monitoring exists only to provide evidence of suspicious behavior and improve assessment integrity.

---

# Core Architectural Principle

Everything revolves around:

> Question Bank + Attempt Engine

The Question Bank is the core content repository. Exams are delivery configurations composed of reusable questions. Academic history is represented by Attempts and Answers.

Domain flow: Question -> Exam -> Attempt -> Answer

---

# Technology Stack

## Backend

- Python
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Pydantic

## Frontend

- Next.js
- React
- TypeScript
- TailwindCSS

## Infrastructure

- Docker
- Docker Compose

---

# Development Philosophy

## Keep It Simple

Prefer simple solutions over complex abstractions.

Avoid premature optimization.

Avoid overengineering.

---

## Security First

Every new feature must be evaluated for:

- Authentication impact
- Authorization impact
- Data exposure
- LGPD implications

---

## Privacy by Design

Collect the minimum amount of information required.

Never collect data without a clear purpose.

Monitoring features must always be transparent to users.

---

# User Roles

## Student

Can:

- View assigned exams
- Start attempts
- Submit answers
- View released results

Cannot:

- Access question bank
- Access other students' data
- Modify exams

---

## Teacher

Can:

- Create questions
- Manage question bank
- Create exams
- Grade exams
- View monitoring reports

Cannot:

- Access system administration

---

## Administrator

Can:

- Manage users
- Manage institutions
- Access platform settings
- View audit logs

---

# Database Rules

## UUIDs

All primary keys must use UUID.

Never use incremental IDs.

Example:

```sql
id UUID PRIMARY KEY
```

---

## Auditability

Never delete important academic records.

Prefer:

- soft delete
- archival

instead of hard deletion.

---

## Historical Data

Answers must never be overwritten.

Create new records when historical preservation is required.

---

# Question Bank Rules

Questions must be reusable.

A question may belong to many exams.

Exams must never contain duplicated question content.

Use relationships.

Correct:

```text
Exam
 └── ExamQuestion
       └── Question
```

Wrong:

```text
Exam
 └── Question Copy
```

---

# Exam Delivery Rules

## One Question At A Time

The frontend must never receive the entire exam.

Allowed:

```text
Question 1
submit
Question 2
submit
Question 3
```

Not allowed:

```text
Receive all questions at once
```

Reason:

- Reduces leakage
- Improves monitoring
- Simplifies autosave

---

## Autosave

Answers must be saved immediately after submission.

No answer should depend on a final submit action.

---

# Exam Publication Rules

An exam may only be published if:

- It has a title
- It contains at least 1 question
- All referenced questions exist
- All question weights are greater than 0
- Total weight equals 100
- A class is assigned
- A valid time limit is configured
- The publishing user is the owner teacher or an admin

---

# Attempt Rules

The attempt model and rules are defined as follows:

Exam fields:
- `max_attempts` (INTEGER, default = 1)
- `time_limit`
- `randomize` (or `randomization_enabled`)
- `status`

Attempt fields:
- `attempt_number` (INTEGER, NOT NULL)
- `status`
- `score`

Rules:
- Only one active attempt (`in_progress`) is allowed per student per exam.
- Existing active attempts must be resumed instead of creating a new one.
- A new attempt can only be created if `max_attempts` is not exceeded.
- Submitted attempts cannot be modified.
- Graded attempts are immutable.

---

# Monitoring Rules

COLA-ZERO is not a lockdown browser and must never claim:
- Detection of ChatGPT usage
- Detection of external devices
- Prevention of screenshots
- Prevention of all cheating

The platform only records and reports observable browser events (stored in `security_events` table).

The platform can only:

- Detect events
- Record events
- Generate reports

---

## Supported Events

Frontend monitoring may include:

- visibilitychange
- blur
- focus
- fullscreen enter
- fullscreen exit

---

## Unsupported Claims

Do not implement features that claim to:

- Detect ChatGPT usage
- Detect another device
- Detect external phones
- Detect screenshots reliably
- Prevent all forms of cheating

These claims are technically inaccurate.

---

# LGPD Requirements

All monitoring requires transparency.

Users must be informed that monitoring exists.

---

## Minimum Data Collection

Collect only:

- Account information
- Exam answers
- Exam-related events
- Audit logs

Avoid collecting:

- Contacts
- Personal files
- Device contents
- Browser history

---

## Data Export

The system must support user data export.

---

## Data Deletion

The system must support anonymization when legally permitted.

Academic records may have retention requirements.

---

# Security Standards

## Authentication

Required:

- JWT Access Token: Must be stored in a secure HttpOnly cookie (Secure, SameSite=Lax, short expiration 15–30 min).
- JWT Refresh Token: Must be stored in a secure HttpOnly cookie (Secure, SameSite=Strict, long expiration 7–30 days).

Do not use localStorage or sessionStorage for JWT storage.

Passwords:

- Argon2 preferred
- bcrypt acceptable

Never store plain text passwords.

---

## Authorization

RBAC required.

Every endpoint must validate permissions.

---

## Logging

Security-sensitive actions must generate audit records.

Examples:

- Login
- Password change
- Exam creation
- Grade modification

---

# Backend Guidelines

Use:

- Service layer
- Repository pattern when useful
- Dependency injection

Avoid:

- Business logic in routes
- Large route files
- Direct database access inside controllers

---

# Frontend Guidelines

Prefer:

- Reusable components
- Server-safe rendering
- Strong TypeScript typing

Avoid:

- Massive pages
- Business logic inside UI components

---

# Testing Requirements

Every critical module must include tests.

Priority:

1. Authentication
2. Authorization
3. Exam delivery
4. Answer submission
5. Grading
6. Monitoring

---

# Performance Goals

Target:

- Question delivery < 500ms
- Login < 1 second
- Exam submission < 500ms

---

# Future Features

Possible future modules:

- AI-assisted question generation
- Statistical item analysis
- Difficulty calibration
- Learning analytics
- Institutional multi-tenancy
- Safe Exam Browser integration

These features are optional and must not affect the MVP architecture.

---

# MVP Definition

The MVP is complete when:

- Users authenticate
- Teachers create questions
- Teachers create exams
- Students take exams
- Answers are graded
- Monitoring events are recorded
- Reports are generated
- LGPD requirements are satisfied

Everything else is secondary.

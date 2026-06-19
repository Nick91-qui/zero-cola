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

The primary entity is NOT the exam.

The primary entity is the Question.

Exams are collections of questions.

Attempts are student interactions with exams.

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

# Monitoring Rules

COLA-ZERO is not a lockdown browser.

Agents must never claim that the platform can prevent cheating.

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

- JWT Access Token
- JWT Refresh Token

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

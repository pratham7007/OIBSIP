# Online Examination System

**Internship:** Oasis Infobyte - OIBSIP
**Track:** Java Development
**Assignment:** Task 4

## Objective & description

Swing-based timed multiple-choice examination.

## Tech stack

Java, Maven, SQLite (for database-backed assignments).

## Features implemented

- Login and profile update
- Previous/next navigation, countdown auto-submit, and manual submit
- Answer review and score summary

## How to run / setup

Use JDK 25+ and Maven 3.8+. From this folder run `mvn clean package`, then `mvn exec:java`. Swing projects need a desktop session.

Primary deliverable: [`src/main/java/com/oasis/exam/OnlineExamApp.java`](./src/main/java/com/oasis/exam/OnlineExamApp.java).

> Database-backed demos create local data at runtime; do not use real credentials.

## Generated outputs

- [outputs/online-examination-1.0.0.jar](./outputs/online-examination-1.0.0.jar)

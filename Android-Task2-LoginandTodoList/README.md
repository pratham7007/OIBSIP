# Login and To-do List

**Internship:** Oasis Infobyte - OIBSIP
**Track:** Android App Development
**Assignment:** Task 2

## Objective & description

Provide user registration/login and a per-user to-do list backed by SQLite.

## Tech stack

Java, Android SDK, Gradle.

## Features implemented

- SQLite-backed registration and login
- Per-user tasks with optional notes, completion, deletion, and empty state
- Salted PBKDF2-HMAC-SHA256 password derivation and parameterized database operations

## How to run / setup

Open this folder in Android Studio and run on an emulator/device, or run `.\gradlew.bat assembleDebug` in PowerShell.

Primary deliverable: [`app/src/main/java/com/oasis/internship/LoginActivity.java`](./app/src/main/java/com/oasis/internship/LoginActivity.java).

> Each task folder contains the full launcher app so its task can be run and explored independently; open the named screen from the launcher.

## Generated outputs

- [outputs/app-debug.apk](./outputs/app-debug.apk)

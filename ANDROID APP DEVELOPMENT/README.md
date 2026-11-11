# Android App Development assignments

This folder is one Android Studio application containing five separately launchable assignment screens. Open the project root (this folder) in Android Studio; the launcher presents the five screens.

## Requirements and setup

- Android Studio (a current stable release with Android Gradle Plugin 8.7.3 support)
- JDK 25 or newer to run the Gradle build (the Android app's language/API compatibility is governed separately by Android Gradle Plugin and Android SDK settings)
- Android SDK Platform 35 and a matching emulator or USB-debugging Android device
- Internet access for the first Gradle sync to download the Android Gradle Plugin and dependencies

In Android Studio, choose **Open**, select this folder, install the suggested SDK packages, wait for Gradle sync, then choose **Run**. To build from a terminal after installing the SDK, set `JAVA_HOME` to a JDK 25+ installation and run `.\gradlew.bat assembleDebug` from this folder. The wrapper uses Gradle 9.7.1. The debug APK is written to `app\build\outputs\apk\debug\app-debug.apk`.

On this machine, the Android SDK is installed at `%LOCALAPPDATA%\Android\Sdk`. The user-level `ANDROID_HOME` and `ANDROID_SDK_ROOT` variables point to it, and the user `PATH` includes `platform-tools` and the command-line tools. `local.properties` supplies the SDK path to this project and is excluded from version control. Restart VS Code or open a new terminal to inherit the updated user environment.

The project uses the Android Gradle Plugin 8.7.3, compile SDK 35, target SDK 34, min SDK 26, and has no third-party runtime dependencies. The higher minimum API supports the built-in PBKDF2-HMAC-SHA256 password derivation used by the local account database.

## Assignment screens

1. **Unit converter** — category Spinner for length, weight, and temperature; unit Spinners reset on category changes; validates empty, malformed, and non-finite numeric input.
2. **Login + user-specific to-do list** — SQLite registration/login with per-user random salts and PBKDF2-HMAC-SHA256 (210,000 iterations), parameterized lookups/updates, a foreign-key-linked task table, optional notes, completion, deletion, empty state, and logout. Passwords are never stored in plaintext. Password derivation runs off the UI thread.
3. **Calculator** — XML GridLayout keypad, decimal input, clear/backspace, arithmetic precedence, and divide-by-zero error handling.
4. **Quiz** — ten general-knowledge questions shuffled on each run, immediate green/red feedback, score, correct/incorrect totals, restart, and saved in-progress state across recreation.
5. **Stopwatch** — start, pause/resume, reset, and lap list. Elapsed time is derived from the monotonic Android elapsed-realtime clock; UI callbacks pause when the screen is backgrounded and resume with the correct elapsed value.

## Validation status

The project files and assignment requirements were checked against the Android section of `D:\Oasis\OASIS INFOBYTE — Task List.pdf`. Android command-line tools, Android SDK Platform 35, Build Tools 34.0.0 and 35.0.0, and platform-tools are installed. `.\gradlew.bat assembleDebug` completed successfully and produced `app\build\outputs\apk\debug\app-debug.apk`. No emulator or device test has been performed.

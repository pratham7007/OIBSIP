# Java Development Assignments

Five independent Java 25+ programs are provided. Each assignment has its own source tree and Maven `pom.xml`, configured to compile for Java 25; run Maven with JDK 25 or newer from that assignment's directory. The two database-backed applications use SQLite and create their local `data` folder on first run. SQL values are bound with JDBC `PreparedStatement`; account passwords use per-user salted PBKDF2 hashes rather than plaintext.

## Requirements

- JDK 25 or newer (`java` and `javac` on `PATH`)
- Apache Maven 3.8+ for dependency resolution and the run commands below
- A desktop session for the Swing applications
- Network access on the first Maven build to download the SQLite JDBC driver for the reservation and library apps

## Assignments

| Assignment | Program | Run |
|---|---|---|
| 1. Online Reservation System | Swing GUI with account registration/login, train selection, booking, PNR lookup and owner-only cancellation | `cd "Online Reservation System"; mvn clean package; mvn exec:java` |
| 2. Number Guessing Game | Console game with Easy/Medium/Hard, bounded attempts, replay and round summary | `cd "Number Guessing Game"; mvn clean package; mvn exec:java` |
| 3. ATM Interface | OOP console simulation with three login attempts, hashed in-memory PINs, history, deposits, withdrawals and transfers | `cd "ATM Interface"; mvn clean package; mvn exec:java` |
| 4. Online Examination System | Swing MCQ exam with login, profile update, previous/next, countdown auto-submit, manual submit and answer review | `cd "Online Examination System"; mvn clean package; mvn exec:java` |
| 5. Digital Library Management System | Local web-style HTML/CSS app with user/admin roles, catalogue, issues/returns, reservations, fines, member list and queries | `cd "Digital Library Management System"; mvn clean package; mvn exec:java` |

On Windows PowerShell, run one project at a time; each `cd` path contains spaces. The library listens only on `127.0.0.1:8080` by default. To use another port or a shorter exam timer, pass Java options to Maven, for example `$env:JAVA_TOOL_OPTIONS='-Doasis.library.port=8081'; mvn exec:java` or `$env:JAVA_TOOL_OPTIONS='-Doasis.exam.minutes=1'; mvn exec:java`.

## First-run accounts and data

- **Train reservations:** Create an account on the Swing sign-in screen. SQLite data is stored in `Online Reservation System\data\train-reservations.db`.
- **ATM:** Two demo account IDs and randomly generated PINs are printed to the console at startup. They and all balances/history exist only for that run.
- **Examination:** The `student` username and a randomly generated temporary password are printed to the console at startup. After login, use the profile screen to set a display name and optionally change the password. The default exam duration is 30 minutes; for a short demonstration set `-Doasis.exam.minutes=1`.
- **Digital library:** The first server startup creates an `admin` account with a random password printed once to the console. Save it before closing the terminal. Members self-register at `/register`. Library records are stored in `Digital Library Management System\data\library.db`; back up that file before resetting it. The example server is for local demonstration, not production deployment.

## Validation notes

All source is compiled with the Java 25 release target and can be syntax-checked without third-party libraries using JDK 25 `javac`. Maven is the supported build/run path; the database programs additionally need the declared SQLite JDBC dependency at runtime. The exercise programs use in-memory state where persistence was not specified.

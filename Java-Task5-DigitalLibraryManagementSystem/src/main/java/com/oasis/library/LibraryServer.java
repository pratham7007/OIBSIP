package com.oasis.library;

import com.sun.net.httpserver.*;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.*;
import java.sql.*;
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.concurrent.*;

public final class LibraryServer {
    private static final String DB_URL;
    private static final int PORT = Integer.getInteger("oasis.library.port", 8080);
    private static final Map<String, Session> SESSIONS = new ConcurrentHashMap<>();
    private static final SecureRandom RANDOM = new SecureRandom();
    private static final String[] SEED_BOOKS = {
            "The Pragmatic Programmer|Andrew Hunt and David Thomas|9780201616224|Technology|4",
            "Clean Code|Robert C. Martin|9780132350884|Technology|3",
            "The Hobbit|J. R. R. Tolkien|9780547928227|Fantasy|2",
            "Pride and Prejudice|Jane Austen|9780141439518|Classics|2",
            "A Brief History of Time|Stephen Hawking|9780553380163|Science|2"
    };

    static {
        try {
            Path data = Path.of("data");
            Files.createDirectories(data);
            DB_URL = "jdbc:sqlite:" + data.resolve("library.db").toAbsolutePath();
        } catch (IOException ex) {
            throw new ExceptionInInitializerError(ex);
        }
    }

    private LibraryServer() {}

    public static void main(String[] args) throws Exception {
        initializeDatabase();
        createFirstAdminIfNeeded();
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", PORT), 0);
        server.createContext("/", LibraryServer::handle);
        server.setExecutor(Executors.newFixedThreadPool(Math.max(4, Runtime.getRuntime().availableProcessors())));
        server.start();
        System.out.println("Oasis Digital Library is running at http://127.0.0.1:" + PORT);
        System.out.println("Stop with Ctrl+C. This development server listens on localhost only.");
    }

    private static Connection connect() throws SQLException {
        Connection c = DriverManager.getConnection(DB_URL);
        try (Statement s = c.createStatement()) { s.execute("PRAGMA foreign_keys=ON"); }
        return c;
    }

    private static void initializeDatabase() throws SQLException {
        try (Connection c = connect(); Statement s = c.createStatement()) {
            s.executeUpdate("""
                    CREATE TABLE IF NOT EXISTS users(
                      id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE, display_name TEXT NOT NULL,
                      salt TEXT NOT NULL, password_hash TEXT NOT NULL,
                      role TEXT NOT NULL CHECK(role IN ('ADMIN','USER')), active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
                      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )""");
            s.executeUpdate("""
                    CREATE TABLE IF NOT EXISTS books(
                      id INTEGER PRIMARY KEY, title TEXT NOT NULL, author TEXT NOT NULL,
                      isbn TEXT NOT NULL UNIQUE, category TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity >= 0)
                    )""");
            s.executeUpdate("""
                    CREATE TABLE IF NOT EXISTS loans(
                      id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
                      book_id INTEGER NOT NULL REFERENCES books(id), issued_on TEXT NOT NULL,
                      due_on TEXT NOT NULL, returned_on TEXT
                    )""");
            s.executeUpdate("""
                    CREATE TABLE IF NOT EXISTS reservations(
                      id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
                      book_id INTEGER NOT NULL REFERENCES books(id), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                      status TEXT NOT NULL DEFAULT 'WAITING' CHECK(status IN ('WAITING','FULFILLED','CANCELLED')),
                      UNIQUE(user_id, book_id, status)
                    )""");
            s.executeUpdate("""
                    CREATE TABLE IF NOT EXISTS fines(
                      id INTEGER PRIMARY KEY, loan_id INTEGER NOT NULL UNIQUE REFERENCES loans(id),
                      user_id INTEGER NOT NULL REFERENCES users(id), amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
                      paid INTEGER NOT NULL DEFAULT 0 CHECK(paid IN (0,1)), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )""");
            s.executeUpdate("""
                    CREATE TABLE IF NOT EXISTS queries(
                      id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
                      subject TEXT NOT NULL, message TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )""");
        }
        try (Connection c = connect(); PreparedStatement p = c.prepareStatement(
                "INSERT OR IGNORE INTO books(title, author, isbn, category, quantity) VALUES(?, ?, ?, ?, ?)")) {
            for (String line : SEED_BOOKS) {
                String[] book = line.split("\\|", -1);
                for (int i = 0; i < 4; i++) p.setString(i + 1, book[i]);
                p.setInt(5, Integer.parseInt(book[4]));
                p.addBatch();
            }
            p.executeBatch();
        }
    }

    private static void createFirstAdminIfNeeded() throws SQLException {
        try (Connection c = connect(); PreparedStatement count = c.prepareStatement(
                "SELECT COUNT(*) FROM users WHERE role='ADMIN'"); ResultSet rs = count.executeQuery()) {
            if (rs.next() && rs.getInt(1) > 0) return;
        }
        String password = newSecret();
        byte[] salt = salt();
        try (Connection c = connect(); PreparedStatement p = c.prepareStatement(
                "INSERT INTO users(username, display_name, salt, password_hash, role) VALUES(?, ?, ?, ?, 'ADMIN')")) {
            p.setString(1, "admin");
            p.setString(2, "Library Administrator");
            p.setString(3, Base64.getEncoder().encodeToString(salt));
            p.setString(4, passwordHash(password.toCharArray(), salt));
            p.executeUpdate();
        }
        System.out.println("First-run admin credentials (save them; the password is not stored in plaintext):");
        System.out.println("Username: admin");
        System.out.println("Temporary password: " + password);
        System.out.println("Change this password after setup; no password-reset endpoint is provided.");
    }

    private static void handle(HttpExchange exchange) throws IOException {
        try {
            Session session = session(exchange);
            String path = exchange.getRequestURI().getPath();
            if (exchange.getRequestMethod().equals("GET")) {
                switch (path) {
                    case "/", "/books" -> sendHtml(exchange, 200, catalogue(session, query(exchange, "q"), query(exchange, "category")));
                    case "/login" -> sendHtml(exchange, 200, loginPage(session, ""));
                    case "/register" -> sendHtml(exchange, 200, registerPage(session, ""));
                    case "/admin" -> sendHtml(exchange, 200, adminPage(requireRole(session, "ADMIN"), session));
                    default -> sendHtml(exchange, 404, page("Not found", "<h1>Page not found</h1>"));
                }
            } else if (exchange.getRequestMethod().equals("POST")) {
                Map<String, String> form = readForm(exchange);
                if (!Objects.equals(session.csrf, form.get("csrf"))) {
                    sendHtml(exchange, 403, page("Request rejected", "<h1>Request token is invalid</h1>"));
                    return;
                }
                handlePost(exchange, session, path, form);
            } else {
                exchange.getResponseHeaders().set("Allow", "GET, POST");
                sendHtml(exchange, 405, page("Method not allowed", "<h1>Method not allowed</h1>"));
            }
        } catch (Forbidden ex) {
            redirect(exchange, "/login");
        } catch (Exception ex) {
            ex.printStackTrace(System.err);
            sendHtml(exchange, 400, page("Request failed", "<h1>Request could not be completed</h1><p>"
                    + esc(Objects.toString(ex.getMessage(), "Please check your input.")) + "</p><p><a href='/books'>Back to catalogue</a></p>"));
        } finally {
            exchange.close();
        }
    }

    private static void handlePost(HttpExchange x, Session session, String path, Map<String, String> form) throws Exception {
        switch (path) {
            case "/login" -> login(x, session, form);
            case "/register" -> register(x, form);
            case "/logout" -> { session.user = null; redirect(x, "/"); }
            case "/issue" -> { issue(requireRole(session, "USER"), integer(form, "bookId")); redirect(x, "/books"); }
            case "/reserve" -> { reserve(requireRole(session, "USER"), integer(form, "bookId")); redirect(x, "/books"); }
            case "/return" -> { returnBook(requireRole(session, "USER"), integer(form, "loanId")); redirect(x, "/books"); }
            case "/query" -> { submitQuery(requireRole(session, "USER"), form); redirect(x, "/books"); }
            case "/admin/book/save" -> { saveBook(requireRole(session, "ADMIN"), form); redirect(x, "/admin"); }
            case "/admin/book/delete" -> { deleteBook(requireRole(session, "ADMIN"), integer(form, "bookId")); redirect(x, "/admin"); }
            case "/admin/fine/paid" -> { markFinePaid(requireRole(session, "ADMIN"), integer(form, "fineId")); redirect(x, "/admin"); }
            case "/admin/member/toggle" -> { toggleMember(requireRole(session, "ADMIN"), integer(form, "userId")); redirect(x, "/admin"); }
            default -> sendHtml(x, 404, page("Not found", "<h1>Action not found</h1>"));
        }
    }

    private static void login(HttpExchange x, Session session, Map<String, String> form) throws Exception {
        String username = required(form, "username", 32);
        char[] password = form.getOrDefault("password", "").toCharArray();
        try (Connection c = connect(); PreparedStatement p = c.prepareStatement(
                "SELECT id, username, display_name, salt, password_hash, role FROM users WHERE username=? AND active=1")) {
            p.setString(1, username);
            try (ResultSet rs = p.executeQuery()) {
                if (!rs.next() || !verifyPassword(password, rs.getString("salt"), rs.getString("password_hash"))) {
                    sendHtml(x, 401, loginPage(session, "Invalid username or password."));
                    return;
                }
                session.user = new User(rs.getInt("id"), rs.getString("username"),
                        rs.getString("display_name"), rs.getString("role"));
            }
        } finally { Arrays.fill(password, '\0'); }
        redirect(x, "/books");
    }

    private static void register(HttpExchange x, Map<String, String> form) throws Exception {
        String username = required(form, "username", 32);
        if (!username.matches("[A-Za-z0-9._-]{3,32}"))
            throw new IllegalArgumentException("Username must be 3–32 letters, digits, dots, underscores or hyphens.");
        String display = required(form, "displayName", 60);
        char[] password = form.getOrDefault("password", "").toCharArray();
        if (password.length < 10 || password.length > 128) {
            Arrays.fill(password, '\0');
            throw new IllegalArgumentException("Password must contain 10–128 characters.");
        }
        byte[] salt = salt();
        try (Connection c = connect(); PreparedStatement p = c.prepareStatement(
                "INSERT INTO users(username, display_name, salt, password_hash, role) VALUES(?, ?, ?, ?, 'USER')")) {
            p.setString(1, username);
            p.setString(2, display);
            p.setString(3, Base64.getEncoder().encodeToString(salt));
            p.setString(4, passwordHash(password, salt));
            p.executeUpdate();
        } finally { Arrays.fill(password, '\0'); }
        redirect(x, "/login");
    }

    private static String catalogue(Session session, String search, String category) throws SQLException {
        StringBuilder body = new StringBuilder("<h1>Book catalogue</h1><form method='get' action='/books'>"
                + "<label>Title or author <input name='q' value='" + esc(search) + "'></label> "
                + "<label>Category <input name='category' value='" + esc(category) + "'></label> <button>Search</button></form>");
        User user = session.user;
        if (user == null) body.append("<p><a href='/login'>Sign in</a> or <a href='/register'>create an account</a> to issue books.</p>");
        try (Connection c = connect(); PreparedStatement p = c.prepareStatement("""
                SELECT b.id, b.title, b.author, b.isbn, b.category, b.quantity,
                       b.quantity - (SELECT COUNT(*) FROM loans l WHERE l.book_id=b.id AND l.returned_on IS NULL) AS available
                FROM books b
                WHERE (?='' OR LOWER(b.title) LIKE LOWER(?) OR LOWER(b.author) LIKE LOWER(?))
                  AND (?='' OR LOWER(b.category)=LOWER(?))
                ORDER BY b.title""")) {
            p.setString(1, search);
            p.setString(2, "%" + search + "%");
            p.setString(3, "%" + search + "%");
            p.setString(4, category);
            p.setString(5, category);
            try (ResultSet rs = p.executeQuery()) {
                body.append("<div class='books'>");
                while (rs.next()) {
                    int id = rs.getInt("id");
                    int available = rs.getInt("available");
                    body.append("<article><h2>").append(esc(rs.getString("title"))).append("</h2><p>")
                            .append(esc(rs.getString("author"))).append(" · ").append(esc(rs.getString("category")))
                            .append("</p><p>ISBN ").append(esc(rs.getString("isbn"))).append(" · ")
                            .append(available).append(" available of ").append(rs.getInt("quantity")).append("</p>");
                    if (user != null && user.role.equals("USER")) {
                        if (available > 0) body.append(formButton(session, "/issue", "bookId", id, "Issue (14 days)"));
                        else body.append(formButton(session, "/reserve", "bookId", id, "Reserve next available copy"));
                    }
                    body.append("</article>");
                }
                body.append("</div>");
            }
        }
        if (user != null && user.role.equals("USER")) {
            body.append("<h2>Your loans</h2>");
            try (Connection c = connect(); PreparedStatement p = c.prepareStatement("""
                    SELECT l.id, b.title, l.issued_on, l.due_on FROM loans l JOIN books b ON b.id=l.book_id
                    WHERE l.user_id=? AND l.returned_on IS NULL ORDER BY l.due_on""")) {
                p.setInt(1, user.id);
                try (ResultSet rs = p.executeQuery()) {
                    body.append("<table><tr><th>Title</th><th>Issued</th><th>Due</th><th></th></tr>");
                    while (rs.next()) body.append("<tr><td>").append(esc(rs.getString(2))).append("</td><td>")
                            .append(esc(rs.getString(3))).append("</td><td>").append(esc(rs.getString(4)))
                            .append("</td><td>").append(formButton(session, "/return", "loanId", rs.getInt(1), "Return")).append("</td></tr>");
                    body.append("</table>");
                }
            }
            body.append("<h2>Fines</h2>");
            try (Connection c = connect(); PreparedStatement p = c.prepareStatement(
                    "SELECT amount_cents, paid, created_at FROM fines WHERE user_id=? ORDER BY id DESC")) {
                p.setInt(1, user.id);
                try (ResultSet rs = p.executeQuery()) {
                    body.append("<ul>");
                    while (rs.next()) body.append("<li>₹").append(rs.getLong(1) / 100).append(" — ")
                            .append(rs.getInt(2) == 1 ? "paid" : "unpaid").append(" (")
                            .append(esc(rs.getString(3))).append(")</li>");
                    body.append("</ul>");
                }
            }
            body.append("<h2>Advance reservations</h2>");
            try (Connection c = connect(); PreparedStatement p = c.prepareStatement("""
                    SELECT b.title, r.status, r.created_at FROM reservations r JOIN books b ON b.id=r.book_id
                    WHERE r.user_id=? ORDER BY r.created_at DESC LIMIT 20""")) {
                p.setInt(1, user.id);
                try (ResultSet rs = p.executeQuery()) {
                    body.append("<ul>");
                    while (rs.next()) body.append("<li>").append(esc(rs.getString(1))).append(" — ")
                            .append(esc(rs.getString(2))).append(" (").append(esc(rs.getString(3))).append(")</li>");
                    body.append("</ul>");
                }
            }
            body.append("<h2>Contact the library</h2><form method='post' action='/query'>").append(csrf(session))
                    .append("<label>Subject <input name='subject' maxlength='100' required></label>")
                    .append("<label>Message <textarea name='message' maxlength='2000' required></textarea></label><button>Send query</button></form>");
        }
        return page("Catalogue", body.toString(), session);
    }

    private static void issue(User user, int bookId) throws Exception {
        try (Connection c = connect()) {
            c.setAutoCommit(false);
            try {
                int available = available(c, bookId);
                if (available < 1) throw new IllegalArgumentException("No copies are currently available.");
                long reservationId = -1;
                try (PreparedStatement p = c.prepareStatement("""
                        SELECT id, user_id FROM reservations WHERE book_id=? AND status='WAITING'
                        ORDER BY created_at, id LIMIT 1""")) {
                    p.setInt(1, bookId);
                    try (ResultSet rs = p.executeQuery()) {
                        if (rs.next()) {
                            if (rs.getInt("user_id") != user.id)
                                throw new IllegalArgumentException("A reservation is ahead of you in the queue.");
                            reservationId = rs.getLong("id");
                        }
                    }
                }
                LocalDate today = LocalDate.now();
                try (PreparedStatement p = c.prepareStatement(
                        "INSERT INTO loans(user_id, book_id, issued_on, due_on) VALUES(?, ?, ?, ?)")) {
                    p.setInt(1, user.id); p.setInt(2, bookId); p.setString(3, today.toString());
                    p.setString(4, today.plusDays(14).toString()); p.executeUpdate();
                }
                if (reservationId >= 0) {
                    try (PreparedStatement p = c.prepareStatement("UPDATE reservations SET status='FULFILLED' WHERE id=?")) {
                        p.setLong(1, reservationId); p.executeUpdate();
                    }
                }
                c.commit();
            } catch (Exception ex) {
                c.rollback();
                throw ex;
            } finally { c.setAutoCommit(true); }
        }
    }

    private static void reserve(User user, int bookId) throws SQLException {
        try (Connection c = connect()) {
            if (available(c, bookId) > 0)
                throw new IllegalArgumentException("A copy is available; issue it from the catalogue instead.");
        }
        try (Connection c = connect(); PreparedStatement p = c.prepareStatement("""
                INSERT INTO reservations(user_id, book_id, status) VALUES(?, ?, 'WAITING')
                ON CONFLICT(user_id, book_id, status) DO NOTHING""")) {
            p.setInt(1, user.id); p.setInt(2, bookId); p.executeUpdate();
        }
    }

    private static int available(Connection c, int bookId) throws SQLException {
        try (PreparedStatement p = c.prepareStatement("""
                SELECT b.quantity - (SELECT COUNT(*) FROM loans l WHERE l.book_id=b.id AND l.returned_on IS NULL)
                FROM books b WHERE b.id=?""")) {
            p.setInt(1, bookId);
            try (ResultSet rs = p.executeQuery()) {
                if (!rs.next()) throw new IllegalArgumentException("Book not found.");
                return rs.getInt(1);
            }
        }
    }

    private static void returnBook(User user, int loanId) throws Exception {
        try (Connection c = connect()) {
            c.setAutoCommit(false);
            try {
                LocalDate due;
                try (PreparedStatement p = c.prepareStatement("""
                        SELECT due_on FROM loans WHERE id=? AND user_id=? AND returned_on IS NULL""")) {
                    p.setInt(1, loanId); p.setInt(2, user.id);
                    try (ResultSet rs = p.executeQuery()) {
                        if (!rs.next()) throw new IllegalArgumentException("Active loan not found.");
                        due = LocalDate.parse(rs.getString(1));
                    }
                }
                LocalDate today = LocalDate.now();
                try (PreparedStatement p = c.prepareStatement(
                        "UPDATE loans SET returned_on=? WHERE id=? AND user_id=? AND returned_on IS NULL")) {
                    p.setString(1, today.toString()); p.setInt(2, loanId); p.setInt(3, user.id);
                    if (p.executeUpdate() != 1) throw new IllegalArgumentException("Loan has already been returned.");
                }
                long daysLate = Math.max(0, ChronoUnit.DAYS.between(due, today));
                if (daysLate > 0) {
                    try (PreparedStatement p = c.prepareStatement(
                            "INSERT INTO fines(loan_id, user_id, amount_cents) VALUES(?, ?, ?)")) {
                        p.setInt(1, loanId); p.setInt(2, user.id); p.setLong(3, Math.multiplyExact(daysLate, 500));
                        p.executeUpdate();
                    }
                }
                c.commit();
            } catch (Exception ex) {
                c.rollback();
                throw ex;
            } finally { c.setAutoCommit(true); }
        }
    }

    private static void submitQuery(User user, Map<String, String> form) throws SQLException {
        String subject = required(form, "subject", 100);
        String message = required(form, "message", 2000);
        try (Connection c = connect(); PreparedStatement p = c.prepareStatement(
                "INSERT INTO queries(user_id, subject, message) VALUES(?, ?, ?)")) {
            p.setInt(1, user.id); p.setString(2, subject); p.setString(3, message); p.executeUpdate();
        }
    }

    private static String adminPage(User admin, Session session) throws SQLException {
        StringBuilder body = new StringBuilder("<h1>Admin dashboard</h1><h2>Add or edit a book</h2>")
                .append("<form method='post' action='/admin/book/save'>").append(csrf(session))
                .append("<input type='hidden' name='bookId' value=''>")
                .append("<label>Title <input name='title' maxlength='160' required></label>")
                .append("<label>Author <input name='author' maxlength='120' required></label>")
                .append("<label>ISBN <input name='isbn' maxlength='32' required></label>")
                .append("<label>Category <input name='category' maxlength='60' required></label>")
                .append("<label>Total quantity <input name='quantity' type='number' min='0' required></label><button>Save book</button></form>");
        try (Connection c = connect(); PreparedStatement p = c.prepareStatement("SELECT id, title, author, isbn, category, quantity FROM books ORDER BY title");
             ResultSet rs = p.executeQuery()) {
            body.append("<h2>Manage catalogue</h2><table><tr><th>Title</th><th>Author</th><th>ISBN</th><th>Category</th><th>Total</th><th></th></tr>");
            while (rs.next()) body.append("<tr><td>").append(esc(rs.getString(2))).append("</td><td>")
                    .append(esc(rs.getString(3))).append("</td><td>").append(esc(rs.getString(4))).append("</td><td>")
                    .append(esc(rs.getString(5))).append("</td><td>").append(rs.getInt(6)).append("</td><td>")
                    .append("<details><summary>Edit</summary><form method='post' action='/admin/book/save'>")
                    .append(csrf(session)).append("<input type='hidden' name='bookId' value='").append(rs.getInt(1)).append("'>")
                    .append("<label>Title <input name='title' maxlength='160' value='").append(esc(rs.getString(2))).append("' required></label>")
                    .append("<label>Author <input name='author' maxlength='120' value='").append(esc(rs.getString(3))).append("' required></label>")
                    .append("<label>ISBN <input name='isbn' maxlength='32' value='").append(esc(rs.getString(4))).append("' required></label>")
                    .append("<label>Category <input name='category' maxlength='60' value='").append(esc(rs.getString(5))).append("' required></label>")
                    .append("<label>Total quantity <input name='quantity' type='number' min='0' value='").append(rs.getInt(6))
                    .append("' required></label><button>Update</button></form></details>")
                    .append(formButton(session, "/admin/book/delete", "bookId", rs.getInt(1), "Delete")).append("</td></tr>");
            body.append("</table>");
        }
        try (Connection c = connect(); PreparedStatement p = c.prepareStatement("""
                SELECT l.id, u.username, b.title, l.issued_on, l.due_on FROM loans l
                JOIN users u ON u.id=l.user_id JOIN books b ON b.id=l.book_id
                WHERE l.returned_on IS NULL ORDER BY l.due_on"""); ResultSet rs = p.executeQuery()) {
            body.append("<h2>Active issued books</h2><table><tr><th>Member</th><th>Book</th><th>Issued</th><th>Due</th></tr>");
            while (rs.next()) body.append("<tr><td>").append(esc(rs.getString(2))).append("</td><td>")
                    .append(esc(rs.getString(3))).append("</td><td>").append(esc(rs.getString(4)))
                    .append("</td><td>").append(esc(rs.getString(5))).append("</td></tr>");
            body.append("</table>");
        }
        try (Connection c = connect(); PreparedStatement p = c.prepareStatement("""
                SELECT f.id, u.username, b.title, f.amount_cents, f.paid FROM fines f
                JOIN users u ON u.id=f.user_id JOIN loans l ON l.id=f.loan_id JOIN books b ON b.id=l.book_id
                ORDER BY f.id DESC"""); ResultSet rs = p.executeQuery()) {
            body.append("<h2>Fines</h2><table><tr><th>Member</th><th>Book</th><th>Fine</th><th>Status</th><th></th></tr>");
            while (rs.next()) {
                body.append("<tr><td>").append(esc(rs.getString(2))).append("</td><td>").append(esc(rs.getString(3)))
                        .append("</td><td>₹").append(rs.getLong(4) / 100).append("</td><td>")
                        .append(rs.getInt(5) == 1 ? "Paid" : "Unpaid").append("</td><td>");
                if (rs.getInt(5) == 0) body.append(formButton(session, "/admin/fine/paid", "fineId", rs.getInt(1), "Mark paid"));
                body.append("</td></tr>");
            }
            body.append("</table>");
        }
        try (Connection c = connect(); PreparedStatement p = c.prepareStatement(
                "SELECT id, username, display_name, role, active, created_at FROM users ORDER BY id"); ResultSet rs = p.executeQuery()) {
            body.append("<h2>Registered members</h2><table><tr><th>Username</th><th>Name</th><th>Role</th><th>Status</th><th>Joined</th><th>Action</th></tr>");
            while (rs.next()) {
                body.append("<tr><td>").append(esc(rs.getString(2))).append("</td><td>").append(esc(rs.getString(3)))
                        .append("</td><td>").append(esc(rs.getString(4))).append("</td><td>")
                        .append(rs.getInt(5) == 1 ? "Active" : "Disabled").append("</td><td>").append(esc(rs.getString(6)))
                        .append("</td><td>");
                if (rs.getString(4).equals("USER"))
                    body.append(formButton(session, "/admin/member/toggle", "userId", rs.getInt(1),
                            rs.getInt(5) == 1 ? "Disable" : "Enable"));
                body.append("</td></tr>");
            }
            body.append("</table>");
        }
        try (Connection c = connect(); PreparedStatement p = c.prepareStatement("""
                SELECT u.username, q.subject, q.message, q.created_at FROM queries q JOIN users u ON u.id=q.user_id
                ORDER BY q.id DESC LIMIT 100"""); ResultSet rs = p.executeQuery()) {
            body.append("<h2>Member queries</h2><div class='books'>");
            while (rs.next()) body.append("<article><b>").append(esc(rs.getString(2))).append("</b><p>From ")
                    .append(esc(rs.getString(1))).append(" · ").append(esc(rs.getString(4))).append("</p><p>")
                    .append(esc(rs.getString(3))).append("</p></article>");
            body.append("</div>");
        }
        return page("Admin dashboard", body.toString(), session);
    }

    private static void saveBook(User admin, Map<String, String> f) throws SQLException {
        String title = required(f, "title", 160);
        String author = required(f, "author", 120);
        String isbn = required(f, "isbn", 32);
        String category = required(f, "category", 60);
        int quantity = integer(f, "quantity");
        if (quantity < 0 || quantity > 100_000) throw new IllegalArgumentException("Quantity must be between 0 and 100000.");
        String id = f.getOrDefault("bookId", "").trim();
        if (id.isEmpty()) {
            try (Connection c = connect(); PreparedStatement p = c.prepareStatement(
                    "INSERT INTO books(title, author, isbn, category, quantity) VALUES(?, ?, ?, ?, ?)")) {
                p.setString(1, title); p.setString(2, author); p.setString(3, isbn);
                p.setString(4, category); p.setInt(5, quantity); p.executeUpdate();
            }
        } else {
            int bookId = Integer.parseInt(id);
            try (Connection c = connect()) {
                try (PreparedStatement activeLoans = c.prepareStatement(
                        "SELECT COUNT(*) FROM loans WHERE book_id=? AND returned_on IS NULL")) {
                    activeLoans.setInt(1, bookId);
                    try (ResultSet rs = activeLoans.executeQuery()) {
                        if (rs.next() && quantity < rs.getInt(1))
                            throw new IllegalArgumentException("Quantity cannot be lower than the number of books currently issued.");
                    }
                }
                try (PreparedStatement p = c.prepareStatement(
                        "UPDATE books SET title=?, author=?, isbn=?, category=?, quantity=? WHERE id=?")) {
                p.setString(1, title); p.setString(2, author); p.setString(3, isbn);
                p.setString(4, category); p.setInt(5, quantity); p.setInt(6, bookId);
                if (p.executeUpdate() != 1) throw new IllegalArgumentException("Book not found.");
                }
            }
        }
    }

    private static void deleteBook(User admin, int bookId) throws SQLException {
        try (Connection c = connect(); PreparedStatement p = c.prepareStatement(
                "DELETE FROM books WHERE id=? AND NOT EXISTS(SELECT 1 FROM loans WHERE book_id=?) " +
                        "AND NOT EXISTS(SELECT 1 FROM reservations WHERE book_id=?)")) {
            p.setInt(1, bookId); p.setInt(2, bookId); p.setInt(3, bookId);
            if (p.executeUpdate() != 1) throw new IllegalArgumentException("Book not found or has loan history; it cannot be deleted.");
        }
    }

    private static void toggleMember(User admin, int userId) throws SQLException {
        try (Connection c = connect(); PreparedStatement p = c.prepareStatement(
                "UPDATE users SET active=1-active WHERE id=? AND role='USER' AND id<>?")) {
            p.setInt(1, userId); p.setInt(2, admin.id);
            if (p.executeUpdate() != 1) throw new IllegalArgumentException("Member not found or cannot be disabled.");
        }
        try (Connection c = connect(); PreparedStatement p = c.prepareStatement(
                "SELECT active FROM users WHERE id=?")) {
            p.setInt(1, userId);
            try (ResultSet rs = p.executeQuery()) {
                if (rs.next() && rs.getInt(1) == 0)
                    SESSIONS.entrySet().removeIf(entry -> entry.getValue().user != null
                            && entry.getValue().user.id == userId);
            }
        }
    }

    private static void markFinePaid(User admin, int fineId) throws SQLException {
        try (Connection c = connect(); PreparedStatement p = c.prepareStatement("UPDATE fines SET paid=1 WHERE id=?")) {
            p.setInt(1, fineId);
            if (p.executeUpdate() != 1) throw new IllegalArgumentException("Fine not found.");
        }
    }

    private static Session session(HttpExchange x) {
        String token = null;
        List<String> cookies = x.getRequestHeaders().get("Cookie");
        if (cookies != null) {
            for (String header : cookies) for (String cookie : header.split(";")) {
                String[] pair = cookie.trim().split("=", 2);
                if (pair.length == 2 && pair[0].equals("OASISSESSION")) token = pair[1];
            }
        }
        Session session = token == null ? null : SESSIONS.get(token);
        if (session == null) {
            token = newSecret();
            session = new Session(null, newSecret());
            SESSIONS.put(token, session);
            x.getResponseHeaders().add("Set-Cookie", "OASISSESSION=" + token + "; Path=/; HttpOnly; SameSite=Strict");
        }
        return session;
    }

    private static User requireRole(Session session, String role) {
        if (session.user == null || !session.user.role.equals(role)) throw new Forbidden();
        return session.user;
    }

    private static Map<String, String> readForm(HttpExchange x) throws IOException {
        String raw = new String(x.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
        Map<String, String> result = new HashMap<>();
        for (String pair : raw.split("&")) {
            if (pair.isEmpty()) continue;
            String[] parts = pair.split("=", 2);
            result.put(URLDecoder.decode(parts[0], StandardCharsets.UTF_8),
                    URLDecoder.decode(parts.length == 2 ? parts[1] : "", StandardCharsets.UTF_8));
        }
        return result;
    }

    private static String query(HttpExchange x, String key) {
        String query = x.getRequestURI().getRawQuery();
        if (query == null) return "";
        for (String pair : query.split("&")) {
            String[] parts = pair.split("=", 2);
            if (URLDecoder.decode(parts[0], StandardCharsets.UTF_8).equals(key))
                return URLDecoder.decode(parts.length == 2 ? parts[1] : "", StandardCharsets.UTF_8);
        }
        return "";
    }

    private static int integer(Map<String, String> form, String key) {
        try { return Integer.parseInt(required(form, key, 16)); }
        catch (NumberFormatException ex) { throw new IllegalArgumentException("Invalid number for " + key + "."); }
    }

    private static String required(Map<String, String> form, String key, int maxLength) {
        String value = form.getOrDefault(key, "").trim();
        if (value.isEmpty() || value.length() > maxLength)
            throw new IllegalArgumentException(key + " is required and must be at most " + maxLength + " characters.");
        return value;
    }

    private static String formButton(Session session, String action, String field, int value, String label) {
        return "<form class='inline' method='post' action='" + action + "'>" + csrf(session) + "<input type='hidden' name='" + field
                + "' value='" + value + "'><button>" + esc(label) + "</button></form>";
    }

    private static StringBuilder csrf(Session session) {
        return new StringBuilder("<input type='hidden' name='csrf' value='").append(esc(session.csrf)).append("'>");
    }

    private static String loginPage(Session session, String error) {
        return page("Sign in", "<h1>Library sign in</h1>" + message(error)
                + "<form method='post' action='/login'>" + csrf(session)
                + "<label>Username <input name='username' maxlength='32' required autocomplete='username'></label>"
                + "<label>Password <input type='password' name='password' required autocomplete='current-password'></label>"
                + "<button>Sign in</button></form><p><a href='/register'>Create a member account</a></p>", session);
    }

    private static String registerPage(Session session, String error) {
        return page("Register", "<h1>Create a member account</h1>" + message(error)
                + "<form method='post' action='/register'>" + csrf(session)
                + "<label>Display name <input name='displayName' maxlength='60' required></label>"
                + "<label>Username <input name='username' maxlength='32' required autocomplete='username'></label>"
                + "<label>Password (10+ characters) <input type='password' name='password' minlength='10' maxlength='128' required autocomplete='new-password'></label>"
                + "<button>Register</button></form>", session);
    }

    private static String message(String text) {
        return text.isEmpty() ? "" : "<p class='error'>" + esc(text) + "</p>";
    }

    private static String page(String title, String body) { return page(title, body, new Session(null, "")); }

    private static String page(String title, String body, Session session) {
        String nav = "<header><a class='brand' href='/books'>Oasis Library</a><nav><a href='/books'>Catalogue</a>";
        if (session.user == null) nav += "<a href='/login'>Sign in</a><a href='/register'>Register</a>";
        else if (session.user.role.equals("ADMIN")) nav += "<a href='/admin'>Admin</a>";
        else nav += "<span>Signed in as " + esc(session.user.displayName) + "</span>";
        if (session.user != null) nav += "<form class='inline' method='post' action='/logout'>" + csrf(session)
                + "<button class='quiet'>Sign out</button></form>";
        nav += "</nav></header>";
        return "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
                + "<title>" + esc(title) + " · Oasis Library</title><style>" + CSS + "</style></head><body>"
                + nav + "<main>" + body + "</main><footer>Oasis Digital Library · Demo application · Late return fine ₹5/day</footer></body></html>";
    }

    private static void sendHtml(HttpExchange x, int status, String html) throws IOException {
        byte[] bytes = html.getBytes(StandardCharsets.UTF_8);
        x.getResponseHeaders().set("Content-Type", "text/html; charset=utf-8");
        x.getResponseHeaders().set("X-Content-Type-Options", "nosniff");
        x.getResponseHeaders().set("Content-Security-Policy", "default-src 'self'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'");
        x.getResponseHeaders().set("Cache-Control", "no-store");
        x.sendResponseHeaders(status, bytes.length);
        x.getResponseBody().write(bytes);
    }

    private static void redirect(HttpExchange x, String target) throws IOException {
        x.getResponseHeaders().set("Location", target);
        x.sendResponseHeaders(303, -1);
    }

    private static String esc(String value) {
        if (value == null) return "";
        return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace("\"", "&quot;").replace("'", "&#39;");
    }

    private static byte[] salt() {
        byte[] value = new byte[16];
        RANDOM.nextBytes(value);
        return value;
    }

    private static String passwordHash(char[] password, byte[] salt) {
        PBEKeySpec spec = new PBEKeySpec(password, salt, 180_000, 256);
        try {
            return Base64.getEncoder().encodeToString(
                    SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256").generateSecret(spec).getEncoded());
        } catch (GeneralSecurityException ex) {
            throw new IllegalStateException("Password hashing is unavailable.", ex);
        } finally { spec.clearPassword(); }
    }

    private static boolean verifyPassword(char[] password, String encodedSalt, String expected) {
        byte[] actual = Base64.getDecoder().decode(passwordHash(password, Base64.getDecoder().decode(encodedSalt)));
        return MessageDigest.isEqual(actual, Base64.getDecoder().decode(expected));
    }

    private static String newSecret() {
        byte[] bytes = new byte[24];
        RANDOM.nextBytes(bytes);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
    }

    private static final String CSS = """
            :root{font:16px/1.5 system-ui,sans-serif;color:#14251f;background:#f3f6f2}
            *{box-sizing:border-box}body{margin:0}header{background:#163d34;color:white;padding:14px max(5vw,20px);display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap}
            nav{display:flex;align-items:center;gap:18px;flex-wrap:wrap}a{color:#17665a}header a{color:white;text-decoration:none}.brand{font-size:1.3rem;font-weight:700}
            main{max-width:1100px;margin:32px auto;padding:0 20px;min-height:70vh}h1{color:#174a3f}form:not(.inline){display:grid;gap:12px;max-width:540px;background:white;padding:18px;border-radius:12px;margin:16px 0}
            label{display:grid;gap:5px}input,textarea{font:inherit;padding:9px;border:1px solid #aebdb6;border-radius:6px}textarea{min-height:110px}
            button{font:inherit;color:white;background:#17665a;border:0;border-radius:6px;padding:8px 13px;cursor:pointer}button:hover{background:#0d4b42}.quiet{background:transparent}
            .inline{display:inline}table{width:100%;border-collapse:collapse;background:white;margin:14px 0}td,th{padding:9px;border-bottom:1px solid #dbe3df;text-align:left;vertical-align:top}
            .books{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;margin:20px 0}article{background:white;padding:16px;border-radius:12px;box-shadow:0 2px 9px #163d3410}
            article h2{margin-top:0;font-size:1.1rem}.error{color:#a32222}footer{text-align:center;padding:20px;color:#53675f}
            @media(max-width:600px){header{align-items:flex-start}nav{gap:10px}main{margin:18px auto;padding:0 14px}table{font-size:.87rem}}
            """;

    private record User(int id, String username, String displayName, String role) {}
    private static final class Session {
        private User user;
        private final String csrf;
        private Session(User user, String csrf) { this.user = user; this.csrf = csrf; }
    }
    private static final class Forbidden extends RuntimeException {}
}

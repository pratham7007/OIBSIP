package com.oasis.train;

import javax.swing.*;
import java.awt.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.*;
import java.sql.*;
import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.*;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;

public final class TrainReservationApp {
    private TrainReservationApp() {}

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            try {
                Database.initialize();
                new LoginWindow().setVisible(true);
            } catch (Exception ex) {
                JOptionPane.showMessageDialog(null, "Could not open the reservation database:\n" + ex.getMessage(),
                        "Startup error", JOptionPane.ERROR_MESSAGE);
            }
        });
    }

    private static final class Database {
        private static final String URL;
        static {
            try {
                Path folder = Path.of("data");
                Files.createDirectories(folder);
                URL = "jdbc:sqlite:" + folder.resolve("train-reservations.db").toAbsolutePath();
            } catch (Exception ex) {
                throw new ExceptionInInitializerError(ex);
            }
        }

        static Connection connect() throws SQLException {
            Connection connection = DriverManager.getConnection(URL);
            try (Statement statement = connection.createStatement()) {
                statement.execute("PRAGMA foreign_keys = ON");
            }
            return connection;
        }

        static void initialize() throws SQLException {
            try (Connection c = connect(); Statement s = c.createStatement()) {
                s.executeUpdate("""
                    CREATE TABLE IF NOT EXISTS users (
                      id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE,
                      salt TEXT NOT NULL, password_hash TEXT NOT NULL
                    )""");
                s.executeUpdate("""
                    CREATE TABLE IF NOT EXISTS trains (
                      train_number TEXT PRIMARY KEY, train_name TEXT NOT NULL
                    )""");
                s.executeUpdate("""
                    CREATE TABLE IF NOT EXISTS bookings (
                      pnr INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id),
                      passenger_name TEXT NOT NULL, train_number TEXT NOT NULL REFERENCES trains(train_number),
                      train_name TEXT NOT NULL, class_type TEXT NOT NULL, journey_date TEXT NOT NULL,
                      source TEXT NOT NULL, destination TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )""");
            }
            try (Connection c = connect(); PreparedStatement p = c.prepareStatement(
                    "INSERT OR IGNORE INTO trains(train_number, train_name) VALUES(?, ?)")) {
                String[][] trains = {{"12001", "Deccan Express"}, {"12951", "Mumbai Rajdhani"},
                        {"12627", "Karnataka Express"}, {"12123", "Deccan Queen"}};
                for (String[] train : trains) {
                    p.setString(1, train[0]);
                    p.setString(2, train[1]);
                    p.addBatch();
                }
                p.executeBatch();
            }
        }

        static boolean register(String username, char[] password) throws SQLException {
            byte[] salt = Passwords.salt();
            try (Connection c = connect(); PreparedStatement p = c.prepareStatement(
                    "INSERT INTO users(username, salt, password_hash) VALUES(?, ?, ?)")) {
                p.setString(1, username);
                p.setString(2, Base64.getEncoder().encodeToString(salt));
                p.setString(3, Passwords.hash(password, salt));
                p.executeUpdate();
                return true;
            }
        }

        static OptionalInt authenticate(String username, char[] password) throws SQLException {
            try (Connection c = connect(); PreparedStatement p = c.prepareStatement(
                    "SELECT id, salt, password_hash FROM users WHERE username = ?")) {
                p.setString(1, username);
                try (ResultSet rs = p.executeQuery()) {
                    if (!rs.next()) return OptionalInt.empty();
                    byte[] salt = Base64.getDecoder().decode(rs.getString("salt"));
                    return Passwords.matches(password, salt, rs.getString("password_hash"))
                            ? OptionalInt.of(rs.getInt("id")) : OptionalInt.empty();
                }
            }
        }

        static java.util.List<Train> trains() throws SQLException {
            java.util.List<Train> result = new ArrayList<>();
            try (Connection c = connect(); PreparedStatement p = c.prepareStatement(
                    "SELECT train_number, train_name FROM trains ORDER BY train_number");
                 ResultSet rs = p.executeQuery()) {
                while (rs.next()) result.add(new Train(rs.getString(1), rs.getString(2)));
            }
            return result;
        }

        static long book(int userId, String passenger, Train train, String coach, LocalDate date,
                         String source, String destination) throws SQLException {
            try (Connection c = connect(); PreparedStatement p = c.prepareStatement("""
                    INSERT INTO bookings(user_id, passenger_name, train_number, train_name, class_type,
                                         journey_date, source, destination)
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?)""", Statement.RETURN_GENERATED_KEYS)) {
                p.setInt(1, userId);
                p.setString(2, passenger);
                p.setString(3, train.number());
                p.setString(4, train.name());
                p.setString(5, coach);
                p.setString(6, date.toString());
                p.setString(7, source);
                p.setString(8, destination);
                p.executeUpdate();
                try (ResultSet keys = p.getGeneratedKeys()) {
                    if (keys.next()) return keys.getLong(1);
                }
            }
            throw new SQLException("The database did not return a PNR.");
        }

        static Optional<Booking> booking(int userId, long pnr) throws SQLException {
            try (Connection c = connect(); PreparedStatement p = c.prepareStatement("""
                    SELECT pnr, passenger_name, train_number, train_name, class_type, journey_date, source, destination
                    FROM bookings WHERE user_id = ? AND pnr = ?""")) {
                p.setInt(1, userId);
                p.setLong(2, pnr);
                try (ResultSet rs = p.executeQuery()) {
                    if (!rs.next()) return Optional.empty();
                    return Optional.of(new Booking(rs.getLong(1), rs.getString(2), rs.getString(3),
                            rs.getString(4), rs.getString(5), rs.getString(6), rs.getString(7), rs.getString(8)));
                }
            }
        }

        static boolean cancel(int userId, long pnr) throws SQLException {
            try (Connection c = connect(); PreparedStatement p = c.prepareStatement(
                    "DELETE FROM bookings WHERE user_id = ? AND pnr = ?")) {
                p.setInt(1, userId);
                p.setLong(2, pnr);
                return p.executeUpdate() == 1;
            }
        }
    }

    private static final class Passwords {
        private static byte[] salt() {
            byte[] salt = new byte[16];
            new SecureRandom().nextBytes(salt);
            return salt;
        }

        private static String hash(char[] password, byte[] salt) {
            PBEKeySpec spec = new PBEKeySpec(password, salt, 160_000, 256);
            try {
                return Base64.getEncoder().encodeToString(
                        SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256").generateSecret(spec).getEncoded());
            } catch (GeneralSecurityException ex) {
                throw new IllegalStateException("Password hashing is unavailable.", ex);
            } finally {
                spec.clearPassword();
            }
        }

        private static boolean matches(char[] password, byte[] salt, String expected) {
            byte[] actual = Base64.getDecoder().decode(hash(password, salt));
            return MessageDigest.isEqual(actual, Base64.getDecoder().decode(expected));
        }
    }

    private record Train(String number, String name) {
        @Override public String toString() { return number + " — " + name; }
    }
    private record Booking(long pnr, String passenger, String trainNumber, String trainName,
                           String coach, String date, String source, String destination) {
        String details() {
            return "PNR: " + pnr + "\nPassenger: " + passenger + "\nTrain: " + trainNumber + " — " + trainName
                    + "\nClass: " + coach + "\nJourney date: " + date + "\nRoute: " + source + " → " + destination;
        }
    }

    private static final class LoginWindow extends JFrame {
        private final JTextField username = new JTextField(18);
        private final JPasswordField password = new JPasswordField(18);

        LoginWindow() {
            super("Oasis Rail Reservations — Sign in");
            setDefaultCloseOperation(EXIT_ON_CLOSE);
            setSize(430, 250);
            setLocationRelativeTo(null);
            JPanel fields = new JPanel(new GridLayout(0, 2, 8, 10));
            fields.setBorder(BorderFactory.createEmptyBorder(24, 28, 12, 28));
            fields.add(new JLabel("Username")); fields.add(username);
            fields.add(new JLabel("Password")); fields.add(password);
            JButton login = new JButton("Sign in");
            JButton register = new JButton("Create account");
            JPanel actions = new JPanel();
            actions.add(login); actions.add(register);
            add(fields, BorderLayout.CENTER); add(actions, BorderLayout.SOUTH);
            login.addActionListener(e -> signIn());
            register.addActionListener(e -> signUp());
            getRootPane().setDefaultButton(login);
        }

        private void signIn() {
            char[] chars = password.getPassword();
            try {
                OptionalInt id = Database.authenticate(username.getText().trim(), chars);
                if (id.isEmpty()) {
                    JOptionPane.showMessageDialog(this, "Access denied. Check your username and password.",
                            "Sign-in failed", JOptionPane.ERROR_MESSAGE);
                } else {
                    dispose();
                    new ReservationWindow(id.getAsInt(), username.getText().trim()).setVisible(true);
                }
            } catch (Exception ex) { showError(ex); }
            finally { Arrays.fill(chars, '\0'); password.setText(""); }
        }

        private void signUp() {
            String name = username.getText().trim();
            char[] chars = password.getPassword();
            try {
                if (!name.matches("[A-Za-z0-9._-]{3,32}") || chars.length < 10) {
                    JOptionPane.showMessageDialog(this,
                            "Use a 3–32 character username and a password of at least 10 characters.");
                    return;
                }
                Database.register(name, chars);
                JOptionPane.showMessageDialog(this, "Account created. Sign in to continue.");
                password.setText("");
            } catch (SQLException ex) {
                JOptionPane.showMessageDialog(this, "That username is already in use.", "Registration failed",
                        JOptionPane.WARNING_MESSAGE);
            } catch (Exception ex) { showError(ex); }
            finally { Arrays.fill(chars, '\0'); }
        }
    }

    private static final class ReservationWindow extends JFrame {
        private final int userId;
        private final JTextField passenger = new JTextField(20);
        private final JComboBox<Train> train = new JComboBox<>();
        private final JTextField trainName = new JTextField(20);
        private final JComboBox<String> coach = new JComboBox<>(new String[]{"Sleeper", "AC 3 Tier", "AC 2 Tier", "AC First Class"});
        private final JTextField date = new JTextField(20);
        private final JTextField source = new JTextField(20);
        private final JTextField destination = new JTextField(20);
        private final JTextField pnr = new JTextField(16);
        private final JTextArea bookingDetails = new JTextArea(7, 36);
        private Booking fetched;

        ReservationWindow(int userId, String username) {
            super("Oasis Rail Reservations — " + username);
            this.userId = userId;
            setDefaultCloseOperation(EXIT_ON_CLOSE);
            setSize(670, 520);
            setLocationRelativeTo(null);
            trainName.setEditable(false);
            bookingDetails.setEditable(false);
            bookingDetails.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 13));
            JTabbedPane tabs = new JTabbedPane();
            tabs.addTab("Book a journey", bookingPanel());
            tabs.addTab("Find / cancel PNR", cancellationPanel());
            add(tabs);
            try {
                for (Train item : Database.trains()) train.addItem(item);
            } catch (SQLException ex) { showError(ex); }
            train.addActionListener(e -> {
                Train selected = (Train) train.getSelectedItem();
                trainName.setText(selected == null ? "" : selected.name());
            });
        }

        private JPanel bookingPanel() {
            JPanel form = new JPanel(new GridBagLayout());
            form.setBorder(BorderFactory.createEmptyBorder(18, 30, 18, 30));
            GridBagConstraints g = new GridBagConstraints();
            g.insets = new Insets(6, 8, 6, 8); g.anchor = GridBagConstraints.WEST;
            addRow(form, g, 0, "Passenger name", passenger);
            addRow(form, g, 1, "Train number / name", train);
            addRow(form, g, 2, "Train name", trainName);
            addRow(form, g, 3, "Class", coach);
            date.setToolTipText("Enter the journey date as YYYY-MM-DD.");
            addRow(form, g, 4, "Journey date (YYYY-MM-DD)", date);
            addRow(form, g, 5, "From", source);
            addRow(form, g, 6, "To", destination);
            JButton book = new JButton("Book ticket");
            g.gridx = 1; g.gridy = 7; form.add(book, g);
            book.addActionListener(e -> createBooking());
            return form;
        }

        private JPanel cancellationPanel() {
            JPanel panel = new JPanel(new BorderLayout(8, 8));
            JPanel search = new JPanel();
            search.add(new JLabel("PNR")); search.add(pnr);
            JButton fetch = new JButton("Fetch booking"); search.add(fetch);
            bookingDetails.setBorder(BorderFactory.createEmptyBorder(12, 12, 12, 12));
            JButton cancel = new JButton("Confirm cancellation");
            cancel.setEnabled(false);
            JPanel bottom = new JPanel(); bottom.add(cancel);
            panel.setBorder(BorderFactory.createEmptyBorder(14, 18, 14, 18));
            panel.add(search, BorderLayout.NORTH);
            panel.add(new JScrollPane(bookingDetails), BorderLayout.CENTER);
            panel.add(bottom, BorderLayout.SOUTH);
            fetch.addActionListener(e -> fetchBooking(cancel));
            cancel.addActionListener(e -> cancelBooking(cancel));
            return panel;
        }

        private void createBooking() {
            String name = passenger.getText().trim();
            String from = source.getText().trim();
            String to = destination.getText().trim();
            Train selected = (Train) train.getSelectedItem();
            try {
                if (name.isBlank() || from.isBlank() || to.isBlank() || selected == null)
                    throw new IllegalArgumentException("Complete every required field.");
                if (from.equalsIgnoreCase(to)) throw new IllegalArgumentException("Source and destination must differ.");
                LocalDate journeyDate = LocalDate.parse(date.getText().trim());
                if (journeyDate.isBefore(LocalDate.now())) throw new IllegalArgumentException("Journey date cannot be in the past.");
                long reference = Database.book(userId, name, selected, Objects.toString(coach.getSelectedItem()),
                        journeyDate, from, to);
                Booking booking = Database.booking(userId, reference).orElseThrow();
                JOptionPane.showMessageDialog(this, booking.details(), "Booking confirmed", JOptionPane.INFORMATION_MESSAGE);
            } catch (DateTimeParseException ex) {
                JOptionPane.showMessageDialog(this, "Enter a valid date in YYYY-MM-DD format.");
            } catch (IllegalArgumentException ex) {
                JOptionPane.showMessageDialog(this, ex.getMessage());
            } catch (Exception ex) { showError(ex); }
        }

        private void fetchBooking(JButton cancel) {
            try {
                long reference = Long.parseLong(pnr.getText().trim());
                fetched = Database.booking(userId, reference).orElse(null);
                if (fetched == null) {
                    bookingDetails.setText("No booking found for this PNR on your account.");
                    cancel.setEnabled(false);
                } else {
                    bookingDetails.setText(fetched.details());
                    cancel.setEnabled(true);
                }
            } catch (NumberFormatException ex) {
                bookingDetails.setText("Enter a numeric PNR.");
                cancel.setEnabled(false);
            } catch (Exception ex) { showError(ex); }
        }

        private void cancelBooking(JButton cancel) {
            if (fetched == null) return;
            int choice = JOptionPane.showConfirmDialog(this, "Cancel this reservation?\n\n" + fetched.details(),
                    "Confirm cancellation", JOptionPane.YES_NO_OPTION, JOptionPane.WARNING_MESSAGE);
            if (choice != JOptionPane.YES_OPTION) return;
            try {
                if (Database.cancel(userId, fetched.pnr())) {
                    bookingDetails.setText("Booking cancelled.");
                    fetched = null;
                    cancel.setEnabled(false);
                } else {
                    bookingDetails.setText("This booking was already cancelled.");
                    cancel.setEnabled(false);
                }
            } catch (Exception ex) { showError(ex); }
        }

        private static void addRow(JPanel panel, GridBagConstraints g, int row, String label, Component field) {
            g.gridy = row; g.gridx = 0; panel.add(new JLabel(label), g);
            g.gridx = 1; panel.add(field, g);
        }
    }

    private static void showError(Exception ex) {
        JOptionPane.showMessageDialog(null, ex.getMessage(), "Operation failed", JOptionPane.ERROR_MESSAGE);
    }
}

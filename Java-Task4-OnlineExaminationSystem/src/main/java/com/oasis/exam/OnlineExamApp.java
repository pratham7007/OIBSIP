package com.oasis.exam;

import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;
import javax.swing.*;
import java.awt.*;
import java.security.*;
import java.time.Duration;
import java.util.*;

public final class OnlineExamApp {
    private OnlineExamApp() {}

    public static void main(String[] args) {
        String temporaryPassword = UUID.randomUUID().toString().replace("-", "").substring(0, 14) + "aA7!";
        Profile profile = Profile.createDemo(temporaryPassword.toCharArray());
        System.out.printf("Demo login: username=student password=%s%n", temporaryPassword);
        SwingUtilities.invokeLater(() -> new ExamFrame(profile).setVisible(true));
    }

    private static final class Profile {
        final String username;
        String displayName;
        byte[] salt;
        byte[] passwordHash;

        private Profile(String username, String displayName, byte[] salt, byte[] passwordHash) {
            this.username = username;
            this.displayName = displayName;
            this.salt = salt;
            this.passwordHash = passwordHash;
        }

        static Profile createDemo(char[] temporaryPassword) {
            byte[] salt = randomSalt();
            try {
                return new Profile("student", "Student", salt, hash(temporaryPassword, salt));
            } finally {
                Arrays.fill(temporaryPassword, '\0');
            }
        }

        boolean authenticate(char[] candidate) {
            return MessageDigest.isEqual(passwordHash, hash(candidate, salt));
        }

        void update(String name, char[] newPassword) {
            displayName = name;
            salt = randomSalt();
            passwordHash = hash(newPassword, salt);
        }
    }

    private record Question(String text, String[] choices, int answer, String explanation) {}

    private static final class ExamFrame extends JFrame {
        private static final int EXAM_SECONDS = Integer.getInteger("oasis.exam.minutes", 30) * 60;
        private final Profile profile;
        private final java.util.List<Question> questions = questions();
        private final int[] answers = new int[questions.size()];
        private int index;
        private int secondsRemaining = EXAM_SECONDS;
        private long startedAt;
        private final JLabel timerLabel = new JLabel();
        private final JLabel questionLabel = new JLabel();
        private final JLabel counterLabel = new JLabel();
        private final JRadioButton[] choices = new JRadioButton[4];
        private final ButtonGroup choiceGroup = new ButtonGroup();
        private final JPanel root = new JPanel(new CardLayout());
        private final JPanel loginPanel = new JPanel(new GridBagLayout());
        private final JPanel profilePanel = new JPanel(new GridBagLayout());
        private final JPanel examPanel = new JPanel(new BorderLayout(12, 12));
        private final JPanel resultPanel = new JPanel(new BorderLayout(12, 12));
        private final JPasswordField loginPassword = new JPasswordField(20);
        private final JTextField displayName = new JTextField(20);
        private final JPasswordField currentPassword = new JPasswordField(20);
        private final JPasswordField newPassword = new JPasswordField(20);
        private final javax.swing.Timer countdown;
        private boolean examRunning;
        private boolean submitted;

        ExamFrame(Profile profile) {
            super("Oasis Online Examination");
            this.profile = profile;
            Arrays.fill(answers, -1);
            setDefaultCloseOperation(DO_NOTHING_ON_CLOSE);
            setMinimumSize(new Dimension(690, 500));
            setSize(780, 560);
            setLocationRelativeTo(null);
            buildLogin();
            buildProfile();
            buildExam();
            root.add(loginPanel, "login");
            root.add(profilePanel, "profile");
            root.add(examPanel, "exam");
            root.add(resultPanel, "result");
            setContentPane(root);
            countdown = new javax.swing.Timer(1000, e -> tick());
            addWindowListener(new java.awt.event.WindowAdapter() {
                @Override public void windowClosing(java.awt.event.WindowEvent e) {
                    if (examRunning) {
                        int answer = JOptionPane.showConfirmDialog(ExamFrame.this,
                                "Are you sure you want to quit the exam?", "Leave exam?",
                                JOptionPane.YES_NO_OPTION, JOptionPane.WARNING_MESSAGE);
                        if (answer == JOptionPane.YES_OPTION) {
                            countdown.stop();
                            examRunning = false;
                            dispose();
                        }
                    } else dispose();
                }
            });
        }

        private void buildLogin() {
            GridBagConstraints g = constraints();
            JLabel title = new JLabel("Student sign in", SwingConstants.CENTER);
            title.setFont(title.getFont().deriveFont(Font.BOLD, 24f));
            g.gridx = 0; g.gridy = 0; g.gridwidth = 2; loginPanel.add(title, g);
            g.gridwidth = 1; g.gridy++;
            loginPanel.add(new JLabel("Username"), g);
            g.gridx = 1; loginPanel.add(new JLabel(profile.username), g);
            g.gridx = 0; g.gridy++; loginPanel.add(new JLabel("Password"), g);
            g.gridx = 1; loginPanel.add(loginPassword, g);
            JButton login = new JButton("Sign in");
            g.gridx = 0; g.gridy++; g.gridwidth = 2; loginPanel.add(login, g);
            login.addActionListener(e -> {
                char[] candidate = loginPassword.getPassword();
                boolean valid = profile.username.equals("student") && profile.authenticate(candidate);
                Arrays.fill(candidate, '\0');
                loginPassword.setText("");
                if (!valid) {
                    JOptionPane.showMessageDialog(this, "Access denied. Check your credentials.");
                    return;
                }
                show("profile");
            });
            loginPanel.setBorder(BorderFactory.createEmptyBorder(60, 100, 60, 100));
            getRootPane().setDefaultButton(login);
        }

        private void buildProfile() {
            GridBagConstraints g = constraints();
            JLabel title = new JLabel("Update your profile before starting", SwingConstants.CENTER);
            title.setFont(title.getFont().deriveFont(Font.BOLD, 20f));
            g.gridx = 0; g.gridy = 0; g.gridwidth = 2; profilePanel.add(title, g);
            g.gridwidth = 1; g.gridy++;
            profilePanel.add(new JLabel("Display name"), g);
            displayName.setText(profile.displayName);
            g.gridx = 1; profilePanel.add(displayName, g);
            g.gridx = 0; g.gridy++; profilePanel.add(new JLabel("Current password"), g);
            g.gridx = 1; profilePanel.add(currentPassword, g);
            g.gridx = 0; g.gridy++; profilePanel.add(new JLabel("New password (optional)"), g);
            g.gridx = 1; profilePanel.add(newPassword, g);
            JButton update = new JButton("Save profile");
            JButton start = new JButton("Start examination");
            g.gridx = 0; g.gridy++; profilePanel.add(update, g);
            g.gridx = 1; profilePanel.add(start, g);
            update.addActionListener(e -> updateProfile());
            start.addActionListener(e -> {
                if (displayName.getText().trim().isEmpty()) {
                    JOptionPane.showMessageDialog(this, "Display name is required.");
                    return;
                }
                profile.displayName = displayName.getText().trim();
                startExam();
            });
            profilePanel.setBorder(BorderFactory.createEmptyBorder(40, 100, 40, 100));
        }

        private void updateProfile() {
            char[] current = currentPassword.getPassword();
            char[] replacement = newPassword.getPassword();
            try {
                if (!profile.authenticate(current)) {
                    JOptionPane.showMessageDialog(this, "Current password is incorrect.");
                    return;
                }
                String name = displayName.getText().trim();
                if (name.isEmpty()) throw new IllegalArgumentException("Display name cannot be empty.");
                if (replacement.length > 0 && replacement.length < 10)
                    throw new IllegalArgumentException("New password must contain at least 10 characters.");
                if (replacement.length > 0) profile.update(name, replacement);
                else profile.displayName = name;
                currentPassword.setText("");
                newPassword.setText("");
                JOptionPane.showMessageDialog(this, "Profile updated.");
            } catch (IllegalArgumentException ex) {
                JOptionPane.showMessageDialog(this, ex.getMessage());
            } finally {
                Arrays.fill(current, '\0');
                Arrays.fill(replacement, '\0');
            }
        }

        private void buildExam() {
            JPanel top = new JPanel(new BorderLayout());
            top.add(new JLabel("Welcome, " + profile.displayName), BorderLayout.WEST);
            timerLabel.setFont(timerLabel.getFont().deriveFont(Font.BOLD, 18f));
            timerLabel.setForeground(new Color(150, 35, 35));
            top.add(timerLabel, BorderLayout.EAST);
            examPanel.setBorder(BorderFactory.createEmptyBorder(22, 28, 22, 28));
            examPanel.add(top, BorderLayout.NORTH);
            JPanel center = new JPanel(new BorderLayout(10, 10));
            counterLabel.setFont(counterLabel.getFont().deriveFont(Font.BOLD, 14f));
            center.add(counterLabel, BorderLayout.NORTH);
            questionLabel.setVerticalAlignment(SwingConstants.TOP);
            questionLabel.setFont(questionLabel.getFont().deriveFont(Font.BOLD, 18f));
            center.add(questionLabel, BorderLayout.CENTER);
            JPanel optionPanel = new JPanel(new GridLayout(0, 1, 6, 8));
            for (int i = 0; i < choices.length; i++) {
                choices[i] = new JRadioButton();
                choiceGroup.add(choices[i]);
                optionPanel.add(choices[i]);
            }
            center.add(optionPanel, BorderLayout.SOUTH);
            examPanel.add(center, BorderLayout.CENTER);
            JPanel buttons = new JPanel(new FlowLayout(FlowLayout.CENTER, 12, 4));
            JButton previous = new JButton("Previous");
            JButton next = new JButton("Next");
            JButton submit = new JButton("Submit exam");
            buttons.add(previous); buttons.add(next); buttons.add(submit);
            examPanel.add(buttons, BorderLayout.SOUTH);
            previous.addActionListener(e -> { saveAnswer(); if (index > 0) { index--; renderQuestion(); } });
            next.addActionListener(e -> { saveAnswer(); if (index < questions.size() - 1) { index++; renderQuestion(); } });
            submit.addActionListener(e -> {
                int confirm = JOptionPane.showConfirmDialog(this, "Submit your answers now?",
                        "Confirm submission", JOptionPane.YES_NO_OPTION);
                if (confirm == JOptionPane.YES_OPTION) submitExam(false);
            });
        }

        private void startExam() {
            index = 0;
            Arrays.fill(answers, -1);
            secondsRemaining = EXAM_SECONDS;
            submitted = false;
            examRunning = true;
            startedAt = System.nanoTime();
            renderQuestion();
            updateTimer();
            show("exam");
            countdown.start();
        }

        private void renderQuestion() {
            Question q = questions.get(index);
            counterLabel.setText("Question " + (index + 1) + " of " + questions.size());
            questionLabel.setText("<html><div style='width:600px'>" + escapeHtml(q.text()) + "</div></html>");
            choiceGroup.clearSelection();
            for (int i = 0; i < choices.length; i++) {
                choices[i].setText(q.choices()[i]);
                if (answers[index] == i) choices[i].setSelected(true);
            }
        }

        private void saveAnswer() {
            for (int i = 0; i < choices.length; i++) if (choices[i].isSelected()) answers[index] = i;
        }

        private void tick() {
            secondsRemaining--;
            updateTimer();
            if (secondsRemaining <= 0) submitExam(true);
        }

        private void updateTimer() {
            timerLabel.setText("Time left: %02d:%02d".formatted(Math.max(0, secondsRemaining) / 60,
                    Math.max(0, secondsRemaining) % 60));
        }

        private void submitExam(boolean automatic) {
            if (submitted) return;
            saveAnswer();
            submitted = true;
            examRunning = false;
            countdown.stop();
            long elapsed = Math.max(0, Duration.ofNanos(System.nanoTime() - startedAt).toMinutes());
            int score = 0;
            StringBuilder details = new StringBuilder("<html><body style='width:650px'><h2>Answer review</h2>");
            for (int i = 0; i < questions.size(); i++) {
                Question q = questions.get(i);
                boolean correct = answers[i] == q.answer();
                if (correct) score++;
                details.append("<p><b>").append(i + 1).append(". ").append(escapeHtml(q.text())).append("</b><br>")
                        .append("Your answer: ").append(answers[i] < 0 ? "Not answered" : escapeHtml(q.choices()[answers[i]]))
                        .append(" — ").append(correct ? "Correct" : "Incorrect")
                        .append("<br>Correct answer: ").append(escapeHtml(q.choices()[q.answer()]))
                        .append("<br>").append(escapeHtml(q.explanation())).append("</p>");
            }
            details.append("</body></html>");
            resultPanel.removeAll();
            JLabel heading = new JLabel("<html><h1>" + (automatic ? "Time is up — submitted" : "Exam submitted")
                    + "</h1><h2>" + score + " out of " + questions.size() + " correct</h2><p>Time taken: "
                    + elapsed + " minutes</p></html>");
            heading.setBorder(BorderFactory.createEmptyBorder(10, 18, 8, 18));
            resultPanel.add(heading, BorderLayout.NORTH);
            resultPanel.add(new JScrollPane(new JLabel(details.toString())), BorderLayout.CENTER);
            JButton logout = new JButton("Log out");
            JPanel bottom = new JPanel(); bottom.add(logout);
            resultPanel.add(bottom, BorderLayout.SOUTH);
            logout.addActionListener(e -> {
                loginPassword.setText("");
                show("login");
            });
            resultPanel.revalidate();
            resultPanel.repaint();
            show("result");
        }

        private void show(String card) { ((CardLayout) root.getLayout()).show(root, card); }

        private static String escapeHtml(String text) {
            return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;");
        }

        private static GridBagConstraints constraints() {
            GridBagConstraints g = new GridBagConstraints();
            g.insets = new Insets(10, 9, 10, 9);
            g.anchor = GridBagConstraints.WEST;
            return g;
        }
    }

    private static byte[] randomSalt() {
        byte[] salt = new byte[16];
        new SecureRandom().nextBytes(salt);
        return salt;
    }

    private static byte[] hash(char[] password, byte[] salt) {
        PBEKeySpec spec = new PBEKeySpec(password, salt, 160_000, 256);
        try {
            return SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256").generateSecret(spec).getEncoded();
        } catch (GeneralSecurityException ex) {
            throw new IllegalStateException("Password hashing is unavailable.", ex);
        } finally {
            spec.clearPassword();
        }
    }

    private static java.util.List<Question> questions() {
        return java.util.List.of(
                new Question("Which Java type represents a whole number?", new String[]{"String", "int", "boolean", "double"}, 1, "The primitive int type represents a signed whole number."),
                new Question("Which keyword creates a subclass?", new String[]{"implements", "extends", "inherits", "super"}, 1, "A class declares its superclass with extends."),
                new Question("Which collection preserves insertion order and permits duplicates?", new String[]{"HashSet", "TreeSet", "ArrayList", "Map"}, 2, "ArrayList preserves element order and allows repeated values."),
                new Question("What does JVM stand for?", new String[]{"Java Variable Method", "Java Virtual Machine", "Joint Version Manager", "Java Visual Model"}, 1, "The JVM executes Java bytecode."),
                new Question("Which keyword prevents a method from being overridden?", new String[]{"static", "final", "private", "native"}, 1, "A final method cannot be overridden by a subclass."),
                new Question("Which block runs whether or not an exception is thrown?", new String[]{"catch", "throws", "finally", "assert"}, 2, "A finally block is used for cleanup after try/catch."),
                new Question("Which interface is commonly used for a single-abstract-method lambda?", new String[]{"Serializable", "Runnable", "Cloneable", "Comparable"}, 1, "Runnable has one abstract run method."),
                new Question("What is the default value of an instance boolean field?", new String[]{"true", "false", "null", "0"}, 1, "Instance boolean fields default to false."),
                new Question("Which keyword refers to the current object?", new String[]{"this", "super", "self", "current"}, 0, "this refers to the current object instance."),
                new Question("Which API should be used to safely bind values in JDBC SQL?", new String[]{"StringBuilder", "PreparedStatement", "Scanner", "ResultSetMetaData"}, 1, "PreparedStatement binds values separately from SQL text.")
        );
    }
}

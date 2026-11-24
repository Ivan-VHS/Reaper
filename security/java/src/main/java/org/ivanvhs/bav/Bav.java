package org.ivanvhs.bav;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.attribute.BasicFileAttributes;
import java.text.Normalizer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * BAV Java Guard: deterministic, read-only source and repository inspection.
 *
 * It never loads classes from the inspected project, executes project code,
 * follows symbolic links, or emits matched credential values.
 */
public final class Bav {
    private static final String VERSION = "1.0.0";
    private static final int MAX_FILES = 5_000;
    private static final long MAX_FILE_BYTES = 2L * 1024L * 1024L;
    private static final long MAX_TOTAL_BYTES = 50L * 1024L * 1024L;

    private static final Set<String> EXCLUDED_DIRECTORIES = Set.of(
            ".git", ".venv", "venv", "__pycache__", "build", "dist",
            "node_modules", ".pytest_cache", ".mypy_cache", "coverage",
            ".idea", ".gradle", "target"
    );
    private static final Set<String> TEXT_SUFFIXES = Set.of(
            ".py", ".pyi", ".c", ".h", ".cc", ".cpp", ".cxx", ".hpp", ".hxx",
            ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".java", ".kt",
            ".rs", ".go", ".cs", ".swift", ".sh", ".ps1", ".bat", ".cmd",
            ".yml", ".yaml", ".json", ".jsonc", ".toml", ".ini", ".cfg",
            ".conf", ".xml", ".html", ".css", ".scss", ".md", ".mdx",
            ".rst", ".txt", ".properties", ".cmake", ".gradle", ".sql",
            ".graphql", ".proto", ".lua", ".make"
    );
    private static final Set<String> TEXT_NAMES = Set.of(
            ".env", ".env.example", ".gitignore", ".gitattributes",
            ".editorconfig", "Dockerfile", "Makefile", "CMakeLists.txt",
            "requirements.txt", "CODEOWNERS", "LICENSE", "SECURITY.md"
    );
    private static final Pattern CREDENTIAL_PREFIX = Pattern.compile(
            "(?i)(?:AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,}|"
                    + "xox[baprs]-[A-Za-z0-9-]{16,}|"
                    + "-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)"
    );
    private static final Pattern SECRET_ASSIGNMENT = Pattern.compile(
            "(?i)\\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password|secret)"
                    + "\\s*[:=]\\s*[\\\"'][^\\\"']{12,}[\\\"']"
    );
    private static final Pattern CONFLICT_MARKER = Pattern.compile(
            "^\\s*(?:<{7}|>{7})(?:\\s|$)|^\\s*={7}\\s*$"
    );
    private static final Pattern JAVA_PROCESS_EXEC = Pattern.compile(
            "(?:Runtime\\s*\\.\\s*getRuntime\\s*\\(\\s*\\)\\s*\\.\\s*exec\\s*\\(|"
                    + "new\\s+ProcessBuilder\\s*\\()"
    );
    private static final Pattern JAVA_DESERIALIZATION = Pattern.compile(
            "(?:ObjectInputStream\\s*\\(|\\breadObject\\s*\\()"
    );
    private static final Pattern JAVA_XML_FACTORY = Pattern.compile(
            "(?:DocumentBuilderFactory|SAXParserFactory|XMLInputFactory|TransformerFactory)"
    );
    private static final Pattern JAVA_TRUST_OVERRIDE = Pattern.compile(
            "(?:ALLOW_ALL_HOSTNAME_VERIFIER|HostnameVerifier|X509TrustManager|"
                    + "checkServerTrusted\\s*\\([^)]*\\)\\s*\\{\\s*\\})"
    );
    private static final Pattern JAVA_WEAK_CRYPTO = Pattern.compile(
            "(?i)(?:MessageDigest\\s*\\.\\s*getInstance\\s*\\(\\s*[\\\"'](?:MD5|SHA-?1)[\\\"']|"
                    + "Cipher\\s*\\.\\s*getInstance\\s*\\(\\s*[\\\"'](?:DES(?:/[^\\\"']*)?|AES/ECB[^\\\"']*)[\\\"'])"
    );
    private static final Pattern JAVA_SQL_CONCAT = Pattern.compile(
            "(?s)(?:prepareStatement|executeQuery|executeUpdate)\\s*\\(\\s*[^;]{0,240}\\+"
    );
    private static final Pattern JAVA_ARCHIVE_PATH = Pattern.compile(
            "(?:resolve|normalize)\\s*\\(\\s*[^)]*(?:entry|zipEntry|getName)\\s*\\("
    );
    private static final Set<Integer> HIDDEN_CODEPOINTS = Set.of(
            0x061C, 0x200B, 0x200C, 0x200D, 0x200E, 0x200F,
            0x202A, 0x202B, 0x202C, 0x202D, 0x202E,
            0x2066, 0x2067, 0x2068, 0x2069
    );

    private Bav() {}

    public record Finding(
            String ruleId,
            String severity,
            String enforcement,
            String path,
            Integer line,
            String message,
            String remediation
    ) {
        Map<String, Object> toMap() {
            Map<String, Object> value = new LinkedHashMap<>();
            value.put("rule_id", ruleId);
            value.put("severity", severity);
            value.put("enforcement", enforcement);
            value.put("path", path);
            value.put("line", line);
            value.put("message", message);
            value.put("remediation", remediation);
            return value;
        }
    }

    private record Rule(String id, String severity, String enforcement, String remediation) {}

    private static final Map<String, Rule> RULES = Map.ofEntries(
            Map.entry("BAV-J-001", new Rule("BAV-J-001", "critical", "block",
                    "Remove the credential, revoke or rotate it, and move secrets to a dedicated secret store.")),
            Map.entry("BAV-J-002", new Rule("BAV-J-002", "high", "review",
                    "Replace shell-like process construction with a narrowly scoped API and fixed argument vectors.")),
            Map.entry("BAV-J-003", new Rule("BAV-J-003", "high", "review",
                    "Avoid native Java object deserialization for untrusted data; use a bounded, schema-driven format.")),
            Map.entry("BAV-J-004", new Rule("BAV-J-004", "high", "review",
                    "Disable external entities and external DTD/schema access, enable secure processing, and fail closed.")),
            Map.entry("BAV-J-005", new Rule("BAV-J-005", "high", "review",
                    "Use normal certificate-chain and hostname verification; never accept every peer.")),
            Map.entry("BAV-J-006", new Rule("BAV-J-006", "high", "review",
                    "Use modern, explicitly configured cryptographic algorithms and authenticated modes.")),
            Map.entry("BAV-J-007", new Rule("BAV-J-007", "high", "review",
                    "Use PreparedStatement parameters; do not concatenate untrusted values into SQL.")),
            Map.entry("BAV-J-008", new Rule("BAV-J-008", "high", "review",
                    "Normalize archive entry paths and verify they remain inside the extraction root."))
    );

    public static Map<String, Object> scan(Path requestedRoot) throws IOException {
        Path root = requestedRoot.toRealPath();
        if (!Files.isDirectory(root)) {
            throw new IOException("scan root is not a directory");
        }

        List<Path> paths = new ArrayList<>();
        List<Finding> findings = new ArrayList<>();
        Map<String, String> normalizedPaths = new HashMap<>();
        long totalBytes = 0L;
        long scannedBytes = 0L;
        int textFiles = 0;

        Files.walkFileTree(root, new SimpleFileVisitor<>() {
            @Override
            public FileVisitResult preVisitDirectory(Path dir, BasicFileAttributes attrs) {
                if (!dir.equals(root) && EXCLUDED_DIRECTORIES.contains(dir.getFileName().toString())) {
                    return FileVisitResult.SKIP_SUBTREE;
                }
                return FileVisitResult.CONTINUE;
            }

            @Override
            public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) {
                paths.add(file);
                return FileVisitResult.CONTINUE;
            }
        });
        paths.sort(Comparator.comparing(path -> root.relativize(path).toString().replace('\\', '/')));

        if (paths.size() > MAX_FILES) {
            throw new IOException("workspace exceeds the BAV Java file-count limit");
        }

        for (Path file : paths) {
            String relative = root.relativize(file).toString().replace('\\', '/');
            if (Files.isSymbolicLink(file)) {
                add(findings, "BAV-J-008", relative, null, "symbolic link requires explicit trust-boundary review");
                continue;
            }
            if (!Files.isRegularFile(file)) {
                continue;
            }

            String canonical = Normalizer.normalize(relative, Normalizer.Form.NFC).toLowerCase(Locale.ROOT);
            String previous = normalizedPaths.putIfAbsent(canonical, relative);
            if (previous != null && !previous.equals(relative)) {
                add(findings, "BAV-J-008", relative, null,
                        "path collides with " + previous + " after case-insensitive Unicode normalization");
            }
            if (containsReservedWindowsName(relative)) {
                add(findings, "BAV-J-008", relative, null, "reserved Windows device name in path");
            }

            long size = Files.size(file);
            totalBytes += size;
            if (totalBytes > MAX_TOTAL_BYTES) {
                throw new IOException("workspace exceeds the BAV Java total-byte limit");
            }
            if (size > MAX_FILE_BYTES || !isTextFile(file)) {
                continue;
            }

            byte[] raw = Files.readAllBytes(file);
            scannedBytes += raw.length;
            String source;
            try {
                source = StandardCharsets.UTF_8.newDecoder()
                        .onMalformedInput(CodingErrorAction.REPORT)
                        .onUnmappableCharacter(CodingErrorAction.REPORT)
                        .decode(ByteBuffer.wrap(raw)).toString();
            } catch (CharacterCodingException exception) {
                add(findings, "BAV-J-008", relative, null, "text source is not valid UTF-8");
                continue;
            }
            textFiles++;
            inspectText(source, relative, findings);
            if (relative.toLowerCase(Locale.ROOT).endsWith(".java")) {
                inspectJava(source, relative, findings);
            }
        }

        findings.sort(Comparator.comparing(Finding::path)
                .thenComparing(f -> f.line() == null ? 0 : f.line())
                .thenComparing(Finding::ruleId)
                .thenComparing(Finding::message));

        int risk = 0;
        boolean blocked = false;
        for (Finding finding : findings) {
            risk += switch (finding.severity()) {
                case "critical" -> 25;
                case "high" -> 12;
                case "medium" -> 5;
                default -> 1;
            };
            blocked |= finding.enforcement().equals("block");
        }
        risk = Math.min(100, risk);
        String verdict = blocked ? "blocked" : (findings.isEmpty() ? "clear" : "review");

        Map<String, Object> report = new LinkedHashMap<>();
        report.put("schema", "bav.java.scan.v1");
        report.put("scanner", Map.of("name", "BAV Java Guard", "version", VERSION));
        report.put("verdict", verdict);
        report.put("risk_score", risk);
        report.put("findings_count", findings.size());
        report.put("findings", findings.stream().map(Finding::toMap).toList());
        report.put("policy", Map.of("rule_prefix", "BAV-J-", "rules_total", RULES.size(),
                "read_only", true, "project_code_execution", false));
        report.put("scan", Map.of("tracked_paths", paths.size(), "text_files_scanned", textFiles,
                "bytes_scanned", scannedBytes, "total_workspace_bytes", totalBytes));
        return report;
    }

    private static void inspectText(String source, String path, List<Finding> findings) {
        if (source.indexOf('\0') >= 0) {
            add(findings, "BAV-J-008", path, null, "NUL byte detected in text source");
            return;
        }

        int crlf = 0;
        int loneLf = 0;
        int loneCr = 0;
        for (int i = 0; i < source.length(); i++) {
            char current = source.charAt(i);
            if (current == '\r') {
                if (i + 1 < source.length() && source.charAt(i + 1) == '\n') {
                    crlf++;
                    i++;
                } else {
                    loneCr++;
                }
            } else if (current == '\n') {
                loneLf++;
            }
        }
        if ((crlf > 0 && loneLf > 0) || (crlf > 0 && loneCr > 0) || (loneLf > 0 && loneCr > 0)) {
            add(findings, "BAV-J-008", path, null, "mixed CRLF/LF/CR line endings");
        }

        String[] lines = source.split("\\R", -1);
        for (int index = 0; index < lines.length; index++) {
            String line = lines[index];
            int lineNumber = index + 1;
            if (CONFLICT_MARKER.matcher(line).find()) {
                add(findings, "BAV-J-008", path, lineNumber, "unresolved merge-conflict marker");
            }
            Matcher credential = CREDENTIAL_PREFIX.matcher(line);
            Matcher assignment = SECRET_ASSIGNMENT.matcher(line);
            if (credential.find() || assignment.find()) {
                add(findings, "BAV-J-001", path, lineNumber, "credential-like value or private-key marker detected; value redacted");
            }
        }

        for (int offset = 0; offset < source.length();) {
            int point = source.codePointAt(offset);
            if (HIDDEN_CODEPOINTS.contains(point) || (point == 0xFEFF && offset > 0)) {
                int line = 1;
                for (int i = 0; i < offset; i++) {
                    if (source.charAt(i) == '\n') {
                        line++;
                    }
                }
                add(findings, "BAV-J-008", path, line,
                        String.format(Locale.ROOT, "hidden direction/zero-width character U+%04X", point));
                break;
            }
            offset += Character.charCount(point);
        }
    }

    private static void inspectJava(String source, String path, List<Finding> findings) {
        if (JAVA_PROCESS_EXEC.matcher(source).find()) {
            add(findings, "BAV-J-002", path, firstLine(source, JAVA_PROCESS_EXEC), "process execution API requires security review");
        }
        if (JAVA_DESERIALIZATION.matcher(source).find()) {
            add(findings, "BAV-J-003", path, firstLine(source, JAVA_DESERIALIZATION),
                    "Java object deserialization API requires an explicit untrusted-input review");
        }
        if (JAVA_XML_FACTORY.matcher(source).find()) {
            String lower = source.toLowerCase(Locale.ROOT);
            boolean hardened = lower.contains("feature_secure_processing")
                    && lower.contains("access_external_dtd")
                    && lower.contains("access_external_schema");
            if (!hardened) {
                add(findings, "BAV-J-004", path, firstLine(source, JAVA_XML_FACTORY),
                        "XML parser factory appears without all expected external-access hardening markers");
            }
        }
        if (JAVA_TRUST_OVERRIDE.matcher(source).find()) {
            String compact = source.replaceAll("\\s+", " ");
            boolean suspicious = compact.matches("(?s).*HostnameVerifier.*return true.*")
                    || compact.matches("(?s).*checkServerTrusted\\s*\\([^)]*\\)\\s*\\{\\s*\\}.*")
                    || compact.contains("ALLOW_ALL_HOSTNAME_VERIFIER");
            if (suspicious) {
                add(findings, "BAV-J-005", path, firstLine(source, JAVA_TRUST_OVERRIDE),
                        "trust-all or empty TLS verification implementation detected");
            }
        }
        if (JAVA_WEAK_CRYPTO.matcher(source).find()) {
            add(findings, "BAV-J-006", path, firstLine(source, JAVA_WEAK_CRYPTO),
                    "weak or unauthenticated cryptographic algorithm selection detected");
        }
        if (JAVA_SQL_CONCAT.matcher(source).find()) {
            add(findings, "BAV-J-007", path, firstLine(source, JAVA_SQL_CONCAT),
                    "SQL statement appears to be assembled through string concatenation");
        }
        if (JAVA_ARCHIVE_PATH.matcher(source).find()
                && !source.contains("startsWith") && !source.contains("startsWith(")) {
            add(findings, "BAV-J-008", path, firstLine(source, JAVA_ARCHIVE_PATH),
                    "archive entry path resolution lacks a visible extraction-root containment check");
        }
    }

    private static Integer firstLine(String source, Pattern pattern) {
        Matcher matcher = pattern.matcher(source);
        if (!matcher.find()) {
            return null;
        }
        int line = 1;
        for (int i = 0; i < matcher.start(); i++) {
            if (source.charAt(i) == '\n') {
                line++;
            }
        }
        return line;
    }

    private static boolean isTextFile(Path path) {
        String name = path.getFileName().toString();
        String lower = name.toLowerCase(Locale.ROOT);
        int dot = lower.lastIndexOf('.');
        return TEXT_NAMES.contains(name) || (dot >= 0 && TEXT_SUFFIXES.contains(lower.substring(dot)));
    }

    private static boolean containsReservedWindowsName(String path) {
        Set<String> reserved = new HashSet<>(Arrays.asList("CON", "PRN", "AUX", "NUL"));
        for (int i = 1; i <= 9; i++) {
            reserved.add("COM" + i);
            reserved.add("LPT" + i);
        }
        for (String component : path.split("/")) {
            String base = component.split("\\.", 2)[0].toUpperCase(Locale.ROOT);
            if (reserved.contains(base)) {
                return true;
            }
        }
        return false;
    }

    private static void add(List<Finding> findings, String ruleId, String path, Integer line, String message) {
        Rule rule = RULES.get(ruleId);
        findings.add(new Finding(rule.id(), rule.severity(), rule.enforcement(),
                path, line, message, rule.remediation()));
    }

    private static String jsonEscape(String value) {
        StringBuilder out = new StringBuilder(value.length() + 16);
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            switch (c) {
                case '"' -> out.append("\\\"");
                case '\\' -> out.append("\\\\");
                case '\b' -> out.append("\\b");
                case '\f' -> out.append("\\f");
                case '\n' -> out.append("\\n");
                case '\r' -> out.append("\\r");
                case '\t' -> out.append("\\t");
                default -> {
                    if (c < 0x20) {
                        out.append(String.format(Locale.ROOT, "\\u%04x", (int) c));
                    } else {
                        out.append(c);
                    }
                }
            }
        }
        return out.toString();
    }

    @SuppressWarnings("unchecked")
    private static String toJson(Object value) {
        if (value == null) return "null";
        if (value instanceof String text) return "\"" + jsonEscape(text) + "\"";
        if (value instanceof Number || value instanceof Boolean) return value.toString();
        if (value instanceof Map<?, ?> map) {
            List<String> fields = new ArrayList<>();
            for (Map.Entry<?, ?> entry : map.entrySet()) {
                fields.add(toJson(String.valueOf(entry.getKey())) + ":" + toJson(entry.getValue()));
            }
            return "{" + String.join(",", fields) + "}";
        }
        if (value instanceof Iterable<?> iterable) {
            List<String> items = new ArrayList<>();
            for (Object item : iterable) items.add(toJson(item));
            return "[" + String.join(",", items) + "]";
        }
        return toJson(value.toString());
    }

    private static int run(String[] args) throws IOException {
        if (args.length == 0 || !args[0].equals("scan")) {
            throw new IllegalArgumentException("usage: Bav scan --root PATH");
        }
        Path root = Path.of(".").toAbsolutePath();
        for (int i = 1; i < args.length; i++) {
            if ("--root".equals(args[i]) && i + 1 < args.length) {
                root = Path.of(args[++i]);
            } else if ("--json".equals(args[i])) {
                // JSON is the only machine interface; retained for explicit callers.
            } else {
                throw new IllegalArgumentException("unknown or incomplete BAV argument: " + args[i]);
            }
        }
        Map<String, Object> report = scan(root);
        System.out.println(toJson(report));
        return "blocked".equals(report.get("verdict")) ? 2 : 0;
    }

    public static void main(String[] args) {
        try {
            int status = run(args);
            if (status != 0) {
                System.exit(status);
            }
        } catch (Exception exception) {
            System.err.println("BAV Java Guard failed: " + exception.getMessage());
            System.exit(2);
        }
    }
}

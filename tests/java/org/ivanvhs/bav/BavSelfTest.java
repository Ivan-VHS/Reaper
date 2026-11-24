package org.ivanvhs.bav;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

public final class BavSelfTest {
    private BavSelfTest() {}

    public static void main(String[] args) throws Exception {
        Path root = Files.createTempDirectory("bav-java-self-test-");
        try {
            Path source = root.resolve("src/main/java/Probe.java");
            Files.createDirectories(source.getParent());
            String probe = """
                    import java.io.ObjectInputStream;
                    import java.security.MessageDigest;
                    final class Probe {
                        Object unsafe(ObjectInputStream in) throws Exception { return in.readObject(); }
                        byte[] weak(byte[] input) throws Exception { return MessageDigest.getInstance("MD5").digest(input); }
                    }
                    """;
            Files.writeString(source, probe, StandardCharsets.UTF_8);
            byte[] before = Files.readAllBytes(source);

            Map<String, Object> report = Bav.scan(root);
            if (!"review".equals(report.get("verdict"))) {
                throw new AssertionError("expected review verdict for deliberately unsafe fixture");
            }
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> findings = (List<Map<String, Object>>) report.get("findings");
            boolean deserialization = findings.stream().anyMatch(item -> "BAV-J-003".equals(item.get("rule_id")));
            boolean crypto = findings.stream().anyMatch(item -> "BAV-J-006".equals(item.get("rule_id")));
            if (!deserialization || !crypto) {
                throw new AssertionError("Java-specific rules were not detected");
            }
            if (!java.util.Arrays.equals(before, Files.readAllBytes(source))) {
                throw new AssertionError("scanner modified an inspected source file");
            }

            Path credential = root.resolve("secrets.txt");
            String secret = "ghp_" + "A".repeat(30);
            Files.writeString(credential, "token = \"" + secret + "\"\n", StandardCharsets.UTF_8);
            Map<String, Object> secretReport = Bav.scan(root);
            String serialized = Bav.toJson(secretReport);
            if (serialized.contains(secret)) {
                throw new AssertionError("secret value leaked into report");
            }
            if (!"blocked".equals(secretReport.get("verdict"))) {
                throw new AssertionError("credential exposure must block");
            }
            System.out.println("BAV Java Guard self-test: PASS");
        } finally {
            try (var walk = Files.walk(root)) {
                walk.sorted(java.util.Comparator.reverseOrder()).forEach(path -> {
                    try {
                        Files.deleteIfExists(path);
                    } catch (Exception error) {
                        throw new RuntimeException(error);
                    }
                });
            }
        }
    }
}

# Human-first governance and consent controls

Status: implemented runtime library and host-injected language built-ins. This is a local application security feature; it is not a medical product, legal compliance certification, or substitute for a controller's legal basis.

## Implemented behavior

- A host application issues reaper.consent.v1 grants using a secret of at least 256 bits. The key never enters the language environment.
- Every grant is bound to one subject, one purpose, an explicit non-empty scope set, an issuance time, and a finite expiry (1 second to 365 days).
- HMAC-SHA-256 verification uses constant-time comparison. A modified, expired, not-yet-valid, wrongly scoped, or incorrectly signed grant fails closed.
- A host can revoke a signed grant. When an AuditLog is supplied, issuance and revocation events are added to the existing hash-chained journal; revocations are restored only after that journal verifies.
- Reaper programs may call consent_check(token, subject, purpose, scope) and consent_revoke(token). Both reject use unless the embedding host injects a ConsentAuthority. Scripts cannot issue grants or read the signing key.

## Embedding example

    from reaper.audit import AuditLog
    from reaper.governance import ConsentAuthority
    from reaper.runtime import Interpreter

    authority = ConsentAuthority(
        secret=load_secret_from_os_key_store(),
        audit_log=AuditLog("audit/governance.jsonl"),
    )
    grant = authority.issue(
        subject="local-user",
        purpose="report-export",
        scopes=["summary-json"],
        ttl_seconds=900,
    )
    interpreter = Interpreter(consent_authority=authority)

The host must keep the key in an operating-system key store or another managed secret provider. Do not hard-code it, commit it, or place it in source files. The caller remains responsible for authenticating the subject and deciding whether the requested purpose is lawful.

## Scope crosswalk

| Medical-rights concept | Reaper implementation / boundary |
|---|---|
| Informed consent and revocation | Signed, purpose/scope-bound grant; finite TTL; immediate revocation |
| Confidentiality and data minimization | Tokens authorize only named scopes; the runtime does not infer blanket permission |
| Access audit | Existing hash-chained execution journal; consent events can be included |
| Patient access / correction / erasure | Not a patient-record system; no PHI store or erasure promise |
| Clinical quality, CDS, medication and research governance | Not applicable to a general-purpose programming language |
| SaMD / clinical AI | Reaper is not represented as a medical device or clinical decision system |
| Human oversight and safety | Native FFI remains opt-in; host policy remains authoritative |

## Security limits

The hash chain is tamper-evident, not WORM storage or a digital signature. HMAC security depends on secret-key protection and correct host identity proofing. The optional audit log is local and single-writer. Revocation persistence requires the same verified journal to be supplied on restart. This module does not implement MFA, HSM integration, jurisdictional transfer controls, regulatory notification, or legal review.

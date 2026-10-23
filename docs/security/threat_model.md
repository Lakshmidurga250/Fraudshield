# Threat Model & Security Posture

## Assets Protected
1. User Credentials and Passwords.
2. User Transaction Assessment Records and Risk Scores.
3. Machine Learning Model Artifacts and Integrity Hashes.
4. Operational Audit Trails.

## Threat Analysis & Mitigations

| Threat | Risk Level | Mitigation in FraudShield |
|---|---|---|
| **Credential Compromise** | High | Werkzeug PBKDF2/scrypt one-way password hashing. Passwords never logged in plaintext. Minimum 8 character validation. |
| **Cross-User Data Leakage (IDOR)** | Critical | Every assessment query filters strictly by `current_user.id`. Foreign key cascade ensures user deletion purges associated assessments. Verified by automated security tests. |
| **CSV Formula Injection** | Medium | Exported CSV cells starting with `=`, `+`, `-`, `@`, `\t`, or `\r` are prefixed with single quote `'` to disable command execution in spreadsheet readers. |
| **Cross-Site Request Forgery (CSRF)** | High | Flask-WTF CSRF tokens required on all mutating state actions (`POST /auth/logout`, `POST /predictions/new`, `POST /models/train`). |
| **Model Deserialization Poisoning** | Critical | Model artifacts (`.joblib`) are verified against registered SHA-256 digests. If checksum mismatch occurs, loading is rejected immediately with a `SecurityError`. |
| **Open Redirect Vulnerability** | Medium | Login `next` parameter validated via `is_safe_redirect_url` to prevent redirection to malicious external hosts. |
| **Denial of Service via Payload** | Medium | `MAX_CONTENT_LENGTH` enforced at 16MB. Input vectors checked for finiteness (`np.isinf`, `np.isnan`). |

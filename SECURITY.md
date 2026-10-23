# Security Policy — FraudShield

## Reporting Security Issues

We take the security of FraudShield and user privacy seriously. If you discover a vulnerability or security boundary issue, please do not open a public GitHub issue.

Please report security concerns responsibly by contacting the maintainer at `security@fraudshield.local` or via a private GitHub Security Advisory.

---

## Supported Versions

| Version | Supported |
|---|---|
| 1.0.x | :white_check_mark: |
| < 1.0 | :x: |

---

## Security Architecture & Defenses

1. **Password Storage**: Passwords are never stored in plaintext. Passwords are salted and hashed using Werkzeug PBKDF2/scrypt.
2. **Session Security**:
   - `SESSION_COOKIE_HTTPONLY = True`
   - `SESSION_COOKIE_SAMESITE = "Lax"`
   - `SESSION_COOKIE_SECURE` enabled in production environments.
3. **Cross-User Record Isolation**:
   - Every database query for assessments and CSV exports filters strictly by `current_user.id`.
   - Access attempts to records of another user return `404 Not Found` without disclosing existence.
4. **CSV Formula Injection Neutralization**:
   - Values starting with `=`, `+`, `-`, `@`, `\t`, or `\r` are prefixed with `'` during export to prevent code execution in spreadsheet software.
5. **Model Artifact Verification**:
   - Model files (`.joblib`) are validated using cryptographic SHA-256 digests prior to deserialization.
6. **Input Sanitization**:
   - Feature dictionaries are validated against explicit schema and finiteness checks (`np.isinf`, `np.isnan`).

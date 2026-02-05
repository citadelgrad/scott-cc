# security-suite

> Security-focused development and vulnerability scanning

## What's Included

### Agents (2)
- **security-advisor** - Search OWASP cheatsheets and provide tailored security guidance
- **security-engineer** - Identify vulnerabilities and ensure compliance with security standards

## When to Use

**Install this if you**:
- Build applications handling sensitive data
- Need OWASP compliance
- Want security reviews before deployment
- Handle authentication, authorization, or payments

**Don't install if you**:
- Build internal tools with no sensitive data
- Have dedicated security team doing reviews

## Common Use Cases

### 1. Security Architecture Review
```
User: "Review this authentication system for vulnerabilities"
security-advisor: Checks against OWASP best practices
security-engineer: Identifies specific vulnerabilities
```

### 2. OWASP Compliance
```
User: "Ensure this API is OWASP compliant"
security-advisor: References relevant OWASP cheatsheets
Output: Compliance checklist with fixes
```

### 3. Vulnerability Scanning
```
User: "Scan this codebase for SQL injection risks"
security-engineer: Analyzes code patterns
Output: Vulnerability report with severity ratings
```

## Quick Start

```bash
# Get security guidance
Ask: "How should I securely store API keys in my Node.js app?"

# Review code for vulnerabilities
Ask: "Review this authentication endpoint for security issues"

# OWASP compliance check
Ask: "Is this password reset flow OWASP compliant?"
```

## Security Checklist

Before deployment, use security-suite to verify:
- [ ] No hardcoded secrets or credentials
- [ ] Input validation on all user inputs
- [ ] SQL injection protection
- [ ] XSS prevention
- [ ] CSRF protection for state-changing operations
- [ ] Authentication and authorization properly implemented
- [ ] Sensitive data encrypted at rest and in transit

## Recommended Combinations

**Full security audit**:
- security-suite ✅
- scott-cc ✅ (main plugin for refactoring)
- mutation-testing ✅ (to verify security tests work)

---
description: Look up OWASP security cheatsheets by topic
model: haiku
---

# Security Cheatsheet Lookup

Look up an OWASP security cheatsheet for the user.

## Target Topic

$ARGUMENTS

## Cheatsheet Location

All cheatsheets are in: `/Users/scott/projects/CheatSheetSeries/cheatsheets/`

Files follow the pattern: `{Topic}_Cheat_Sheet.md`

## Instructions

### If topic provided
1. Search for matching cheatsheet file using Glob: `*{topic}*.md` (case-insensitive)
2. If multiple matches, list them and ask user to clarify
3. Read the matching file and provide the key sections

### If no topic provided
List available categories and ask what they need:

**Authentication & Access Control**
- Authentication, Authorization, Session_Management, Password_Storage
- Multifactor_Authentication, Forgot_Password, Credential_Stuffing_Prevention

**Injection Prevention**
- SQL_Injection_Prevention, Cross_Site_Scripting_Prevention
- OS_Command_Injection_Defense, LDAP_Injection_Prevention

**Web Security**
- Cross-Site_Request_Forgery_Prevention, Clickjacking_Defense
- Content_Security_Policy, HTTP_Headers

**API Security**
- REST_Security, GraphQL, Web_Service_Security, JSON_Web_Token

**Infrastructure**
- Kubernetes_Security, Docker_Security, CI_CD_Security
- Infrastructure_as_Code_Security, Secrets_Management

**Data Protection**
- Cryptographic_Storage, Key_Management, Transport_Layer_Security

**AI/LLM Security**
- LLM_Prompt_Injection_Prevention, AI_Agent_Security, Secure_AI_Model_Ops

## When Returning Cheatsheet Content

1. **Start with Introduction** - What this cheatsheet addresses
2. **Key Recommendations** - The 3-5 most critical actions (prioritized)
3. **Code Examples** - Include relevant examples for user's likely tech stack
4. **Common Mistakes** - What to avoid
5. **Related Cheatsheets** - Mention related topics they should review

## Example Mappings

| User Query | Cheatsheet File |
|------------|-----------------|
| auth, authentication, login | Authentication_Cheat_Sheet.md |
| xss, cross site scripting | Cross_Site_Scripting_Prevention_Cheat_Sheet.md |
| sql injection | SQL_Injection_Prevention_Cheat_Sheet.md |
| csrf | Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.md |
| jwt, token | JSON_Web_Token_for_Java_Cheat_Sheet.md |
| k8s, kubernetes | Kubernetes_Security_Cheat_Sheet.md |
| docker, container | Docker_Security_Cheat_Sheet.md |
| password | Password_Storage_Cheat_Sheet.md |
| session | Session_Management_Cheat_Sheet.md |
| llm, ai, prompt injection | LLM_Prompt_Injection_Prevention_Cheat_Sheet.md |

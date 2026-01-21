---
description: Look up OWASP security cheatsheets by topic
model: haiku
---

# Security Cheatsheet Lookup

Look up OWASP security guidance for the user.

## Target Topic

$ARGUMENTS

## Instructions

1. **If topic provided**: Find the matching cheatsheet(s) from the index below
2. **If no topic provided**: Ask what security topic they need help with
3. **Return**: The summary and link to the full OWASP guide

---

# OWASP Cheat Sheet Series Index

## Authentication & Access Control

### Authentication
Provides guidance on implementing secure authentication mechanisms for web applications. Covers topics including password requirements, multi-factor authentication, secure credential storage, and protection against common authentication attacks. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)

### Authorization
Guidance on implementing authorization mechanisms that ensure users can only access resources they are permitted to use. Covers access control models, authorization best practices, and common vulnerabilities. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)

### Authorization Testing Automation
Provides a methodology for automating authorization testing to validate that access controls are properly enforced. Helps security testers and developers verify that users cannot access unauthorized resources. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Testing_Automation_Cheat_Sheet.html)

### Choosing and Using Security Questions
Guidance on implementing security questions as a secondary authentication mechanism. Discusses the inherent weaknesses of security questions and provides recommendations for making them more secure when they must be used. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Choosing_and_Using_Security_Questions_Cheat_Sheet.html)

### Credential Stuffing Prevention
Describes techniques to prevent credential stuffing attacks where attackers use stolen username/password pairs from data breaches to gain unauthorized access. Covers detection and mitigation strategies. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Credential_Stuffing_Prevention_Cheat_Sheet.html)

### Forgot Password
Best practices for implementing secure password reset functionality. Covers secure token generation, user verification, and protection against account enumeration attacks. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html)

### JAAS (Java Authentication and Authorization Service)
Guidance on securely implementing JAAS in Java applications for authentication and authorization. Covers configuration best practices and common security pitfalls. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/JAAS_Cheat_Sheet.html)

### JSON Web Token for Java
Provides best practices for implementing JWT-based authentication in Java applications. Covers token creation, validation, storage, and common vulnerabilities like algorithm confusion attacks. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)

### Multifactor Authentication
Guidance on implementing MFA to add additional layers of security beyond passwords. Covers various MFA methods, implementation considerations, and user experience best practices. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Multifactor_Authentication_Cheat_Sheet.html)

### OAuth 2.0 Protocol
Security best practices for OAuth 2.0 implementations derived from its RFC. Covers PKCE, token handling, client authentication, and protection against common OAuth attacks. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/OAuth2_Cheat_Sheet.html)

### Password Storage
Advises on proper methods for storing passwords securely using modern hashing algorithms. Recommends Argon2id, scrypt, or bcrypt with appropriate configurations and explains salting and peppering techniques. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)

### SAML Security
Security guidance for implementing SAML-based single sign-on. Covers message confidentiality, integrity, signature validation, and protection against XML signature wrapping attacks. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/SAML_Security_Cheat_Sheet.html)

### Session Management
Comprehensive guide to secure session management in web applications. Covers session ID generation, secure cookie attributes, session lifecycle management, and protection against session hijacking. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)

### Transaction Authorization
Guidance for securing transaction authorizations and preventing bypass attacks. Helps banks, developers, and pentesters implement and validate secure transaction authorization mechanisms. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Transaction_Authorization_Cheat_Sheet.html)

---

## Injection Prevention

### SQL Injection Prevention
Comprehensive guide to preventing SQL injection attacks through parameterized queries, stored procedures, and input validation. Shows code examples across multiple programming languages. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)

### Query Parameterization
Demonstrates how to build parameterized queries in common web languages to prevent SQL injection. A derivative of the SQL Injection Prevention Cheat Sheet with practical code examples. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Query_Parameterization_Cheat_Sheet.html)

### OS Command Injection Defense
Guidance on preventing command injection attacks where attackers can execute arbitrary OS commands. Covers input validation, avoiding direct OS command calls, and using safe APIs. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html)

### LDAP Injection Prevention
Techniques to prevent LDAP injection attacks that can manipulate LDAP queries. Covers input validation, escaping special characters, and secure LDAP query construction. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/LDAP_Injection_Prevention_Cheat_Sheet.html)

### Injection Prevention
General guidance on preventing various types of injection attacks beyond SQL. Covers command injection, LDAP injection, XPath injection, and other injection attack vectors. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Injection_Prevention_Cheat_Sheet.html)

### Input Validation
Best practices for validating user input to prevent various attacks. Covers allowlist vs blocklist approaches, data type validation, and handling of special characters. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)

### XML External Entity Prevention
Guidance on preventing XXE attacks that can lead to data disclosure, SSRF, and denial of service. Covers parser configuration for disabling external entities across various languages. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html)

### XML Security
Awareness of security flaws in XML specifications and how attackers exploit malformed and invalid XML documents. Covers safe XML parsing practices and protection against various XML-based attacks. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/XML_Security_Cheat_Sheet.html)

### Bean Validation
Security guidance for Java Bean Validation to ensure proper input constraints. Covers annotation-based validation and integration with application frameworks. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Bean_Validation_Cheat_Sheet.html)

### Deserialization
Guidance on preventing insecure deserialization vulnerabilities that can lead to remote code execution. Covers safe deserialization practices across multiple programming languages. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html)

---

## Web Application Security

### Cross Site Scripting Prevention
Comprehensive guide to preventing XSS attacks through output encoding, input validation, and Content Security Policy. Covers reflected, stored, and DOM-based XSS. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)

### DOM based XSS Prevention
Specific guidance for preventing DOM-based XSS where the attack payload is executed through client-side JavaScript manipulation. Covers safe DOM manipulation practices. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html)

### DOM Clobbering Prevention
Techniques to prevent DOM Clobbering attacks where attackers can overwrite DOM properties and objects. Covers naming conventions and validation strategies. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/DOM_Clobbering_Prevention_Cheat_Sheet.html)

### XSS Filter Evasion
A comprehensive list of XSS attack vectors demonstrating that input filtering alone is insufficient defense. Useful for security testers to validate XSS protections. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/XSS_Filter_Evasion_Cheat_Sheet.html)

### Cross-Site Request Forgery Prevention
Guidance on preventing CSRF attacks where attackers trick users into performing unintended actions. Covers synchronizer tokens, SameSite cookies, and other defense mechanisms. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)

### Clickjacking Defense
Techniques to prevent clickjacking attacks where malicious sites trick users into clicking hidden elements. Covers X-Frame-Options, CSP frame-ancestors, and JavaScript frame-busting. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Clickjacking_Defense_Cheat_Sheet.html)

### Content Security Policy
Guide to implementing CSP headers to mitigate XSS and other code injection attacks. Covers policy directives, deployment strategies, and reporting. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html)

### Server-Side Request Forgery Prevention
Guidance on preventing SSRF attacks where applications can be tricked into making requests to internal resources. Covers input validation, allowlisting, and network-level protections. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)

### Unvalidated Redirects and Forwards
Techniques to prevent attacks that exploit open redirects to phish users or bypass access controls. Covers validation strategies and safe redirect implementations. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html)

### File Upload
Security guidance for handling file uploads safely. Covers file type validation, storage location, filename sanitization, and protection against malicious uploads. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)

### Insecure Direct Object Reference Prevention
Guidance on preventing IDOR vulnerabilities where attackers can access unauthorized resources by manipulating object references. Covers access control validation strategies. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html)

### HTTP Headers
Comprehensive guide to security-related HTTP headers and their proper configuration. Covers response headers that protect against various web attacks. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html)

### HTTP Strict Transport Security
Guide to implementing HSTS to protect against protocol downgrade attacks and cookie hijacking. Covers header configuration and preloading. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Strict_Transport_Security_Cheat_Sheet.html)

### HTML5 Security
Security considerations for HTML5 features including Web Storage, WebSockets, and new APIs. Covers safe usage patterns and common vulnerabilities. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html)

### AJAX Security
Security guidance for AJAX-based applications covering same-origin policy, CORS, and protection against client-side attacks. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/AJAX_Security_Cheat_Sheet.html)

### Cookie Theft Mitigation
Techniques to protect cookies from theft and misuse including secure and HttpOnly flags, SameSite attributes, and session management best practices. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Cookie_Theft_Mitigation_Cheat_Sheet.html)

### Prototype Pollution Prevention
Guidance on preventing prototype pollution attacks in JavaScript applications that can lead to unauthorized data access or code execution. Covers safe object creation patterns. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Prototype_Pollution_Prevention_Cheat_Sheet.html)

### Cross-site Leaks
Describes XS-Leak vulnerabilities that exploit browser side-channels to leak cross-origin information. Covers attack vectors and defense mechanisms like SameSite cookies. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/XS_Leaks_Cheat_Sheet.html)

### Securing Cascading Style Sheets
Security considerations when authoring CSS to prevent information leakage about application features and roles. Covers CSS isolation and obfuscation techniques. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Securing_Cascading_Style_Sheets_Cheat_Sheet.html)

### Third Party JavaScript Management
Guidance on mitigating risks from third-party JavaScript including loss of control, arbitrary code execution, and data leakage. Covers subresource integrity and sandboxing. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Third_Party_Javascript_Management_Cheat_Sheet.html)

### Third Party Payment Gateway Integration
Secure practices for integrating third-party payment gateways to prevent payment spoofing, order manipulation, and fraud. Covers the typical payment flow and security at each step. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Third_Party_Payment_Gateway_Integration.html)

### Mass Assignment
Guidance on preventing mass assignment vulnerabilities where attackers can modify object properties they shouldn't have access to. Covers allowlisting and input filtering. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html)

### Browser Extension Vulnerabilities
Security considerations for browser extensions that have elevated privileges. Covers common vulnerability patterns and secure development practices. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Browser_Extension_Vulnerabilities_Cheat_Sheet.html)

### WebSocket Security
Security guide for WebSocket implementations covering CSWSH prevention, authentication, injection attacks, and DoS protection. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html)

---

## API & Web Services

### REST Security
Comprehensive security guide for RESTful APIs covering HTTPS, access control, JWT handling, input validation, and response security. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html)

### REST Assessment
Guide for security testing RESTful web services covering attack surface identification, parameter discovery, and fuzzing techniques. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/REST_Assessment_Cheat_Sheet.html)

### Web Service Security
Security guidance for web services including transport encryption, authentication, authorization, and message integrity. Covers both REST and SOAP services. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Web_Service_Security_Cheat_Sheet.html)

### GraphQL
Security considerations specific to GraphQL APIs including query complexity limits, introspection controls, and authorization. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/GraphQL_Cheat_Sheet.html)

### gRPC Security
Security guidance for gRPC services covering TLS configuration, authentication, and secure message handling. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/gRPC_Security_Cheat_Sheet.html)

### Microservices Security
Comprehensive security guidance for microservices architectures covering service-to-service authentication, API gateways, and distributed security patterns. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Microservices_Security_Cheat_Sheet.html)

### Microservices Security Architecture Documentation
Guide for documenting security architecture in microservices environments to ensure consistent security implementations. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Microservices_based_Security_Arch_Doc_Cheat_Sheet.html)

---

## Infrastructure & DevOps

### Docker Security
Security best practices for Docker containers including image security, runtime protection, and secure configuration. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html)

### Node.js Docker
Production-grade guidelines for building optimized and secure Node.js Docker containers. Covers base image selection, multi-stage builds, and security hardening. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/NodeJS_Docker_Cheat_Sheet.html)

### Kubernetes Security
Comprehensive security guide for Kubernetes deployments covering pod security, RBAC, network policies, and secrets management. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Kubernetes_Security_Cheat_Sheet.html)

### Serverless / FaaS Security
Security best practices for serverless platforms like AWS Lambda, Azure Functions, and Google Cloud Functions. Covers IAM, environment isolation, and input validation. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Serverless_FaaS_Security_Cheat_Sheet.html)

### Infrastructure as Code Security
Security guidance for IaC tools like Terraform and CloudFormation covering secrets management, policy enforcement, and secure deployment practices. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Infrastructure_as_Code_Security_Cheat_Sheet.html)

### CI/CD Security
Security best practices for continuous integration and deployment pipelines covering access control, secrets management, and artifact integrity. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/CI_CD_Security_Cheat_Sheet.html)

### Database Security
Guidance on securing databases including access control, encryption, query security, and audit logging. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Database_Security_Cheat_Sheet.html)

### NoSQL Security
Security guidance for NoSQL databases covering injection prevention, authentication, access control, and network security for MongoDB, CouchDB, Cassandra and others. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/NoSQL_Security_Cheat_Sheet.html)

### Network Segmentation
Guide to implementing network segmentation for defense in depth. Covers DMZ design, microsegmentation, and access control between network zones. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Network_Segmentation_Cheat_Sheet.html)

### Secure Cloud Architecture
Security guidelines for cloud architectures covering risk assessment, public/private components, and secure storage patterns for medium to large scale enterprise systems. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Cloud_Architecture_Cheat_Sheet.html)

### Denial of Service
Guidance on protecting applications against DoS attacks through rate limiting, resource management, and architectural patterns. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Denial_of_Service_Cheat_Sheet.html)

### Multi-Tenant Security
Security considerations for multi-tenant applications covering data isolation, access control, and resource management. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html)

### Virtual Patching
Framework for implementing virtual patches to mitigate known vulnerabilities quickly while source code fixes are developed. Uses WAF and similar tools for mitigation. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Virtual_Patching_Cheat_Sheet.html)

---

## Data Protection & Cryptography

### Cryptographic Storage
Guidance on properly storing sensitive data using encryption. Covers algorithm selection, key management, and secure implementation patterns. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)

### Key Management
Best practices for cryptographic key management including generation, storage, rotation, and destruction of encryption keys. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html)

### Transport Layer Security
Comprehensive guide to TLS implementation covering protocol versions, cipher suites, certificate management, and proper configuration. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html)

### Pinning
Technical guide to certificate and public key pinning for securing communication channels against MITM attacks. Discusses when pinning is appropriate and implementation approaches. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Pinning_Cheat_Sheet.html)

### Secrets Management
Best practices for centralized storage, provisioning, auditing, and rotation of secrets like API keys, credentials, and certificates. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

### User Privacy Protection
Mitigation methods to protect user privacy and anonymity including strong cryptography, HSTS, and privacy-focused design patterns. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/User_Privacy_Protection_Cheat_Sheet.html)

---

## AI/LLM Security

### AI Agent Security
Security guidance for AI agent systems covering prompt injection, data leakage, and secure integration patterns for autonomous AI applications. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html)

### LLM Prompt Injection Prevention
Techniques to prevent prompt injection attacks against large language models that can manipulate AI behavior and leak sensitive information. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)

### Secure AI/ML Model Ops
Practical security guidance for operating and deploying AI/ML systems including protection against data poisoning, model theft, and adversarial attacks. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Secure_AI_Model_Ops_Cheat_Sheet.html)

---

## Secure Development Practices

### Secure Code Review
Methodology for manual security code review to identify vulnerabilities automated tools miss. Covers preparation, review process, and common vulnerability patterns. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Code_Review_Cheat_Sheet.html)

### Secure Product Design
Guidance on building security into products from inception through the development lifecycle. Covers security principles like least privilege, defense-in-depth, and zero trust. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Product_Design_Cheat_Sheet.html)

### Threat Modeling
Structured process for identifying security threats and determining mitigations during application design. Covers system modeling, threat identification, and risk response. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html)

### Attack Surface Analysis
Methodology for identifying and reducing the attack surface of applications to minimize security risk. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Attack_Surface_Analysis_Cheat_Sheet.html)

### Abuse Case
Guide to identifying potential abuse scenarios for application features to drive security requirements. Helps teams think like attackers during design. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Abuse_Case_Cheat_Sheet.html)

### Error Handling
Best practices for secure error handling that prevents information leakage while maintaining usability. Covers logging, error messages, and exception handling. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet.html)

### Logging
Security guidance for application logging covering what to log, secure storage, and protection against log injection attacks. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)

### Logging Vocabulary
Standardized vocabulary for security event logging to enable consistent analysis and correlation across applications. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Vocabulary_Cheat_Sheet.html)

### Software Supply Chain Security
Guidance on securing the software supply chain from source code through deployment. Covers dependency management, build security, and artifact integrity. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Software_Supply_Chain_Security_Cheat_Sheet.html)

### Dependency Graph / SBOM
Guide to creating and using Software Bills of Materials for tracking dependencies and managing supply chain security. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Dependency_Graph_SBOM_Cheat_Sheet.html)

### NPM Security
Best practices for npm package management including avoiding published secrets, enforcing lockfiles, and minimizing attack surfaces. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/NPM_Security_Cheat_Sheet.html)

### Vulnerability Disclosure
Guidance for both security researchers and organizations on responsible vulnerability disclosure processes and communication. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Vulnerability_Disclosure_Cheat_Sheet.html)

### Legacy Application Management
Strategies for managing security risks in legacy applications that cannot be easily updated or replaced. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Legacy_Application_Management_Cheat_Sheet.html)

---

## Framework-Specific Security

### Node.js Security
Best practices for securing Node.js applications covering application security, error handling, server security, and platform security. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Nodejs_Security_Cheat_Sheet.html)

### Java Security
Security guidance specific to Java applications covering common vulnerabilities and secure coding practices. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Java_Security_Cheat_Sheet.html)

### DotNet Security
Security best practices for .NET applications covering authentication, authorization, input validation, and secure configuration. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/DotNet_Security_Cheat_Sheet.html)

### PHP Configuration
Security-focused PHP configuration guide covering php.ini settings and web server configuration for Apache, Nginx, and Caddy. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/PHP_Configuration_Cheat_Sheet.html)

### Ruby on Rails
Security tips for Rails developers covering command injection, SQL injection, XSS, and other common vulnerabilities with Rails-specific mitigations. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Ruby_on_Rails_Cheat_Sheet.html)

### Django Security
Security best practices for Django web applications covering common vulnerabilities and Django-specific security features. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Django_Security_Cheat_Sheet.html)

### Django REST Framework
Security guidance for building secure REST APIs with Django REST Framework. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Django_REST_Framework_Cheat_Sheet.html)

### Laravel
Security guidance for Laravel PHP framework covering authentication, CSRF protection, and secure configuration. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Laravel_Cheat_Sheet.html)

### Symfony
Security tips for Symfony PHP framework covering XSS, CSRF, SQL injection, and other common vulnerabilities with Symfony-specific mitigations. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Symfony_Cheat_Sheet.html)

### C-Based Toolchain Hardening
Security guidance for C/C++ development including compiler flags and toolchain options that improve security. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/C-Based_Toolchain_Hardening_Cheat_Sheet.html)

---

## Mobile & IoT Security

### Mobile Application Security
Security considerations for mobile applications covering data storage, network communication, authentication, and platform-specific security. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Mobile_Application_Security_Cheat_Sheet.html)

### Automotive Security
Security guidance for automotive systems including connected vehicles, ECUs, and vehicle-to-everything (V2X) communication. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Automotive_Security.html)

### Drone Security
Security considerations for unmanned aerial systems covering communication security, firmware integrity, and operational security. [Full Guide](https://cheatsheetseries.owasp.org/cheatsheets/Drone_Security_Cheat_Sheet.html)

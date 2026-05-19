# Threat Model — CyberQuest

## Overview
This document outlines identified threats and mitigations for the CyberQuest system.

## STRIDE Analysis

| Threat | Description | Mitigation |
|--------|-------------|------------|
| Spoofing | Unauthorised login | bcrypt + 2FA |
| Tampering | Modifying scores | Server-side validation |
| Repudiation | Denying actions | Login attempt logging |
| Information Disclosure | Data leaks | RBAC, no debug in prod |
| Denial of Service | Flooding login | Rate limiting (future) |
| Elevation of Privilege | Student → Teacher | Role-checked decorators |

## To be completed by: Member 1

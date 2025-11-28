1. Product Summary

SentinelVNC is a real-time security system that detects and prevents VNC-based data exfiltration using:

Network analysis

Application analysis

Visual OCR + steganography checks

AI-based risk scoring

Automated response

Immutable blockchain logging

2. Users & Stakeholders

SOC Analysts

Security Administrators

Incident Response Teams

Auditors

Compliance Officers

3. Product Objectives

Detect malicious exfiltration attempts

Respond automatically

Provide clear forensic evidence

Ensure immutability via blockchain

Enable analyst review with explanations

4. Success Metrics
Metric	Target
Detection Accuracy	≥ 90%
False Positives	≤ 5%
Response Time	≤ 2 sec
Blockchain Integrity	100% consistency
Dashboard Latency	< 1 sec refresh
5. Scope
In-Scope

VNC monitoring

Detection engine

Automated response

Forensics capture

Blockchain integrity

Out-of-Scope

Other remote protocols

Mobile VNC clients

6. Functional Requirements
Proxy

Intercept sessions

Split into 3 streams

Detectors

Network: DNS/ICMP, file transfer

App: clipboard, keystrokes

Visual: OCR, steganography

Risk Engine

Multi-event correlation

Risk scoring algorithm

Response

Allow / deceive / kill

Forensics

PCAP + screenshots + manifest

Blockchain

Store incident hash

Dashboard

UI for incidents

Evidence viewer

Risk explanations

7. Non-Functional Requirements

Real-time (<2s response)

99% uptime

Secure storage

Horizontal scaling

Low latency

8. User Stories

As an analyst, I want to see all incidents.

As an admin, I want to auto-kill high-risk sessions.

As an auditor, I want immutable logs.
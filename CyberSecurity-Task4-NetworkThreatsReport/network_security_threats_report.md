# Common Network Security Threats

## Introduction

Networks connect users, applications, and data across organizational boundaries. A failure
of availability can interrupt essential services; weak identity and transport controls can
expose information or enable impersonation. Administrators should use layered controls,
monitor for abnormal behavior, and plan incident response. The examples below describe
threats for defensive awareness, not instructions for conducting them.

## Denial of Service and Distributed DoS

**How it works.** A denial-of-service (DoS) event overwhelms a service or its network path
with work or traffic. A distributed attack uses many sources; reflection/amplification can
abuse exposed third-party services and falsified source addressing to send larger replies
toward a victim.

**Documented incident and impact.** GitHub's February 2018 incident report describes a
memcached reflection attack that peaked at 1.35 Tbps and caused a short period of
unavailability. The report notes that the incident affected availability, not
confidentiality or integrity.

**Mitigations.**
1. Use upstream DDoS protection, scrubbing, and resilient capacity/peering appropriate to
   the service's risk.
2. Disable or firewall unnecessary UDP reflection services; use source-address validation
   at network edges where feasible.
3. Monitor traffic and service health, rehearse provider escalation, and keep a tested
   failover/incident plan.

## Man-in-the-Middle (MITM)

**How it works.** An adversary positioned between two communicating parties may observe,
relay, or alter traffic when endpoint authentication or transport protection is weak.
Possession of a trusted certificate or compromised network component can make a fraudulent
endpoint appear legitimate.

**Documented example and impact.** In 2011, Google reported a certificate-authority
incident in which fraudulent certificates could enable impersonation of Google services.
Certificate revocation and browser protections reduced exposure. The incident illustrates
why certificate issuance and trust-store monitoring matter; it does not mean TLS is
inherently ineffective.

**Mitigations.**
1. Require modern TLS, validate certificates, and never suppress certificate warnings.
2. Use phishing-resistant multifactor authentication and protect endpoints and DNS.
3. Monitor certificate-transparency and identity-provider signals; revoke compromised
   credentials/certificates through a practiced response process.

## IP Spoofing

**How it works.** IP spoofing forges the source address in a packet. It can obscure origin
or facilitate reflection attacks, but by itself does not authenticate a user or prove that
the spoofed host was compromised.

**Documented example and impact.** GitHub's 2018 DDoS report explains how source-address
spoofing helped direct amplified memcached responses toward its infrastructure. Spoofing
can frustrate attribution, enable traffic reflection, and contribute to service outages.

**Mitigations.**
1. Apply ingress and egress source-address validation (BCP 38/RFC 2827) at network
   boundaries.
2. Restrict services that can be abused as reflectors; rate-limit and filter anomalous
   traffic upstream.
3. Correlate network telemetry with provider data; do not treat a packet's source address
   as proof of identity.

## DNS Poisoning and Hijacking

**How it works.** DNS poisoning/hijacking changes or forges name-resolution information so
that a client reaches an unintended endpoint. This may occur through compromised registrar
accounts, name-server configuration, resolver cache manipulation, or control-plane access.

**Documented example and impact.** CISA's 2019 advisory on a global DNS infrastructure
hijacking campaign describes attackers using compromised credentials to alter DNS records,
redirect traffic, and obtain valid encryption certificates for affected domains. This can
enable interception or impersonation; actual exposure depends on the services and controls
in place.

**Mitigations.**
1. Protect registrar and DNS-provider accounts with phishing-resistant MFA, role separation,
   and change alerts.
2. Use DNSSEC validation where supported, encrypted resolver transport where appropriate,
   and strong certificate validation.
3. Monitor DNS configuration and certificate issuance; keep a recovery plan for restoring
   known-good records and rotating credentials.

## Comparison

| Threat | Typical vector | Who is at risk | Execution difficulty (context-dependent) | Mitigation ease |
|---|---|---|---|---|
| DoS/DDoS | Traffic exhaustion or reflection | Public services and their users | Medium to high; tooling and capacity vary | Medium; upstream coordination is often needed |
| MITM | Untrusted network, endpoint, or certificate path | Users of affected services | Medium to high | Medium; TLS, identity, and monitoring help |
| IP spoofing | Forged packet source address | Network operators and reflected-traffic victims | Low to forge; impact depends on network controls | Medium; boundary filtering requires provider support |
| DNS poisoning/hijacking | Resolver, registrar, or DNS control-plane abuse | Organizations and their customers | Medium to high | Medium; account hardening and recovery planning are essential |

## Administrator takeaways

1. Build layered controls: availability, trusted identity, DNS integrity, and network-edge
   filtering solve different parts of the problem.
2. Keep an inventory of internet-facing services and remove unnecessary exposure.
3. Monitor, rehearse response, and treat provider/registrar recovery as part of incident
   readiness.

## References

1. GitHub, [February 28th DDoS Incident Report](https://github.blog/news-insights/company-news/ddos-incident-report/), 2018.
2. Google Security Blog, [An update on attempted man-in-the-middle attacks](https://security.googleblog.com/2011/08/update-on-attempted-man-in-middle.html), 2011.
3. CISA, [DNS Infrastructure Hijacking Campaign (AA19-024A)](https://www.cisa.gov/news-events/cybersecurity-advisories/aa19-024a), 2019.
4. IETF, [RFC 2827: Network Ingress Filtering](https://www.rfc-editor.org/rfc/rfc2827).
5. NIST, [SP 800-81 Rev. 3: Secure Domain Name System (DNS) Deployment Guide](https://csrc.nist.gov/pubs/sp/800/81/r3/final), 2026.

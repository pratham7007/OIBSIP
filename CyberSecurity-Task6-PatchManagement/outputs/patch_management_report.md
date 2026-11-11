# The Importance of Patch Management

## Introduction

Patch management is the process of identifying, prioritizing, acquiring, installing, and
verifying software updates. It is a preventive-maintenance activity within vulnerability
management: a published vulnerability may have a vendor fix, but risk remains until
affected assets are identified and the fix is applied or an approved compensating control
is in place.

## Why patches matter

Vulnerabilities are reported and catalogued with identifiers such as CVEs. A CVE record
helps stakeholders refer to a specific issue; severity scoring (for example CVSS) supports
prioritization but is not a substitute for assessing exposure, exploit activity, and
business context.

- **WannaCry (2017):** the ransomware outbreak exploited SMBv1 vulnerabilities addressed
  by Microsoft security updates before the outbreak. The UK's National Audit Office
  documented disruption to NHS services, illustrating the operational impact of delayed
  remediation and unsupported systems.
- **Equifax (2017):** the U.S. Government Accountability Office reported that the breach
  involved exploitation of an Apache Struts vulnerability for which a patch had been
  available. This is a documented patching failure, not a claim that patch management
  alone explains the full breach. The incident exposed sensitive personal information
  and led to extensive regulatory and remediation consequences.

Unpatched systems can enable unauthorized access, ransomware, data loss, service
disruption, and compliance failures. Security teams should distinguish confirmed facts
from assumptions about exploitability and apply patches according to risk.

## Patch-management lifecycle

1. **Discovery:** maintain an inventory of hardware, operating systems, applications,
   owners, dependencies, and support status.
2. **Assessment:** match advisories to assets; prioritize known exploitation, exposure,
   potential impact, and available mitigations.
3. **Testing:** validate patches on representative systems and test backups, rollback, and
   business-critical workflows.
4. **Deployment:** roll out in risk-based waves with change approval and an emergency path
   for actively exploited issues.
5. **Verification:** confirm installation and service health; rescan inventory, document
   exceptions, and set expiry/review dates for compensating controls.

## Seven-step priority checklist

1. Establish an accurate asset and software inventory, including end-of-life systems.
2. Subscribe to vendor and CISA alerts and assign an accountable system owner.
3. Prioritize exploited and internet-exposed vulnerabilities using context, not CVSS alone.
4. Define regular patch windows and an expedited emergency-change process.
5. Test updates and backups in a representative staging environment.
6. Deploy in controlled waves; isolate or apply compensating controls where patching is
   temporarily unsafe.
7. Verify completion, track exceptions to an owner/deadline, and report patch latency.

## Common challenges and responses

| Challenge | Practical response |
|---|---|
| Legacy or unsupported software | Plan migration; isolate and restrict access while a funded exception remains |
| Downtime concerns | Use staged rollout, maintenance windows, redundancy, and tested rollback |
| Incomplete asset inventory | Reconcile endpoint, cloud, and software inventories; assign owners |
| Patch breaks an application | Test representative workflows and coordinate vendor support |
| Remote/offline endpoints | Use endpoint management, deadlines, and clear compliance reporting |
| Change fatigue | Risk-rank updates and automate routine, reversible deployment |

## Conclusion

Patching reduces exposure only when teams know what they operate, prioritize work based on
current risk, and verify that updates actually landed. Exceptions should be explicit,
time-bounded, and paired with compensating controls. Executive reporting should focus on
coverage, time-to-remediate, and overdue high-risk assets.

## References

1. NIST, [SP 800-40 Rev. 4: Guide to Enterprise Patch Management Planning](https://csrc.nist.gov/pubs/sp/800/40/r4/final), 2022.
2. CISA, [Known Exploited Vulnerabilities Catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog).
3. MITRE, [Common Vulnerabilities and Exposures (CVE)](https://www.cve.org/).
4. FIRST, [Common Vulnerability Scoring System (CVSS)](https://www.first.org/cvss/).
5. UK National Audit Office, [Investigation: WannaCry cyber attack and the NHS](https://www.nao.org.uk/reports/investigation-wannacry-cyber-attack-and-the-nhs/), 2017.
6. U.S. GAO, [Data Protection: Actions Taken by Equifax and Federal Agencies in Response to the 2017 Breach](https://www.gao.gov/products/gao-18-559), 2018.

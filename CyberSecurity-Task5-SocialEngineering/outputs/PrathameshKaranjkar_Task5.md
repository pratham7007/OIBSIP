# Social Engineering Attacks: Risks and Defenses

## Introduction

Social engineering uses deception and human context to persuade someone to disclose
information, approve an action, or bypass a process. It is effective because an attacker
can exploit trust, urgency, authority, or routine rather than defeat a technical control.
The FBI's 2023 Internet Crime Report documents the continuing scale of reported online
crime, but complaint totals are not a measure of every social-engineering event and should
not be presented as a phishing success rate.

## Phishing

Phishing messages impersonate a trusted person or service to prompt a click, credential
entry, payment, or attachment opening. **Spear phishing** is tailored to a person or team;
**whaling** targets senior decision-makers; **vishing** uses voice calls; **smishing** uses
SMS or messaging apps.

**Case study.** In July 2020, attackers used social engineering against employees to gain
access to internal tools at Twitter. Twitter reported account compromise and unauthorized
posts from high-profile accounts; DOJ later charged three people for alleged roles in the
incident. The charges are allegations, not findings of guilt. The case demonstrates that
employee verification and tightly scoped administrative access matter even when the
company has technical controls.

**Prevention.**
1. Use phishing-resistant MFA and password managers; do not approve unexpected
   authentication prompts.
2. Verify payment, credential, or access requests through a separately known channel.
3. Filter and report suspicious messages; isolate attachments and links in a controlled
   analysis workflow.
4. Restrict privileged access, use just-in-time approval, and alert on unusual admin-tool
   activity.

## Pretexting

Pretexting is a fabricated scenario used to make a request seem legitimate, such as a
supposed executive, supplier, auditor, or IT support representative. The target may be
asked to change payment details, reveal a code, or bypass a normal check.

**Case study (with caveat).** The 2020 Twitter incident is a documented example of
employee-targeted social engineering. Public official reporting supports the broad tactic;
this report does not assert a particular fabricated support pretext without a source that
substantiates that detail.

**Prevention.**
1. Require dual approval and out-of-band verification for money movement and account
   recovery.
2. Publish a simple process for support staff to authenticate themselves; never ask users
   to disclose MFA codes.
3. Provide a rapid reporting path and ensure reports are handled without blame.

## Baiting

Baiting offers something enticing in order to prompt unsafe action. Physical bait can
involve an unknown removable drive; digital bait can be a purported document, download, or
offer that leads to an unsafe file or site.

**Related example.** CISA warns that unknown USB drives can carry malware and advises
against plugging them in. This supports the risk of untrusted removable media, but does not
by itself establish intentional baiting or how a specific infection began.

**Prevention.**
1. Disable autorun and block unapproved removable storage with centrally managed controls.
2. Do not connect found media or install unapproved software; use approved request channels.
3. Keep endpoint protection and application allow-listing current; report suspicious media
   for safe handling.

## Quid pro quo

Quid pro quo offers a benefit or service in exchange for information or action, for example
a caller offering technical help in exchange for credentials. Staff should use only
approved support channels, refuse credential disclosure, and independently verify
unexpected offers.

## Comparison

| Type | Primary target | Psychological lever | Best countermeasure |
|---|---|---|---|
| Phishing | Email, messaging, or account users | Urgency, curiosity, trust | Phishing-resistant MFA and independent verification |
| Pretexting | Employees with access or authority | Authority and plausibility | Dual control and trusted callback procedures |
| Baiting | Users of devices or downloads | Curiosity or reward | Removable-media controls and approved software channels |
| Quid pro quo | Users seeking help or a benefit | Reciprocity | Approved support process; never disclose credentials |

## Five-point awareness checklist

1. Practice verifying unusual requests using known contact details.
2. Teach staff to report messages, calls, and unexpected MFA prompts quickly.
3. Include executives and support desks in role-specific exercises.
4. Rehearse payment and account-recovery controls with finance and IT.
5. Measure reporting speed and process improvements, not employee blame.

## References

1. CISA, [Recognize and Report Phishing](https://www.cisa.gov/secure-our-world/recognize-and-report-phishing).
2. U.S. Department of Justice, [Three Individuals Charged for Alleged Roles in Twitter Hack](https://www.justice.gov/usao-ndca/pr/three-individuals-charged-their-alleged-roles-twitter-hack), 2020.
3. CISA, [Using Caution with USB Drives](https://www.cisa.gov/news-events/news/using-caution-usb-drives).
4. FBI, [2023 Internet Crime Report](https://www.ic3.gov/AnnualReport/Reports/2023_IC3Report.pdf).

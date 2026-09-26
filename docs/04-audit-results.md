# 04 - Audit Results

Output of OpenClaw's built-in security audit, plus how the controls map to the
NIST Cybersecurity Framework 2.0.

Command:

```bash
openclaw security audit
```

To save a copy:

```bash
openclaw security audit > ~/audit.txt 2>&1
```

`audit.txt` is gitignored.

---

## Scorecard

| Metric | Baseline | After Fix 1 | After Fix 2 |
|---|---|---|---|
| Critical | 0 | 0 | 0 |
| Warnings | 3 | 3 | **PENDING - not recorded** |

### About that pending cell

**I never re-ran the audit after Fix 2.** There is no recorded number, so this
document does not print one.

I could estimate. Warning 1 was caused by the Telegram group allowlist, and Fix
2 removed it, so it *should* be gone. But "should be" is not a measurement, and
a security document that presents an expectation as a result is not worth
reading.

To fill in the cell:

```bash
openclaw security audit > ~/audit.txt 2>&1
```

This is a **High** priority open item.

Note that warnings stayed at 3 after Fix 1 as well. Fix 1 changed
`tools.fs.workspaceOnly` from `false` to `true`, which was a genuine
improvement, but it was not itself one of the three warnings. Fixing a real
problem does not always move the counter.

---

## Findings

### Warning 1 - `security.trust_model.multi_user_heuristic`

**Cause.** The Telegram group allowlist contained a wildcard, so OpenClaw
inferred the deployment was multi-user. I had designed it as single-user. The
config disagreed with my intent.

**Status: FIXED by Fix 2.** The `groups` block was removed and
`groupPolicy: "disabled"` was set.

**Verification: pending re-run.**

---

### Warning 2 - Runtime and process tools without full sandbox

**Cause.** `sandbox=off`, with `exec` and process tools enabled.

**Status: OPEN. Deferred.** Full sandbox mode needs Docker inside the distro.

**Compensating control.** Distro isolation: dedicated WSL2 distro, no `/mnt/c`,
Windows interop off, unprivileged dedicated user. This limits the blast radius.
It does not prevent the compromise.

---

### Warning 3 - `plugins.installs_unpinned_npm_specs`

**Cause.** `@openclaw/duckduckgo-plugin` is installed without a version pin.

**Status: OPEN. Low risk.** One package, official `@openclaw` scope, holds no
credential.

---

## Attack surface (informational)

| Item | Value | Assessment |
|---|---|---|
| Groups open | 0 | Good, after Fix 2 |
| `tools.elevated` | enabled | Review - default, not chosen |
| Webhooks | disabled | Good - no inbound HTTP |
| Internal hooks | enabled | Default, gateway-internal |
| Browser control | enabled | Review - widens injection exposure |

---

## Control mapping - NIST CSF 2.0

### Verification note

The framework codes below were checked against the published CSF 2.0 document,
not from memory. Method and results are in the next section.

| # | Control | Implementation | CSF 2.0 | Status |
|---|---|---|---|---|
| C1 | Isolation / segmentation | Dedicated WSL2 distro `openclaw`, no `/mnt/c`, interop off | **PR.IR** | Implemented |
| C2 | Least privilege | Dedicated `claw` user, no skills, no extra plugins, `fs.workspaceOnly=true` | **PR.AA** | Implemented |
| C3 | Network exposure | Gateway bound `127.0.0.1:18789`, Tailscale off, webhooks disabled | **PR.IR** | Implemented |
| C4 | Access control | Telegram DM pairing, groups disabled | **PR.AA** | Implemented |
| C5 | Identity separation | Dedicated agent Gmail, separate API keys, no billing | **PR.AA** | Implemented |
| C6 | Supply chain | Official `@openclaw` npm scope, community ClawHub skipped | **GV.SC** | Partial - plugin unpinned |
| C7 | Secrets management | Plaintext keys in config, inside isolated distro | **PR.DS** | **Gap** |
| C8 | Monitoring | `openclaw security audit`, `openclaw gateway status`, journald | **DE.CM** | Partial - not scheduled |
| C9 | Data handling | Rule: no PHI or credentials sent to the agent | **GV.PO** | Policy only |
| C10 | Availability | systemd user service with lingering enabled | **PR.IR** | Implemented |

Three rows are honest about not being finished. C6 is partial because the
plugin is unpinned. C7 is a straight gap. C8 is partial because the audit is
something I remember to run, not something scheduled.

---

## CSF 2.0 code verification

The codes above started as unverified guesses. I checked all six against the
source before publishing.

**Source checked:** *The NIST Cybersecurity Framework (CSF) 2.0*, NIST CSWP 29,
published 26 February 2024.
<https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf>

**Method:** read the CSF 2.0 Core in Appendix A of that document and matched
each Function / Category identifier and its official name.

**Result: all six codes are valid CSF 2.0 Categories. No corrections were
needed.**

| Code | Function | Official Category name | Verdict |
|---|---|---|---|
| **PR.IR** | Protect | Technology Infrastructure Resilience | Valid |
| **PR.AA** | Protect | Identity Management, Authentication, and Access Control | Valid |
| **GV.SC** | Govern | Cybersecurity Supply Chain Risk Management | Valid |
| **PR.DS** | Protect | Data Security | Valid |
| **DE.CM** | Detect | Continuous Monitoring | Valid |
| **GV.PO** | Govern | Policy | Valid |

### Two things worth knowing about CSF 2.0

**1. GOVERN is new.** CSF 2.0 has six Functions, not five: **GOVERN, IDENTIFY,
PROTECT, DETECT, RESPOND, RECOVER.** GOVERN was added in 2.0. So `GV.SC` and
`GV.PO` only exist in 2.0. Anything written against CSF 1.1 will not have them.

**2. Several Protect categories were renamed in 2.0.** CSF 1.1 had `PR.AC`
(Access Control) and `PR.IP` (Information Protection Processes). Those are
gone. `PR.AA` and `PR.PS` (Platform Security) replaced them, and `PR.IR` is
new. Using `PR.AC` in a document that claims to be CSF 2.0 is a common and
visible mistake.

### Supporting subcategories

To confirm the mappings were sensible and not just the right shape, I checked
the relevant subcategory text:

- **PR.IR-01** - "Networks and environments are protected from unauthorized
  logical access and usage." Supports C1 (isolation) and C3 (loopback bind).
- **PR.IR-03 / PR.IR-04** - resilience mechanisms and resource capacity for
  availability. Supports C10 (systemd service with lingering).
- **PR.AA-05** - access permissions, entitlements and authorizations defined in
  policy, incorporating least privilege. Supports C2 and C4.
- **PR.AA-01** - identities and credentials for authorized users, services and
  hardware are managed. Supports C5.
- **GV.SC-03 / GV.SC-06** - supply chain risk management integrated into the
  cybersecurity programme, and due diligence before acquisition. Supports C6.
- **PR.DS-01** - "The confidentiality, integrity, and availability of
  data-at-rest are protected." This is exactly what C7 fails to do. Plaintext
  keys at rest is a PR.DS-01 gap, stated plainly.
- **DE.CM-09** - computing hardware and software, runtime environments and
  their data are monitored. Supports C8.
- **GV.PO-01** - policy for managing cybersecurity risks is established.
  Supports C9.

### One mapping I would refine

C2 (least privilege) is mapped to **PR.AA**, which is right for the dedicated
user and the permission model. But "no skills, no extra plugins installed" also
lands squarely on **PR.PS-05**: *"Installation and execution of unauthorized
software are prevented."* If I were mapping this again I would split C2 across
PR.AA and PR.PS.

I am leaving the table as-is and noting the refinement here, because showing
the reasoning is more useful than a silently tidier table.

---

## What the audit actually taught me

The two problems it found were both **wizard defaults**, not mistakes I made.
`fs.workspaceOnly` defaulted to `false`. The group allowlist defaulted to a
wildcard. I had made careful choices throughout onboarding and still ended up
with both.

Reading my own config would probably not have caught them. Running the tool
did, in seconds.

## Sources

- NIST CSWP 29, *The NIST Cybersecurity Framework (CSF) 2.0*, 26 Feb 2024:
  <https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf>
- <https://docs.openclaw.ai/gateway/security>

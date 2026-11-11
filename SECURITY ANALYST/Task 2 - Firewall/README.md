# Task 2 — UFW firewall configuration

UFW is a front end for Linux netfilter rules. This folder contains a guarded script that
sets default-deny inbound/default-allow outbound, permits SSH and HTTPS, and denies HTTP.
The script has **not** been run: this Windows environment is not an Ubuntu lab.

## Important safety check

Enabling a firewall or changing SSH rules can disconnect a remote administrator. Run only
on a disposable Linux VM you control, from its console, after confirming the intended SSH
port and recovery access. The script asks for explicit confirmation and requires root.

On the VM, install UFW with the distribution package manager, inspect the script, then
run it from the VM console. Verify with `ufw status verbose`. To test a deny rule, use a
service and client you control on an isolated host-only VM network and document the result;
do not test against another network.

Rule rationale: SSH is permitted for remote administration; HTTPS for encrypted web
services; inbound HTTP is denied; unsolicited inbound connections are denied by default.
Outbound traffic is allowed for normal client use. Tailor these decisions to the host role.

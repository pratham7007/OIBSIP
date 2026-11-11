#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run from the console of your own Linux lab VM with sudo." >&2
  exit 1
fi

cat <<'NOTICE'
This changes the host firewall:
  default deny incoming; allow outgoing; allow SSH and HTTPS; deny HTTP.
It may disrupt remote access. Use only on a VM you own, from its console.
NOTICE
read -r -p "Type APPLY-FIREWALL to continue: " confirmation
if [[ "${confirmation}" != "APPLY-FIREWALL" ]]; then
  echo "No firewall changes made."
  exit 0
fi

command -v ufw >/dev/null || {
  echo "UFW is not installed. Install it using your Linux distribution's package manager." >&2
  exit 1
}

ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow https
ufw deny http
ufw --force enable
ufw status verbose

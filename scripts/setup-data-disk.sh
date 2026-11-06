#!/usr/bin/env bash
# NEXUS /data disk setup. Default is a dry-run; pass --yes to format.
set -euo pipefail

DISK="${DISK:-/dev/nvme1n1}"
EXPECTED_SERIAL="${EXPECTED_SERIAL:-ZTA82T0AB2639102R1}"
EXPECTED_MODEL_SUBSTR="ZHITAI"
MOUNT_POINT="/data"
LABEL="nexus-data"

say() { printf '\n== %s ==\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

[ -b "$DISK" ] || die "block device not found: $DISK"
MODEL="$(lsblk -dno MODEL "$DISK" | xargs)"
SERIAL="$(lsblk -dno SERIAL "$DISK" | xargs)"
SIZE="$(lsblk -dno SIZE "$DISK" | xargs)"

say "Target disk"
printf 'device : %s\nmodel  : %s\nserial : %s\nsize   : %s\n' "$DISK" "$MODEL" "$SERIAL" "$SIZE"

case "$MODEL" in
  *"$EXPECTED_MODEL_SUBSTR"*) ;;
  *) die "model does not contain $EXPECTED_MODEL_SUBSTR; refusing" ;;
esac
[ "$SERIAL" = "$EXPECTED_SERIAL" ] || die "serial mismatch; expected $EXPECTED_SERIAL, got $SERIAL"

if lsblk -ln -o TYPE "$DISK" | grep -qx 'part'; then
  die "disk already has partitions; refusing to format"
fi
if lsblk -no MOUNTPOINTS "$DISK" | grep -q '/'; then
  die "disk or partition is mounted; refusing"
fi
if [ -e "$MOUNT_POINT" ] && [ -n "$(ls -A "$MOUNT_POINT" 2>/dev/null || true)" ]; then
  die "$MOUNT_POINT already exists and is not empty; refusing"
fi

say "Planned operations"
cat <<EOF
1. wipefs -a $DISK
2. parted: GPT + one partition (0%..100%)
3. mkfs.ext4 -m 1 -L $LABEL ${DISK}p1
4. mount ${DISK}p1 at $MOUNT_POINT
5. add UUID entry to /etc/fstab (backup first)
6. create /data/{docker,k3s,models,apps,media,registry,cache,backups}
7. enable fstrim.timer
EOF

if [ "${1:-}" != "--yes" ]; then
  say "DRY RUN"
  echo "Re-run with --yes (as root) to execute:"
  echo "  sudo bash $0 --yes"
  exit 0
fi

[ "$(id -u)" -eq 0 ] || die "must run as root: sudo bash $0 --yes"

say "Wiping signatures on $DISK"
wipefs -a "$DISK"

say "Creating GPT partition"
parted -s "$DISK" mklabel gpt
parted -s -a optimal "$DISK" mkpart primary ext4 0% 100%
partprobe "$DISK" || true
udevadm settle

PART="${DISK}p1"
[ -b "$PART" ] || die "partition not found: $PART"

say "Formatting $PART as ext4"
mkfs.ext4 -m 1 -L "$LABEL" "$PART"

say "Mounting $MOUNT_POINT"
mkdir -p "$MOUNT_POINT"
UUID="$(blkid -s UUID -o value "$PART")"
[ -n "$UUID" ] || die "failed to read UUID"

cp -a /etc/fstab "/etc/fstab.bak.$(date +%Y%m%d-%H%M%S)"
if grep -qE "^[^#]+[[:space:]]+${MOUNT_POINT}[[:space:]]" /etc/fstab; then
  die "/etc/fstab already has an entry for $MOUNT_POINT"
fi
printf 'UUID=%s  %s  ext4  defaults,noatime  0  2\n' "$UUID" "$MOUNT_POINT" >> /etc/fstab
systemctl daemon-reload
mount "$MOUNT_POINT"
findmnt -no SOURCE,TARGET,FSTYPE,OPTIONS "$MOUNT_POINT"

say "Creating layout"
mkdir -p "$MOUNT_POINT"/{docker,k3s,models,apps,media,registry,cache,backups}
chown root:root "$MOUNT_POINT"/{docker,k3s}
chown -R banren45:banren45 "$MOUNT_POINT"/{models,apps,media,registry,cache,backups}
chmod 775 "$MOUNT_POINT"/{models,apps,media,registry,cache,backups}
chmod 755 "$MOUNT_POINT"

say "Enabling fstrim.timer"
systemctl enable --now fstrim.timer

say "Done"
lsblk -o NAME,SIZE,FSTYPE,LABEL,UUID,MOUNTPOINTS "$DISK"
df -hT "$MOUNT_POINT"

#!/usr/bin/env bash
# ==============================================================================
# setup_zram.sh — Kernel-level zRAM Compressed Swap Setup for 2GB Raspberry Pi 5
# Platform: Raspberry Pi OS / Debian Linux (ARM64)
# ==============================================================================
set -euo pipefail

ZRAM_SIZE_MB="${1:-1024}"
ZRAM_BYTES=$(( ZRAM_SIZE_MB * 1024 * 1024 ))

echo "=================================================================="
echo "  CONFIGURING KERNEL zRAM COMPRESSED SWAP (${ZRAM_SIZE_MB} MB LZ4)"
echo "=================================================================="

if [[ $EUID -ne 0 ]]; then
    echo "[INFO] Re-running with sudo privileges..."
    exec sudo bash "$0" "$@"
fi

# 1. Disable legacy MicroSD disk swap to avoid I/O bottlenecks and flash wear
echo "[1/5] Disabling MicroSD disk swap..."
if command -v dphys-swapfile >/dev/null 2>&1; then
    dphys-swapfile swapoff 2>/dev/null || true
    systemctl disable dphys-swapfile 2>/dev/null || true
fi

# Swapoff existing disk swap partitions/files (leaving zram if already active)
while read -r line; do
    swap_dev=$(echo "$line" | awk '{print $1}')
    if [[ "$swap_dev" != "Filename" && "$swap_dev" != *"/dev/zram"* ]]; then
        echo "Deactivating disk swap: $swap_dev"
        swapoff "$swap_dev" 2>/dev/null || true
    fi
done < /proc/swaps

# 2. Load zRAM kernel module
echo "[2/5] Initializing zRAM kernel module..."
modprobe zram num_devices=1

# Reset /dev/zram0 if it was already initialized
if [[ -e /sys/block/zram0/disksize ]]; then
    swapoff /dev/zram0 2>/dev/null || true
    echo 1 > /sys/block/zram0/reset 2>/dev/null || true
fi

# 3. Configure LZ4 compression algorithm & pool size
echo "[3/5] Configuring LZ4 compression and ${ZRAM_SIZE_MB} MB size..."
if grep -q "lz4" /sys/block/zram0/comp_algorithm; then
    echo lz4 > /sys/block/zram0/comp_algorithm
elif grep -q "zstd" /sys/block/zram0/comp_algorithm; then
    echo zstd > /sys/block/zram0/comp_algorithm
fi

echo "$ZRAM_BYTES" > /sys/block/zram0/disksize

# 4. Format and activate zRAM swap with high priority
echo "[4/5] Formatting and activating /dev/zram0..."
mkswap -L zram0 /dev/zram0 >/dev/null
swapon -p 100 /dev/zram0

# 5. Apply memory management kernel parameters
echo "[5/5] Applying kernel virtual memory parameters..."
cat << 'EOF' > /etc/sysctl.d/99-zram.conf
vm.swappiness = 100
vm.vfs_cache_pressure = 500
vm.dirty_background_ratio = 5
vm.dirty_ratio = 10
EOF

sysctl --system >/dev/null

# Persist as systemd service
SERVICE_PATH="/etc/systemd/system/zram-swap.service"
cat << EOF > "$SERVICE_PATH"
[Unit]
Description=Initialize zRAM Compressed Swap
DefaultDependencies=no
Before=swap.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c "modprobe zram && echo lz4 > /sys/block/zram0/comp_algorithm && echo $ZRAM_BYTES > /sys/block/zram0/disksize && mkswap /dev/zram0 && swapon -p 100 /dev/zram0"
ExecStop=/bin/bash -c "swapoff /dev/zram0 2>/dev/null && echo 1 > /sys/block/zram0/reset"
RemainAfterExit=yes

[Install]
WantedBy=swap.target
EOF

systemctl daemon-reload
systemctl enable zram-swap.service 2>/dev/null || true

echo "=================================================================="
echo "  zRAM ACTIVATION COMPLETE"
echo "=================================================================="
swapon --show
free -h

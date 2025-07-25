Cross-Platform Disk Image Writer
A secure CLI tool for writing disk images (.img/.iso) to USB drives or external storage – Supports Linux and macOS with advanced validation and formatting options.

Key Features
✔ Multi-OS Support: Works on Linux (dd/badblocks) and macOS (diskutil)
✔ Safe Write Mode: Data integrity checks with fsync + oflag=direct
✔ Disk Health Checks: Pre-write verification using badblocks (Linux) or diskutil verify (macOS)
✔ Auto-Unmount & Formatting: Supports FAT32, ExFAT, NTFS, EXT4, HFS+, and APFS
✔ User-Friendly: Interactive prompts for beginners, verbose logging

Use Cases
Create bootable USB drives (Raspberry Pi, Arduino, OS installers)

Clone disks or restore backups

Repair corrupted storage devices

Requirements
Bash 4.0+

Linux (e.g., Ubuntu/Debian) or macOS

sudo/root access (for raw disk operations)

Quick Start
bash
chmod +x disk_writer.sh
sudo ./disk_writer.sh
Warning ⚠️
This tool performs low-level disk operations. Double-check the target device (/dev/sdX or /dev/diskX) to avoid accidental data loss.

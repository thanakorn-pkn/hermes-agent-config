---
name: homebrew-relocate
description: Relocate Homebrew installation to a different partition or directory
domain: devops
---

# Homebrew Relocation Skill

## Overview
This skill provides a procedure for relocating Homebrew installation to a different partition or directory, useful for systems with limited root partition space or when wanting to store packages on a larger data drive.

## When to Use
- When you need to move Homebrew from default location (/home/linuxbrew/.linuxbrew) to a different partition/directory
- When setting up a homelab or development environment with separate data/storage partitions
- When the root partition has limited space but you have a larger data partition available

## Prerequisites
- Homebrew already installed (in default or custom location)
- Target partition/directory available and mounted with sufficient space
- sudo privileges for moving directories and creating symlinks
- Shell profile file to update (~/.bashrc, ~/.zshrc, etc.)

## Procedure

### 1. Verify Current Homebrew Installation
```bash
# Check if brew is available and its location
which brew
brew --version
ls -ld $(brew --prefix)
```

### 2. Prepare Target Location
```bash
# Choose target directory (e.g., /data/linuxbrew)
TARGET_DIR="/data/linuxbrew"

# Ensure target directory exists and has sufficient space
sudo mkdir -p "$TARGET_DIR"
df -h "$TARGET_DIR"  # Check available space
```

### 3. Move Homebrew Installation
```bash
# Get current Homebrew prefix
CURRENT_PREFIX=$(brew --prefix)

# Move the entire Homebrew installation to target location
sudo mv "$CURRENT_PREFIX" "$TARGET_DIR"

# Verify the move was successful
ls -ld "$TARGET_DIR"
ls -ld "$TARGET_DIR"/bin/brew
```

### 4. Create Symlink (Optional but Recommended)
```bash
# Create symlink from original location to new location
# This ensures any scripts or documentation expecting the original path still work
sudo ln -s "$TARGET_DIR" "$CURRENT_PREFIX"

# Verify symlink
ls -ld "$CURRENT_PREFIX"
ls -l "$CURRENT_PREFIX"/bin/brew
```

### 5. Update Shell PATH
```bash
# Determine your shell profile file
PROFILE_FILE="$HOME/.bashrc"  # Default to bash, adjust for zsh, fish, etc.

# Add Homebrew bin to PATH if not already present
if ! grep -q "export PATH.*$TARGET_DIR/bin" "$PROFILE_FILE"; then
    echo 'export PATH="'$TARGET_DIR'/bin:$PATH"' >> "$PROFILE_FILE"
fi

# Reload shell profile
source "$PROFILE_FILE"

# Verify PATH includes new location
echo $PATH | grep "$TARGET_DIR/bin"
```

### 6. Verify Installation Works
```bash
# Check brew version and location
brew --version
which brew
brew --prefix

# Test basic functionality
brew update
brew doctor
```

### 7. Install Packages
```bash
# Install desired packages (example: gcc)
brew install gcc

# Handle any post-install issues if they arise
# (e.g., if postinstall step fails, run: brew postinstall <formula>)

# Verify installed package
which gcc
gcc --version
```

### 8. Troubleshooting Common Issues

#### Symlink Permission Issues
If you encounter "Permission denied" when creating symlink:
```bash
sudo ln -s "$TARGET_DIR" "$CURRENT_PREFIX"
```

#### PATH Not Updated
If brew command not found after relocation:
```bash
# Check current PATH
echo $PATH

# Manually add to current session
export PATH="$TARGET_DIR/bin:$PATH"

# Then permanently add to profile as shown in step 5
```

#### Post-install Script Failures
If a formula's post-install step fails:
```bash
brew postinstall <formula-name>
```

#### Hash Cache Issues
If system still finds old version of commands:
```bash
hash -r  # Clear command hash cache
```

## Verification
After completing the relocation:
1. `brew --version` shows correct version
2. `which brew` points to the symlink or new location
3. `brew --prefix` shows the new target directory
4. Installed packages work correctly (e.g., `gcc --version` shows Homebrew version)
5. `brew doctor` reports no issues

## Maintenance
- To move again in future, repeat the process with new target location
- Periodically run `brew cleanup` to free space
- Monitor target partition space usage with `df -h $TARGET_DIR`

## Notes
- This skill assumes Linux environment (Homebrew on Linux)
- For macOS, the default location is different (/usr/local or /opt/homebrew)
- The symlink approach maintains compatibility with scripts expecting Homebrew in standard location
- Always verify you have sufficient space in target partition before moving
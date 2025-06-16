#!/bin/bash
#
# MIT License
#
# Copyright (c) 2025 laplaque/instana_plugins Contributors
#
# This file is part of the Instana Plugins collection.
#
# Shared Installation Functions
# Generic, vendor-agnostic installation functions with TOML manifest support
#

# Colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Global variables for tracking installation state
INSTALLATION_LOG=""

# Function to log installation steps
log_step() {
    local message="$1"
    local level="${2:-INFO}"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "ERROR")
            echo -e "${RED}[$timestamp] ERROR: $message${NC}"
            ;;
        "WARN")
            echo -e "${YELLOW}[$timestamp] WARN: $message${NC}"
            ;;
        "SUCCESS")
            echo -e "${GREEN}[$timestamp] SUCCESS: $message${NC}"
            ;;
        *)
            echo -e "${BLUE}[$timestamp] INFO: $message${NC}"
            ;;
    esac
    
    INSTALLATION_LOG="${INSTALLATION_LOG}[$timestamp] $level: $message\n"
}

# Simple TOML parser for our specific needs
parse_toml_to_env() {
    local toml_file="$1"
    local prefix="${2:-TOML}"
    
    if [ ! -f "$toml_file" ]; then
        log_step "TOML file not found: $toml_file" "ERROR"
        return 1
    fi
    
    # Use Python to parse TOML since it's more reliable than bash parsing
    python3 << EOF
import sys
import re
import os

def parse_toml_simple(filename, prefix):
    """Simple TOML parser that exports as environment variables"""
    try:
        current_section = None
        
        with open(filename, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                # Section headers [metadata], [installation], etc.
                if line.startswith('[') and line.endswith(']'):
                    # Handle nested sections like [common_files."__init__.py"]
                    section_match = re.match(r'\[([^\]]+)\]', line)
                    if section_match:
                        current_section = section_match.group(1)
                        # Clean up section name for environment variables
                        current_section = current_section.replace('"', '').replace('.', '_').replace('-', '_')
                    continue
                    
                # Key-value pairs
                if '=' in line and current_section:
                    try:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Handle different value types
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]  # Remove quotes
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]  # Remove quotes
                        elif value.lower() in ['true', 'false']:
                            value = value.lower()
                        elif value.startswith('[') and value.endswith(']'):
                            # Handle arrays (simplified - just remove brackets)
                            value = value[1:-1].replace('"', '').replace("'", "")
                        
                        # Create environment variable name
                        var_name = f"{prefix}_{current_section}_{key}".upper()
                        var_name = re.sub(r'[^A-Z0-9_]', '_', var_name)
                        
                        # Escape single quotes in value for bash
                        value = value.replace("'", "'\"'\"'")
                        print(f"export {var_name}='{value}'")
                        
                    except ValueError as e:
                        print(f"echo 'Warning: Could not parse line {line_num}: {line}' >&2", file=sys.stderr)
                        continue
                        
    except Exception as e:
        print(f"echo 'Error parsing TOML: {e}' >&2", file=sys.stderr)
        sys.exit(1)

parse_toml_simple('$toml_file', '$prefix')
EOF
}

# Load plugin metadata from plugin.toml
get_plugin_metadata() {
    local plugin_dir="$1"
    local plugin_toml="${plugin_dir}/plugin.toml"
    
    log_step "Loading plugin metadata from $plugin_dir"
    
    # Check if plugin.toml exists
    if [ -f "$plugin_toml" ]; then
        log_step "Found plugin.toml, loading configuration"
        eval "$(parse_toml_to_env "$plugin_toml" "PLUGIN")"
        
        # Validate required fields
        if [ -z "$PLUGIN_METADATA_PLUGIN_NAME" ] || [ -z "$PLUGIN_METADATA_PROCESS_NAME" ]; then
            log_step "Invalid plugin.toml - missing required metadata fields" "ERROR"
            return 1
        fi
        
        log_step "Plugin: $PLUGIN_METADATA_PLUGIN_NAME ($PLUGIN_METADATA_DESCRIPTION)" "SUCCESS"
        return 0
        
    # Fallback to __init__.py for backward compatibility
    elif [ -f "${plugin_dir}/__init__.py" ]; then
        log_step "No plugin.toml found, falling back to __init__.py" "WARN"
        
        # Extract from Python __init__.py
        eval "$(python3 << EOF
import sys
sys.path.insert(0, '$plugin_dir')
try:
    from . import SERVICE_NAMESPACE, PROCESS_NAME, PLUGIN_NAME
    print(f"export PLUGIN_METADATA_SERVICE_NAMESPACE='{SERVICE_NAMESPACE}'")
    print(f"export PLUGIN_METADATA_PROCESS_NAME='{PROCESS_NAME}'")
    print(f"export PLUGIN_METADATA_PLUGIN_NAME='{PLUGIN_NAME}'")
    print(f"export PLUGIN_METADATA_DESCRIPTION='Legacy {PROCESS_NAME} monitoring'")
except ImportError as e:
    print(f"echo 'Error importing from __init__.py: {e}' >&2", file=sys.stderr)
    exit(1)
EOF
)"
        
        if [ $? -eq 0 ]; then
            log_step "Legacy configuration loaded: $PLUGIN_METADATA_PLUGIN_NAME" "SUCCESS"
            return 0
        fi
    fi
    
    log_step "No valid plugin configuration found in $plugin_dir" "ERROR"
    return 1
}

# Verify common files against manifest checksums
verify_common_files() {
    local common_dir="$1"
    local manifest_file="${common_dir}/manifest.toml"
    local force_update="${2:-false}"
    
    log_step "Verifying common files in $common_dir"
    
    if [ ! -f "$manifest_file" ]; then
        log_step "No manifest found, copying from source"
        return 2  # Indicates manifest missing
    fi
    
    # Load manifest
    eval "$(parse_toml_to_env "$manifest_file" "MANIFEST")"
    
    log_step "Framework: $MANIFEST_METADATA_FRAMEWORK_NAME v$MANIFEST_METADATA_VERSION"
    
    # Get list of required files from manifest
    local required_files=($(python3 << EOF
import re
with open('$manifest_file', 'r') as f:
    content = f.read()
    
# Find all common_files sections
pattern = r'\[common_files\."([^"]+)"\]'
files = re.findall(pattern, content)
for file in files:
    print(file)
EOF
))
    
    local files_ok=0
    local files_missing=0
    local files_mismatch=0
    
    # Check each required file
    for file_name in "${required_files[@]}"; do
        local installed_file="${common_dir}/${file_name}"
        
        # Get expected values from manifest
        local hash_var="MANIFEST_COMMON_FILES_${file_name//[^A-Z0-9]/_}_SHA256"
        local size_var="MANIFEST_COMMON_FILES_${file_name//[^A-Z0-9]/_}_SIZE"
        
        # Dynamically get the values (indirect variable expansion)
        local expected_hash="${!hash_var}"
        local expected_size="${!size_var}"
        
        if [ ! -f "$installed_file" ]; then
            ((files_missing++))
            log_step "  ❌ $file_name: MISSING"
        elif [ -z "$expected_hash" ]; then
            log_step "  ⚠️  $file_name: No checksum in manifest"
        else
            # Calculate actual checksum and size
            local actual_hash=$(sha256sum "$installed_file" 2>/dev/null | cut -d' ' -f1)
            local actual_size=$(stat -f%z "$installed_file" 2>/dev/null || stat -c%s "$installed_file" 2>/dev/null)
            
            if [ "$actual_hash" = "$expected_hash" ] && [ "$actual_size" = "$expected_size" ]; then
                ((files_ok++))
                log_step "  ✅ $file_name: OK"
            else
                ((files_mismatch++))
                log_step "  ⚠️  $file_name: CHECKSUM MISMATCH"
            fi
        fi
    done
    
    # Summary
    log_step "Verification complete: $files_ok OK, $files_missing missing, $files_mismatch mismatched"
    
    if [ $files_missing -gt 0 ] || [ $files_mismatch -gt 0 ]; then
        if [ "$force_update" = "true" ] || [ $files_missing -gt 0 ]; then
            return 1  # Needs installation/update
        else
            log_step "Use --force-update to refresh modified files" "WARN"
            return 1  # Needs update but user choice required
        fi
    fi
    
    return 0  # All good
}

# Install or update common files
install_common_files() {
    local base_dir="$1"
    local parent_dir="$2"
    local force_update="${3:-false}"
    
    local common_dir="${base_dir}/common"
    local source_manifest="${parent_dir}/common/manifest.toml"
    
    log_step "Installing common files to $common_dir"
    
    # Create common directory
    mkdir -p "$common_dir"
    if [ $? -ne 0 ]; then
        log_step "Failed to create directory $common_dir" "ERROR"
        return 1
    fi
    
    # Copy manifest first
    if [ ! -f "${common_dir}/manifest.toml" ] || [ "$force_update" = "true" ]; then
        cp "$source_manifest" "${common_dir}/manifest.toml"
        log_step "Copied manifest to installation directory"
    fi
    
    # Install all common files (simplified approach)
    local updated_count=0
    
    # Get list of files from source directory
    for source_file in "${parent_dir}/common"/*.py "${parent_dir}/common"/*.sh; do
        if [ -f "$source_file" ]; then
            local file_name=$(basename "$source_file")
            local target_file="${common_dir}/${file_name}"
            
            # Skip manifest.toml as it's already copied
            if [ "$file_name" = "manifest.toml" ]; then
                continue
            fi
            
            # Copy if file is missing or force update
            if [ ! -f "$target_file" ] || [ "$force_update" = "true" ]; then
                log_step "Installing/updating: $file_name"
                cp "$source_file" "$target_file"
                
                # Set appropriate permissions
                if [ "${file_name##*.}" = "py" ]; then
                    chmod 644 "$target_file"
                elif [ "${file_name##*.}" = "sh" ]; then
                    chmod 755 "$target_file"
                fi
                
                ((updated_count++))
            fi
        fi
    done
    
    if [ $updated_count -gt 0 ]; then
        log_step "Updated $updated_count common files" "SUCCESS"
    else
        log_step "All common files are up-to-date" "SUCCESS"
    fi
    
    return 0
}

# Install plugin-specific files
install_plugin_files() {
    local plugin_source_dir="$1"
    local plugin_target_dir="$2"
    
    log_step "Installing plugin files from $plugin_source_dir to $plugin_target_dir"
    
    # Create plugin directory
    mkdir -p "$plugin_target_dir"
    if [ $? -ne 0 ]; then
        log_step "Failed to create plugin directory $plugin_target_dir" "ERROR"
        return 1
    fi
    
    # Copy sensor.py
    if [ -f "${plugin_source_dir}/sensor.py" ]; then
        cp "${plugin_source_dir}/sensor.py" "${plugin_target_dir}/sensor.py"
        chmod 755 "${plugin_target_dir}/sensor.py"
        log_step "Installed sensor.py"
    else
        log_step "sensor.py not found in $plugin_source_dir" "ERROR"
        return 1
    fi
    
    # Copy plugin.toml if it exists
    if [ -f "${plugin_source_dir}/plugin.toml" ]; then
        cp "${plugin_source_dir}/plugin.toml" "${plugin_target_dir}/plugin.toml"
        chmod 644 "${plugin_target_dir}/plugin.toml"
        log_step "Installed plugin.toml"
    fi
    
    # Handle __init__.py for backward compatibility
    if [ -f "${plugin_source_dir}/__init__.py" ]; then
        # Copy existing __init__.py if it has content
        if [ -s "${plugin_source_dir}/__init__.py" ]; then
            cp "${plugin_source_dir}/__init__.py" "${plugin_target_dir}/__init__.py"
            chmod 644 "${plugin_target_dir}/__init__.py"
            log_step "Installed existing __init__.py"
        else
            # Generate __init__.py from TOML metadata if source is empty
            cat > "${plugin_target_dir}/__init__.py" << EOF
# Auto-generated from plugin.toml metadata
SERVICE_NAMESPACE = "${PLUGIN_METADATA_SERVICE_NAMESPACE:-Unknown}"
PROCESS_NAME = "${PLUGIN_METADATA_PROCESS_NAME:-Unknown}"
PLUGIN_NAME = "${PLUGIN_METADATA_PLUGIN_NAME:-unknown}"
EOF
            chmod 644 "${plugin_target_dir}/__init__.py"
            log_step "Generated __init__.py from TOML metadata"
        fi
    elif [ ! -f "${plugin_target_dir}/__init__.py" ]; then
        # Generate __init__.py from TOML metadata if none exists
        cat > "${plugin_target_dir}/__init__.py" << EOF
# Auto-generated from plugin.toml metadata
SERVICE_NAMESPACE = "${PLUGIN_METADATA_SERVICE_NAMESPACE:-Unknown}"
PROCESS_NAME = "${PLUGIN_METADATA_PROCESS_NAME:-Unknown}"
PLUGIN_NAME = "${PLUGIN_METADATA_PLUGIN_NAME:-unknown}"
EOF
        chmod 644 "${plugin_target_dir}/__init__.py"
        log_step "Generated __init__.py from TOML metadata"
    fi
    
    log_step "Plugin files installed successfully" "SUCCESS"
    return 0
}

# Create systemd service file
create_service_file() {
    local base_dir="$1"
    local is_root="${2:-false}"
    local force_start="${3:-false}"
    
    # Use plugin metadata for service configuration
    local service_name="instana-${PLUGIN_METADATA_PLUGIN_NAME}-monitor"
    local service_description="Instana ${PLUGIN_METADATA_SERVICE_NAMESPACE} ${PLUGIN_METADATA_PROCESS_NAME} Monitor"
    local plugin_path="${base_dir}/${PLUGIN_METADATA_PLUGIN_NAME}"
    
    log_step "Creating systemd service: $service_name"
    
    if [ "$is_root" = "true" ]; then
        # System-level service
        local service_file="/etc/systemd/system/${service_name}.service"
        
        if [ -f "$service_file" ] && [ "$force_start" != "true" ]; then
            log_step "Service file already exists: $service_file" "WARN"
        else
            log_step "Creating system service file: $service_file"
            
            cat > "$service_file" << EOF
[Unit]
Description=$service_description
After=network.target

[Service]
ExecStart=/usr/bin/python3 ${plugin_path}/sensor.py
Restart=always
User=root
Environment=PYTHONUNBUFFERED=1
Environment="PYTHONPATH=${base_dir}"

[Install]
WantedBy=multi-user.target
EOF
            
            # Enable service
            systemctl daemon-reload
            systemctl enable "${service_name}.service"
            log_step "Service enabled: $service_name" "SUCCESS"
            
            # Start service if requested
            if [ "$force_start" = "true" ]; then
                systemctl start "${service_name}.service"
                log_step "Service started: $service_name" "SUCCESS"
            fi
        fi
    else
        # User-level service
        local user_service_dir="$HOME/.config/systemd/user"
        local user_service_file="$user_service_dir/${service_name}.service"
        
        mkdir -p "$user_service_dir"
        
        log_step "Creating user service file: $user_service_file"
        
        cat > "$user_service_file" << EOF
[Unit]
Description=$service_description (User Service)
After=network.target

[Service]
ExecStart=/usr/bin/python3 ${plugin_path}/sensor.py
Restart=always
Environment=PYTHONUNBUFFERED=1
Environment="PYTHONPATH=${base_dir}"

[Install]
WantedBy=default.target
EOF
        
        log_step "User service created. To enable:" "INFO"
        log_step "  systemctl --user daemon-reload" "INFO"
        log_step "  systemctl --user enable ${service_name}.service" "INFO"
        log_step "  systemctl --user start ${service_name}.service" "INFO"
    fi
}

# Main installation function - orchestrates the entire process
install_plugin() {
    local plugin_dir="$1"
    local base_dir="$2"
    local force_update="${3:-false}"
    local restart_service="${4:-false}"
    
    local parent_dir="$(dirname "$plugin_dir")"
    local is_root="false"
    
    if [ "$EUID" -eq 0 ]; then
        is_root="true"
    fi
    
    log_step "Starting plugin installation" "INFO"
    log_step "Plugin directory: $plugin_dir"
    log_step "Base directory: $base_dir"
    log_step "Force update: $force_update"
    log_step "Root installation: $is_root"
    
    # Step 1: Load plugin metadata
    if ! get_plugin_metadata "$plugin_dir"; then
        log_step "Failed to load plugin metadata" "ERROR"
        return 1
    fi
    
    # Step 2: Install common files
    if ! install_common_files "$base_dir" "$parent_dir" "$force_update"; then
        log_step "Failed to install common files" "ERROR"
        return 1
    fi
    
    # Step 3: Install plugin-specific files
    local plugin_target_dir="${base_dir}/${PLUGIN_METADATA_PLUGIN_NAME}"
    if ! install_plugin_files "$plugin_dir" "$plugin_target_dir"; then
        log_step "Failed to install plugin files" "ERROR"
        return 1
    fi
    
    # Step 4: Create systemd service
    create_service_file "$base_dir" "$is_root" "$restart_service"
    
    # Step 5: Summary
    log_step "Installation completed successfully!" "SUCCESS"
    log_step "Plugin: $PLUGIN_METADATA_PLUGIN_NAME ($PLUGIN_METADATA_DESCRIPTION)"
    log_step "Base directory: $base_dir"
    log_step "Plugin directory: $plugin_target_dir"
    log_step "Common directory: ${base_dir}/common"
    
    # Test command suggestion
    log_step "To test the plugin, run:"
    log_step "  PYTHONPATH=${base_dir} python3 ${plugin_target_dir}/sensor.py --once --log-level=DEBUG"
    
    return 0
}

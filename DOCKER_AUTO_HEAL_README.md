# Docker Auto-Heal Script for Oudience Chatbot

## Overview

This PowerShell automation script provides comprehensive Docker Compose auto-healing for the `kavix28/oudience-chatbot` deployment. It automatically detects and fixes the `ModuleNotFoundError: No module named 'prometheus_client'` issue and ensures a healthy container state.

## Features

### Core Functionality

- ✅ **Automatic compose file detection** - Finds and validates docker-compose.yml
- ✅ **Image tag management** - Updates from v1.0 to v1.2 automatically
- ✅ **Full environment reset** - Cleans volumes, containers, and images
- ✅ **Module verification** - Checks prometheus_client availability
- ✅ **Auto-rebuild capability** - Rebuilds image if dependency missing
- ✅ **Health endpoint testing** - Validates /test/system/health
- ✅ **Detailed status reporting** - Shows running image, health, and dependencies

### Resilience Features

- 🔄 **Retry logic** - Up to 3 retries for pull/push operations
- 🔄 **WSL restart** - Auto-restarts WSL if Docker engine unstable
- 🔄 **Network error handling** - Graceful recovery from interruptions
- 🔄 **Digest verification** - Confirms correct image running
- 🔄 **Multiple compose file handling** - Selects correct file if multiple exist
- 🔄 **Idempotent execution** - Safe to run multiple times

## Prerequisites

- Windows 10/11 with WSL2
- Docker Desktop for Windows
- PowerShell 5.1 or later
- Internet connection (for image pull/push)

## Quick Start

### Basic Usage

```powershell
# Navigate to project directory
cd c:\PROJECTS\Oudience_Clone

# Run the auto-heal script
.\docker-auto-heal.ps1
```

### Advanced Usage

```powershell
# Skip WSL restart even if Docker engine is unstable
.\docker-auto-heal.ps1 -SkipWSLRestart

# Customize maximum retry attempts (default: 3)
.\docker-auto-heal.ps1 -MaxRetries 5

# Combine parameters
.\docker-auto-heal.ps1 -SkipWSLRestart -MaxRetries 5
```

## Execution Flow

The script follows this sequential process:

### Step 1: Detect Docker Compose File

- Searches for docker-compose.yml, docker-compose.yaml, compose.yml, compose.yaml
- Handles multiple compose files by selecting primary
- Validates file existence

### Step 2: Check and Update Image Tag

- Parses current image tag from compose file
- Compares with target tag (v1.2)
- Creates backup before modification
- Updates tag if mismatch detected

### Step 3: Validate Docker Environment

- Checks Docker engine status
- Verifies Docker Compose availability
- Auto-restarts WSL if engine unresponsive (unless -SkipWSLRestart)

### Step 4: Full Reset

- Stops all containers
- Removes volumes
- Removes images
- Ensures clean slate

### Step 5: Pull Correct Image

- Pulls updated image with retry logic
- Handles network interruptions
- Retries up to MaxRetries times

### Step 6: Start Container

- Starts container in detached mode
- Waits for stabilization (10 seconds)

### Step 7: Inspect Running Image

- Retrieves running image information
- Shows image ID and digest
- Validates correct image running

### Step 8: Verify prometheus_client Module

- Executes Python import test inside container
- Checks if prometheus_client is available

### Step 9: Rebuild if Module Missing _(Conditional)_

- **Only runs if Step 8 fails**
- Stops container
- Verifies/updates requirements.txt
- Rebuilds image with --no-cache as v1.3
- Pushes to registry with retry logic
- Updates compose file to v1.3
- Pulls and restarts with new image

### Step 10: Health Check

- Tests http://localhost:5001/test/system/health
- Waits 20 seconds for app startup
- Shows response body
- Displays container logs if failed

### Step 11: Final Status Report

- Running image tag
- Container status
- Health status
- Dependency check result (prometheus_client)
- Image digest
- Overall deployment status

## Output Examples

### Successful Deployment

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║       Docker Compose Auto-Heal Script                        ║
║       Oudience Chatbot Deployment                            ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝


===> Step 1: Detecting Docker Compose File
ℹ Found: docker-compose.yml
✓ Using compose file: docker-compose.yml

===> Step 2: Checking and Updating Image Tag
ℹ Current image tag: v1.0
⚠ Tag mismatch: v1.0 ≠ v1.2
ℹ Updating to v1.2...
ℹ Backup created: docker-compose.yml.backup_20260218_041906
✓ Image tag updated to v1.2

...

===> Final Status Report

┌─────────────────────────────────────────────────────────────┐
│  RUNNING IMAGE TAG:  kavix28/oudience-chatbot:v1.2         │
│  CONTAINER STATUS:   running                                │
│  HEALTH STATUS:      healthy                                │
│  DEPENDENCY CHECK:   ✓ PASSED                               │
│  IMAGE DIGEST:       sha256:abc123...                       │
└─────────────────────────────────────────────────────────────┘

🎉 DEPLOYMENT SUCCESSFUL - All checks passed!

⏱️  Total execution time: 45.32 seconds
```

### Rebuild Scenario

If prometheus_client is missing, the script automatically:

```
===> Step 8: Verifying prometheus_client Module
ℹ Executing module check inside container...
✗ Module check failed: ModuleNotFoundError: No module named 'prometheus_client'

===> Step 9: Rebuilding Image (Module Missing)
ℹ Stopping container...
ℹ Verifying requirements.txt...
✓ requirements.txt already contains prometheus-client
ℹ Building image kavix28/oudience-chatbot:v1.3 with --no-cache...
✓ Image rebuilt successfully
ℹ Pushing kavix28/oudience-chatbot:v1.3 to registry...
✓ Image pushed successfully
ℹ Updating compose file to use v1.3...
✓ Compose file updated to v1.3
✓ Container restarted with v1.3 image
```

## Error Handling

The script handles various error scenarios:

### Docker Engine Unresponsive

- Auto-restarts WSL (unless -SkipWSLRestart)
- Retries Docker operations after restart

### Network Interruptions

- Retries pull/push operations (up to MaxRetries)
- Shows clear error messages
- Continues with partial success when possible

### Missing Files

- Checks for Dockerfile before rebuild
- Validates compose file existence
- Creates backups before modifications

### Container Issues

- Shows container logs on health check failure
- Provides detailed error messages
- Returns appropriate exit codes

## Exit Codes

- `0` - Successful deployment with all checks passed
- `1` - Deployment failed or completed with warnings

## File Backups

The script automatically creates backups when modifying files:

```
docker-compose.yml.backup_20260218_041906
```

Backups use timestamp format: `yyyyMMdd_HHmmss`

## Troubleshooting

### Script Execution Policy Error

If you get "script execution is disabled on this system":

```powershell
# Set execution policy for current session
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# Then run the script
.\docker-auto-heal.ps1
```

### Docker Desktop Not Running

Ensure Docker Desktop is running:

1. Start Docker Desktop from Windows Start Menu
2. Wait for "Docker Desktop is running" notification
3. Run the script again

### WSL Issues

If WSL restart fails:

```powershell
# Manually restart WSL
wsl --shutdown

# Wait 5 seconds, then run script
.\docker-auto-heal.ps1
```

### Permission Issues

Run PowerShell as Administrator:

1. Right-click PowerShell
2. Select "Run as Administrator"
3. Navigate to project directory
4. Run script

## Integration with CI/CD

The script can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Auto-heal Docker deployment
  shell: pwsh
  run: |
    cd c:\PROJECTS\Oudience_Clone
    .\docker-auto-heal.ps1 -MaxRetries 5
```

## Customization

### Modify Target Image Tag

Edit the script variable (line ~27):

```powershell
$script:TargetImageTag = "v1.2"  # Change to desired tag
```

### Adjust Health Check Timeout

Edit the sleep duration in `Test-HealthEndpoint` function (line ~363):

```powershell
Start-Sleep -Seconds 20  # Change to desired wait time
```

### Change Container Name

Edit the container name variable (line ~25):

```powershell
$script:ContainerName = "oudience_chatbot_prod"  # Change to your container name
```

## Maintenance

### Logs Collection

The script shows container logs automatically on failure. To manually view logs:

```powershell
docker logs oudience_chatbot_prod

# Follow logs in real-time
docker logs -f oudience_chatbot_prod
```

### Manual Cleanup

If you need to manually clean up:

```powershell
docker compose down --volumes --rmi all
```

## Support

For issues or questions:

1. Check container logs: `docker logs oudience_chatbot_prod`
2. Review script output for specific error messages
3. Verify Docker Desktop is running and updated
4. Check WSL2 is properly configured

## Version History

- **v1.0** - Initial release with core auto-heal functionality
- Comprehensive error handling
- WSL restart capability
- Network retry logic
- Digest verification
- Multi-compose file support

## License

This script is provided as-is for use with the Oudience Chatbot project.

# 🚀 Quick Start Guide - Docker Auto-Heal Script

## ⏱️ 30-Second Setup

```powershell
# 1. Navigate to project
cd c:\PROJECTS\Oudience_Clone

# 2. Run the script
.\docker-auto-heal.ps1
```

That's it! The script handles everything automatically.

---

## 📋 What the Script Does

✅ Detects your docker-compose.yml file  
✅ Updates image tag from v1.0 → v1.2  
✅ Performs full reset (removes containers, volumes, images)  
✅ Pulls the correct image  
✅ Starts the container  
✅ Verifies prometheus_client module  
✅ Auto-rebuilds if dependency missing  
✅ Tests health endpoint  
✅ Shows final status report

---

## 🎯 Expected Output

### ✨ Success

```
🎉 DEPLOYMENT SUCCESSFUL - All checks passed!
⏱️  Total execution time: 45.32 seconds
```

### ⚙️ With Rebuild

If prometheus_client is missing, the script will:

1. Rebuild image as v1.3
2. Push to registry
3. Update compose file
4. Restart container

Total time: ~2-3 minutes

---

## ❌ Troubleshooting

### "Execution of scripts is disabled"

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\docker-auto-heal.ps1
```

### Docker Desktop Not Running

1. Start Docker Desktop
2. Wait for it to fully start
3. Run script again

### Still Having Issues?

```powershell
# Run with verbose output (check script logs)
.\docker-auto-heal.ps1 -Verbose

# Skip WSL restart
.\docker-auto-heal.ps1 -SkipWSLRestart

# Increase retries
.\docker-auto-heal.ps1 -MaxRetries 5
```

---

## 📊 Final Status Report

The script shows:

- ✅ Running image tag
- ✅ Container status
- ✅ Health status
- ✅ Dependency check (prometheus_client)
- ✅ Image digest

---

## 🔧 Advanced Options

```powershell
# Skip WSL restart
.\docker-auto-heal.ps1 -SkipWSLRestart

# More retries for flaky networks
.\docker-auto-heal.ps1 -MaxRetries 5

# Combine options
.\docker-auto-heal.ps1 -SkipWSLRestart -MaxRetries 5
```

---

## 📚 Full Documentation

For detailed information, see: [DOCKER_AUTO_HEAL_README.md](./DOCKER_AUTO_HEAL_README.md)

---

## ✅ Verification Commands

After script completes, verify manually:

```powershell
# Check container is running
docker ps | Select-String "oudience_chatbot_prod"

# Check health
curl http://localhost:5001/test/system/health

# Verify module
docker exec oudience_chatbot_prod python -c "import prometheus_client; print('OK')"

# View logs
docker logs oudience_chatbot_prod --tail 50
```

---

## 🔄 Safe to Run Multiple Times

The script is **idempotent** - you can run it as many times as needed without causing issues.

---

**Need Help?** Check the full README: `DOCKER_AUTO_HEAL_README.md`

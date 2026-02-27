# Oudience Chatbot — Enterprise Deployment Guide

Production deployment documentation for `kavix28/oudience-chatbot`.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Host                              │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  oudience_chatbot_prod                                    │  │
│  │                                                           │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐   │  │
│  │  │ Gunicorn  │→ │ Flask    │→ │ RAG Pipeline         │   │  │
│  │  │ 2w × 4t   │  │ App      │  │ SentenceTransformer  │   │  │
│  │  └──────────┘  └──────────┘  │ DistilBERT QA        │   │  │
│  │       ↑                       └──────────────────────┘   │  │
│  │  :5001 (mapped)                                          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Volumes:                                                       │
│    oudience_data        → /app/data                             │
│    oudience_sessions    → /app/flask_sessions                   │
│    oudience_uploads     → /app/uploads                          │
│    oudience_model_cache → /app/model_cache                      │
└─────────────────────────────────────────────────────────────────┘
```

### Image Build Stages

| Stage    | Base                      | Purpose             | Contents                   |
| -------- | ------------------------- | ------------------- | -------------------------- |
| `deps`   | python:3.10-slim-bookworm | Compile Python deps | venv with all pip packages |
| `models` | deps                      | Download ML models  | HuggingFace model cache    |
| `final`  | python:3.10-slim-bookworm | Runtime             | App code + venv + models   |

---

## Quick Start

### Production (pre-built image)

```powershell
docker compose -f docker-compose.prod.yml up -d
```

### Development (local build + hot-reload)

```powershell
docker compose -f docker-compose.dev.yml up --build
```

### Auto-heal (diagnose + fix + verify)

```powershell
.\docker-auto-heal.ps1
```

---

## Versioning Strategy

### Semantic Tags

| Format             | Meaning               | Example       |
| ------------------ | --------------------- | ------------- |
| `v{major}.{minor}` | Release tag           | `v1.2`        |
| `sha-{7chars}`     | Commit build          | `sha-a1b2c3d` |
| `latest`           | Most recent main push | Always exists |

### How Versions Are Created

1. **On push to main** → CI builds and tags as `latest` + `sha-{commit}`
2. **On git tag** → CI builds and tags as `latest` + `v{X.Y}`
3. **On auto-heal rebuild** → Script increments minor: `v1.2` → `v1.3`

### Creating a Release

```bash
git tag v1.3
git push origin v1.3
# CI automatically builds, pushes, and generates digest-locked manifest
```

### Digest-Locked Deployment

CI generates a `deploy-manifest.yml` artifact using the exact image digest:

```yaml
image: kavix28/oudience-chatbot@sha256:abc123...
```

This ensures the exact bytes that were tested are what runs in production.

---

## Compose Files

| File                      | Purpose                | Command                                               |
| ------------------------- | ---------------------- | ----------------------------------------------------- |
| `docker-compose.yml`      | Default (simple)       | `docker compose up -d`                                |
| `docker-compose.prod.yml` | Production with limits | `docker compose -f docker-compose.prod.yml up -d`     |
| `docker-compose.dev.yml`  | Dev with bind-mount    | `docker compose -f docker-compose.dev.yml up --build` |

### Production Features

- CPU limit: 2 cores, Memory: 4GB
- Log rotation: 5 files × 10MB
- Security: `no-new-privileges`
- Healthcheck: 90s start period for model loading
- Restart: `unless-stopped`

### Dev Features

- Bind-mount for live code editing
- No resource limits
- Debug environment enabled
- Local Dockerfile build

---

## Auto-Heal Script

The `docker-auto-heal.ps1` script runs 3 phases automatically:

| Phase                         | What It Does                                                                |
| ----------------------------- | --------------------------------------------------------------------------- |
| **1 — Image Validation**      | Detect compose file, check/update tag, validate config, pull, verify digest |
| **2 — Dependency Validation** | Start container, test `import prometheus_client`, rebuild if missing        |
| **3 — Health Verification**   | Curl health endpoint, detect restart loops, verify port, print status table |

### Parameters

```powershell
.\docker-auto-heal.ps1                          # defaults
.\docker-auto-heal.ps1 -TargetTag v1.3          # specific version
.\docker-auto-heal.ps1 -MaxRetries 5            # more retries
.\docker-auto-heal.ps1 -SkipWSLRestart          # don't restart WSL
.\docker-auto-heal.ps1 -ComposeFile docker-compose.prod.yml  # specific file
```

---

## CI/CD Pipeline

### Workflow: `ci.yml`

```
push/PR to main
   │
   ├── lint (flake8)
   │      │
   ├── dependency-test (import all critical modules)
   │      │
   ├── build-and-push (Docker image → Docker Hub)
   │      │ tagged: latest + version
   │      │
   └── deploy-artifact (digest-locked manifest)
          └── uploaded as GitHub Actions artifact
```

### Required GitHub Secrets

| Secret            | Description             |
| ----------------- | ----------------------- |
| `DOCKER_USERNAME` | Docker Hub username     |
| `DOCKER_PASSWORD` | Docker Hub access token |

### Workflow: `rollback.yml`

Manual dispatch: Actions → Rollback → enter version → generates pinned manifest.

---

## Secrets Best Practices

1. **Never commit `.env`** — it's in `.gitignore`
2. **Rotate `SECRET_KEY`** before production
3. **Change `ADMIN_PASSWORD_HASH`** from the default
4. **Use Docker secrets** for enterprise:
   ```yaml
   secrets:
     app_key:
       file: ./secret_key.txt
   ```
5. **CI secrets** → GitHub Settings → Secrets → Actions

---

## Troubleshooting Checklist

### Container Won't Start

- [ ] Docker Desktop is running
- [ ] `.env` file exists (copy from `.env.example`)
- [ ] Port 5001 is not used by another process: `netstat -ano | findstr 5001`
- [ ] Check logs: `docker logs oudience_chatbot_prod --tail 50`

### ModuleNotFoundError

- [ ] `requirements.txt` contains `prometheus-client`
- [ ] Image was built AFTER adding the dependency
- [ ] Run `docker-auto-heal.ps1` — it auto-fixes this

### Health Check Failing

- [ ] Wait 90 seconds after start (model loading)
- [ ] Test manually: `curl http://localhost:5001/test/system/health`
- [ ] Check logs for startup errors

### Image Pull Fails

- [ ] Internet connectivity: `ping docker.io`
- [ ] Docker Hub rate limit: check `docker pull` output
- [ ] WSL network issue: `wsl --shutdown` then retry

### WSL / Docker Engine Issues

- [ ] Restart WSL: `wsl --shutdown`
- [ ] Restart Docker Desktop
- [ ] Check Windows Hyper-V is enabled
- [ ] Run `docker info` to verify engine

---

## Final Deployment Commands

### Fresh Production Deployment

```powershell
cd c:\PROJECTS\Oudience_Clone

# 1. Copy environment file
Copy-Item .env.example .env
# Edit .env with your secrets

# 2. Deploy
docker compose -f docker-compose.prod.yml up -d

# 3. Verify
docker ps
curl http://localhost:5001/test/system/health
```

### Full Reset + Redeploy

```powershell
docker compose -f docker-compose.prod.yml down --volumes --rmi all
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

### Automated (recommended)

```powershell
.\docker-auto-heal.ps1 -ComposeFile docker-compose.prod.yml
```

---

## Files Reference

| File                             | Purpose                                               |
| -------------------------------- | ----------------------------------------------------- |
| `Dockerfile`                     | Multi-stage optimized build (deps → models → runtime) |
| `.dockerignore`                  | Excludes secrets, docs, runtime data from build       |
| `docker-compose.yml`             | Default simple compose                                |
| `docker-compose.prod.yml`        | Production with resource limits + security            |
| `docker-compose.dev.yml`         | Development with bind-mount                           |
| `docker-auto-heal.ps1`           | Self-healing deployment script                        |
| `.github/workflows/ci.yml`       | CI/CD pipeline with versioning                        |
| `.github/workflows/rollback.yml` | Manual rollback workflow                              |
| `.env.example`                   | Environment variable template                         |
| `DEPLOYMENT.md`                  | This document                                         |

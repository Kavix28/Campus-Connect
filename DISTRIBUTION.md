# Enterprise Distribution Guide

## 🚀 Quick Start (Production)

This package contains the fully dockerized Oudience AI Chatbot.
No local Python or AI setup is required.

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running.

### How to Run

1. **Clone/Download** this repository.
2. Open a terminal in the folder.
3. Run the start script:

**Linux/Mac:**

```bash
chmod +x run.sh
./run.sh
```

**Windows (PowerShell):**

```powershell
docker compose up -d
```

_(Ensure Docker Desktop is running first)_

The application will be available at: **http://localhost:5001**

---

## 🛠 Builder Instructions (For Developers)

If you made code changes and want to update the distribution image:

### 1. Build the Image

This process will:

- Install all dependencies
- **Download and cache** the AI models (approx 1GB) inside the image
- Optimize layers

```bash
docker build -t oudience-chatbot:latest .
```

### 2. Run Locally to Test

```bash
docker compose up
```

### 3. Push to Docker Hub (Distribution)

```bash
# Tag the image
docker tag oudience-chatbot:latest yourusername/oudience-chatbot:v1.0

# Push
docker push yourusername/oudience-chatbot:v1.0
```

---

## 🔒 Security Notes

- The `.env` file is auto-generated on first run with a random `SECRET_KEY`.
- The application runs as a non-root user (`appuser`) inside the container.
- Models are loaded from the bake-in cache, no external downloads at runtime.

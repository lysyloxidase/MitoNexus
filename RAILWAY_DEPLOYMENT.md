# 🚀 Wdrażanie MitoNexus na Railway.app

## Kroki do deploymentu:

### 1. Utwórz konto na Railway
- Idź na https://railway.app
- Zaloguj się za pomocą GitHub (lysyloxidase)
- Utwórz nowy projekt

### 2. Przygotuj repozytorium
```bash
cd ~/MitoNexus
git add .
git commit -m "Add Railway deployment config"
git push origin main
```

### 3. Utwórz projekt Railway (opcja A - GitHub Connect)
- W Railway kliknij "New Project"
- Wybierz "GitHub Repo"
- Połącz lysyloxidase/MitoNexus
- Railway automatycznie wykryje Dockerfile

### 4. Utwórz projekt Railway (opcja B - CLI)
```bash
# Instaluj Railway CLI
npm install -g @railway/cli

# Zaloguj się
railway login

# Utwórz projekt
railway init

# Deploy
railway up
```

### 5. Dodaj usługi pomocnicze
W Railway dashboard:
- Dodaj **PostgreSQL** (kliknij + Plugins → PostgreSQL)
- Dodaj **Redis** (kliknij + Plugins → Redis)
- Railway automatycznie ustawi zmienne: `DATABASE_URL`, `REDIS_URL`

### 6. Skonfiguruj zmienne środowiskowe
W Railway dashboard → Variables:
```
MITONEXUS_ENVIRONMENT=production
MITONEXUS_DEBUG=false
MITONEXUS_CORS_ORIGINS=["https://*.railway.app"]
MITONEXUS_FRONTEND_URL=https://mitonexus-frontend.railway.app
```

### 7. Deploy backendów
**Backend API:**
- W Railway utwórz serwis z Dockerfile
- Dockerfile: `apps/backend/Dockerfile`
- Port: 8000
- Command: `uvicorn mitonexus.main:app --host 0.0.0.0 --port $PORT`

**Celery Worker:**
- Utwórz drugi serwis (kopię)
- Dockerfile: `apps/backend/Dockerfile`
- Command: `celery -A mitonexus.tasks worker --pool=threads --loglevel=info`
- Brak portu (background task)

**Celery Beat:**
- Trzeci serwis
- Command: `celery -A mitonexus.tasks beat --loglevel=info`

### 8. Deploy frontendu (Next.js)
W Railway:
- Utwórz nowy serwis
- Build command: `pnpm install && pnpm --filter @mitonexus/frontend build`
- Start command: `pnpm --filter @mitonexus/frontend start`
- Port: 3000

### 9. Migruj bazę danych
Po deploymencie:
```bash
railway run "uvicorn mitonexus.main:app --host 0.0.0.0 --port 8000"
# W innym oknie:
railway exec "alembic upgrade head"
```

### 10. Sprawdź deployment
- Backend: `https://mitonexus-backend.railway.app/docs`
- Frontend: `https://mitonexus-frontend.railway.app`

## Koszt
- **Free tier** Railway: $5 kredytu/miesiąc
- PostgreSQL: Darmowa baza do 1GB
- Redis: Darmowe do 1GB
- **Total: Zupełnie darmowe** na start

## Wsparcie GPU (opcjonalne)
Jeśli chcesz GPU dla Ollama:
1. Railway nie oferuje GPU na free tier
2. Alternatywa: Hugging Face Spaces, Google Colab, czy własny serwer z GPU

## Troubleshooting
- Sprawdzaj logi: `railway logs`
- Restart: `railway restart`
- SSH: `railway shell`

## Następne kroki
1. Utwórz konto Railway
2. Podepnij GitHub
3. Deploy backend + Celery
4. Deploy frontend
5. Uruchom migracje
6. Testuj na https://yourdomain.railway.app

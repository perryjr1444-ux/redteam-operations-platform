[8m# 🚀 START HERE - Quick Launch Guide

## Fastest Way to Start (Development Mode)

```bash
cd /opt/projects/redteam_py_app

# Run the development server script
./dev_server.sh
```

Then open your browser to: **http://localhost:5172**

## What Happens

✅ Server starts in DEVELOPMENT mode (no SECRET_KEY required)
✅ SQLite database created automatically
✅ Server runs on http://0.0.0.0:5172
✅ Auto-reloads when you edit code

## First Time Setup

1. **Register a user**: http://localhost:5172/register
2. **Login**: http://localhost:5172/login
3. **Start using the app!**

## URLs

- Main Dashboard: http://localhost:5172/
- Login Page: http://localhost:5172/login
- Register: http://localhost:5172/register
- API Docs: http://localhost:5172/api/docs
- Health Check: http://localhost:5172/api/health

## Still Can't Connect?

Try manual start:

```bash
export ENVIRONMENT=development
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 5172
```

If you get errors about missing packages:

```bash
pip3 install -r requirements.txt
```

## Production Deployment

See **PRODUCTION_DEPLOYMENT.md** for full production setup instructions.
[0m
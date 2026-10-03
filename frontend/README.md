# Placify Frontend

React and Vite dashboard for the Placify FastAPI backend.

## Run locally

Start the backend at `http://127.0.0.1:8000`, then run these commands from this directory:

```powershell
npm install
npm run dev
```

Open the local URL printed by Vite, usually `http://127.0.0.1:5173`.

Vite proxies requests from `/api` to the existing backend. The dashboard only requests a student's progress after **Load progress** is submitted; it does not call AI endpoints automatically.

## Checks

```powershell
npm run lint
npm run build
```
# My Food Journal

A full-stack AI-powered food journal that automatically identifies food from photos using Google Gemini Vision API.

**Live Demo:** https://food-recognition-app-7rtx.onrender.com
![Login screen](screenshots/login.png)
![Main app](screenshots/mainPage.png)
---

## Features

- Upload a food photo — Gemini Vision AI identifies it automatically
- JWT authentication — register, login, private entries per user
- Search your food journal in real time
- Paginated food entries with timestamps
- Delete entries with ownership enforcement (can't delete other users' entries)
- File type validation on uploads

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, SQLModel, SQLite |
| Auth | JWT (python-jose), bcrypt password hashing |
| Frontend | Vanilla JavaScript, Tailwind CSS |
| AI | Google Gemini Vision API |
| Deployment | Render |

## Running Locally

```bash
git clone https://github.com/Sangha0822/food-recognition-app
cd food-recognition-app
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:
```
SECRET_KEY=your-secret-key
GEMINI_API_KEY=your-gemini-api-key
```

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`

## Running Tests

```bash
pytest tests/test_main.py -v
```

## Known Limitations

- Uploaded images are not persistent on Render's free tier (wiped on redeploy) — AWS S3 integration planned
- SQLite database is ephemeral on free hosting — PostgreSQL migration planned

## Roadmap

- [ ] AWS S3 for persistent image storage
- [ ] PostgreSQL for persistent database
- [ ] Daily calendar view for food log
- [ ] Custom food recognition model (PyTorch, MIT Food-101 dataset)
- [ ] Calorie estimation per entry

# Food Recognition and Tracking App

A full-stack AI-powered food journal that automatically identifies food from photos 
and logs them to a personal database.

## The Story
Built during military service to maintain engineering discipline and prepare for a 
career in ML and SWE. Started with zero API or database experience — learned by 
building, debugging, and iterating on a real working product.

## Live Features
- 📸 Upload a food photo → AI automatically identifies it using Gemini Vision API
- 🔍 Search your food journal in real time
- 🗂️ Paginated food entries with image display
- 🕐 Automatic timestamp logging for every entry
- 🗑️ Delete entries with automatic image cleanup

## Tech Stack
- **Backend:** Python, FastAPI, SQLModel (SQLite)
- **Frontend:** JavaScript (Vanilla), Tailwind CSS
- **AI:** Google Gemini Vision API for food recognition
- **Infrastructure:** REST API, CORS, UUID file management, multipart form handling

## What I Learned
- Designing and consuming REST APIs from scratch
- Database modeling with SQLModel and SQLite
- Connecting a decoupled frontend to a backend via fetch()
- Integrating third-party AI vision APIs
- Environment variable management and API key security
- Git workflow with issues, commit history, and proper .gitignore

## Roadmap
- [ ] JWT User Authentication (login/signup)
- [ ] AWS S3 for cloud image storage
- [ ] Load More pagination on frontend
- [ ] Train custom food recognition model on MIT Food-101 dataset (PyTorch)
- [ ] Calorie estimation per food entry
- [ ] Loading spinner for upload UX
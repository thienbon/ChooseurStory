# Choose Your Own Adventure Game Intergrate AI

An interactive, AI-powered choose your own adventure game that creates dynamic, personalized narratives using artificial intelligence to generate unique storytelling experiences.

# Installing

1. Clone the repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your API keys(Freepik,Gemini):
```bash
cp .env.example .env
```
4. Run the application:
```bash
python main.py
```

## Configuration

Create a `.env` file in the root directory with the following variables:

```env
GOOGLE_API_KEY=.....
FREEPIK_API_KEY=....

# Backend API config
API_PREFIX=/api
ALLOWED_ORIGINS=http://localhost:5173

# Use a direct URL; this is the simplest path for the current Settings class
DEBUG=True
DATABASE_URL=postgresql://dbadmin:....
```

---


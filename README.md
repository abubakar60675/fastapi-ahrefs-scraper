# 🕸️ FastAPI Ahrefs Domain Scraper

> ⚠️ **Disclaimer**: This project is intended for **educational and learning purposes only**.

This project is a FastAPI-based web API that scrapes **Ahrefs** traffic and domain rating (DR) information using [Botasaurus](https://github.com/omkarcloud/botasaurus). It simulates human-like behavior using human-like cursor movements and Cloudflare bypassing.

---

## 🚀 Features

- Scrapes **traffic** and **domain rating** from Ahrefs.
- Human-like browser automation with Botasaurus.
- Async-friendly with FastAPI and thread isolation.
- CORS enabled for frontend integration.
- Swagger docs auto-generated at `/docs`.

---

## 🧠 Tech Stack

- [FastAPI](https://fastapi.tiangolo.com/)
- [Botasaurus](https://github.com/omkarcloud/botasaurus)
- [Uvicorn](https://www.uvicorn.org/) (ASGI server)

---

## 🛠️ Installation

> ⚠️ Requires Python 3.8+

```bash
# 1. Clone the repository
git clone https://github.com/abubakar60675/fastapi-ahrefs-scraper
.git
cd fastapi-ahrefs-scraper


# 2. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows

# 3. Install dependencies
pip install -r requirements.txt
```

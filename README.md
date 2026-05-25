# AI Podcast Summarizer

A beginner-friendly FastAPI web app that accepts a YouTube podcast URL,
retrieves its English captions, asks OpenAI for a useful report, displays the
result on one webpage, and saves it as a text file.

## Folder Structure

```text
Podcast/
|-- app/
|   |-- __init__.py
|   |-- main.py
|   `-- static/
|       `-- index.html
|-- outputs/
|   `-- .gitkeep
|-- .env.example
|-- .gitignore
|-- requirements.txt
`-- README.md
```

## What Each File Does

| File | Purpose |
| --- | --- |
| `app/main.py` | FastAPI backend: serves the webpage, extracts a video ID, retrieves captions, calls OpenAI, and saves reports. |
| `app/static/index.html` | The only frontend file. It contains the page layout, CSS styling, and small JavaScript form handler. |
| `app/__init__.py` | Makes `app` an importable Python package. |
| `outputs/.gitkeep` | Keeps the empty report folder in the project before reports are generated. |
| `.env.example` | Safe example of the required local settings. Never put a real API key here. |
| `.gitignore` | Keeps secrets, generated reports, and local Python files out of Git. |
| `requirements.txt` | Lists the Python packages used by the app. |
| `render.yaml` | Configures one free Render Python web service without Docker. |

## Dependencies

| Package | Why It Is Used |
| --- | --- |
| `fastapi` | Creates the web server and API routes. |
| `uvicorn[standard]` | Runs the FastAPI application locally. |
| `openai` | Sends transcript text to the Responses API. |
| `youtube-transcript-api` | Fetches available YouTube captions. |
| `python-dotenv` | Loads the private API key from `.env`. |

## Installation

Run these commands in Terminal:

```bash
cd /Users/Pulas/Documents/Podcast
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
open -e .env
```

In `.env`, replace only the placeholder with a real API key:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_QUICK_MODEL=gpt-5-nano
OPENAI_DEEP_MODEL=gpt-5.4-mini
```

Keep `.env` private. Never place a real API key in `README.md`, source code,
screenshots, or chat.

## Run The App

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

Open the webpage:

```text
http://127.0.0.1:8000
```

FastAPI API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## Frontend

The entire frontend lives in `app/static/index.html`:

- Plain HTML gives the page its URL form, report-style choice, optional focus
  question, instructions, and report area.
- Inline CSS provides a clean responsive layout without a build process.
- Plain JavaScript sends the URL to FastAPI and renders the returned report.
- Returned analysis is added through `textContent`, so model output is handled
  as text rather than executable HTML.

There is no React, frontend framework, templating engine, or CSS dependency.

## How Frontend Connects To Backend

1. A browser visits `/`; FastAPI returns `app/static/index.html`.
2. The user pastes a YouTube URL and submits the form.
3. The user chooses a quick or deep report and can provide an optional
   question they particularly care about.
4. JavaScript calls `fetch("/summarize")` with JSON:

```json
{
  "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID_HERE",
  "report_mode": "quick",
  "focus": "Which opportunity is most realistic?"
}
```

5. FastAPI retrieves the transcript and requests a structured report from
   OpenAI.
6. FastAPI saves the report under `outputs/` and returns JSON containing
   `analysis` and `saved_to`.
7. JavaScript turns the returned headings and bullets into readable report
   cards on the same page.

## Report Quality And Cost

The app offers two simple modes:

| Mode | Default model | Use it for |
| --- | --- | --- |
| Quick scan | `gpt-5-nano` | Fast, low-credit summaries and first looks. |
| Deep analysis | `gpt-5.4-mini` | Better synthesis when a video is worth studying. |

Quick reports use minimal reasoning, low verbosity, and a 1000-token output
limit. Deep reports use more room for stronger synthesis. Longer video
transcripts still consume more input tokens than shorter videos.

Every report asks for:

- An episode overview and main themes
- Supported insights rather than promotional claims stated as fact
- Startup opportunities with customer, MVP, and validation risk
- Action steps
- Important claims or assumptions to verify independently

## Beginner Notes

- Not every YouTube video provides English captions.
- `youtube-transcript-api` retrieves captions; it does not transcribe audio.
- Each successful OpenAI summary uses API credits.
- The backend is intentionally kept in one Python file and the frontend in one
  HTML file, so the full project remains easy to follow.

## Deploy Free On Render

This project includes `render.yaml`, so Render can read the correct service
settings from the GitHub repository. No Dockerfile is needed.

### 1. Put The Project On GitHub

Your `.env` file is ignored by Git and must stay local. The real API key is
added separately in Render.

Create a new empty GitHub repository named `ai-podcast-summarizer`. Do not add
a README, `.gitignore`, or license from GitHub because this project already has
its files. Then run:

```bash
cd /Users/Pulas/Documents/Podcast
git add .env.example .gitignore README.md app outputs/.gitkeep requirements.txt render.yaml
git commit -m "Prepare podcast summarizer for Render deployment"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/ai-podcast-summarizer.git
git push -u origin main
```

Replace `YOUR_GITHUB_USERNAME` with your GitHub username.

### 2. Connect GitHub To Render

1. Sign in at [Render](https://dashboard.render.com/).
2. Click **New** and choose **Blueprint**.
3. Connect your GitHub account if Render asks for permission.
4. Select the `ai-podcast-summarizer` GitHub repository.
5. Render finds `render.yaml` and prepares one web service.
6. When Render prompts for `OPENAI_API_KEY`, paste your current API key into
   Render's secret field. Do not put it into GitHub or `render.yaml`.
7. Apply the Blueprint and wait for the deployment to finish.

### Exact Render Settings

These settings are already defined in `render.yaml`:

| Render Setting | Value |
| --- | --- |
| Service type | Web Service |
| Runtime | Python |
| Instance type | Free |
| Build command | `pip install -r requirements.txt` |
| Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health check path | `/health` |

Environment variables:

| Variable | Value |
| --- | --- |
| `OPENAI_API_KEY` | Add securely in Render; never commit it. |
| `OPENAI_QUICK_MODEL` | `gpt-5-nano` |
| `OPENAI_DEEP_MODEL` | `gpt-5.4-mini` |

### 3. Open And Test The Public App

After deployment, Render displays a public address similar to:

```text
https://ai-podcast-summarizer.onrender.com
```

Open that address on a phone or computer. Paste a short public YouTube video
URL, choose **Quick scan** first to limit API cost, and click **Summarize**.

You can also check that the server is healthy:

```text
https://YOUR_RENDER_URL/health
```

It should display:

```json
{"status":"ok"}
```

### Free Tier Limitations

- Render free web services sleep after 15 minutes without incoming requests.
  The first visit after sleeping may take about a minute to wake up.
- Free Render services use temporary local storage. The app can still save a
  `.txt` report while running, but generated files can disappear after a sleep,
  restart, or redeploy.
- OpenAI API use is separate from Render hosting and consumes your OpenAI
  credits.

## Documentation

- [OpenAI Responses API text generation](https://developers.openai.com/api/docs/guides/text)
- [OpenAI GPT-5 nano model](https://developers.openai.com/api/docs/models/gpt-5-nano)
- [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api)
- [Render FastAPI deployment guide](https://render.com/docs/deploy-fastapi)
- [Render free tier limitations](https://render.com/free)
- [Render Blueprint YAML reference](https://render.com/docs/blueprint-spec)

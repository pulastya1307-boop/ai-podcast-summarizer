import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from openai import OpenAI, OpenAIError
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi


load_dotenv()

app = FastAPI(
    title="AI Podcast Summarizer",
    description="Summarize a YouTube podcast transcript with OpenAI.",
)

OUTPUT_FOLDER = Path("outputs")
HOME_PAGE = Path(__file__).parent / "static" / "index.html"
QUICK_MODEL = "gpt-5-nano"
DEEP_MODEL = "gpt-5.4-mini"


class SummaryRequest(BaseModel):
    youtube_url: str
    report_mode: Literal["quick", "deep"] = "quick"
    focus: str = ""


class SummaryResponse(BaseModel):
    video_id: str
    analysis: str
    report_mode: str
    model: str
    saved_to: str


def extract_video_id(youtube_url: str) -> str:
    """Return the video ID from common YouTube URL formats."""
    parsed_url = urlparse(youtube_url.strip())
    host = parsed_url.netloc.lower().removeprefix("www.")
    video_id = ""

    if host == "youtu.be":
        video_id = parsed_url.path.strip("/").split("/")[0]
    elif host in {"youtube.com", "m.youtube.com", "music.youtube.com"}:
        if parsed_url.path == "/watch":
            video_id = parse_qs(parsed_url.query).get("v", [""])[0]
        elif parsed_url.path.startswith(("/shorts/", "/embed/")):
            video_id = parsed_url.path.split("/")[2]

    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError("Please enter a valid YouTube video URL.")

    return video_id


def get_transcript(video_id: str) -> str:
    """Fetch an English YouTube transcript and combine its caption snippets."""
    try:
        fetched_transcript = YouTubeTranscriptApi().fetch(video_id, languages=["en"])
    except Exception as error:
        raise RuntimeError(
            "An English transcript could not be fetched for this video."
        ) from error

    transcript_text = " ".join(snippet.text for snippet in fetched_transcript).strip()
    if not transcript_text:
        raise RuntimeError("The transcript is empty.")

    return transcript_text


def summarize_transcript(
    transcript: str, report_mode: str, focus: str
) -> tuple[str, str]:
    """Ask OpenAI to turn the transcript into a structured written analysis."""
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to your .env file.")

    if report_mode == "deep":
        model = os.getenv("OPENAI_DEEP_MODEL", DEEP_MODEL)
        max_output_tokens = 1800
        reasoning = {"effort": "none"}
        verbosity = "medium"
        report_detail = "Give a thoughtful report with concrete detail."
    else:
        model = os.getenv("OPENAI_QUICK_MODEL", QUICK_MODEL)
        max_output_tokens = 1000
        reasoning = {"effort": "minimal"}
        verbosity = "low"
        report_detail = "Keep the report compact and practical."

    client = OpenAI()
    focus_instruction = (
        f"Pay special attention to this listener question: {focus.strip()}"
        if focus.strip()
        else "No special listener question was provided."
    )
    prompt = f"""You are a careful analyst helping someone learn from a video or podcast transcript.

Read the transcript below and produce a clear report with exactly these headings:

# Episode Overview
Write a 3-5 sentence overview. State whether this is a discussion, presentation,
news roundup, music, or another type of content.

# Main Themes
- List 3-5 central topics or arguments, without unnecessary repetition.

# Key Insights
- List the strongest supported lessons and briefly explain why each matters.

# Startup Opportunities
- Only include ideas genuinely supported by the transcript.
- For each useful idea include: Problem | Target customer | Simple MVP | Risk to validate.
- If there is no credible startup opportunity, state that plainly.

# Action Plan
- List concrete next steps a listener could take after this episode.

# Questions To Verify
- Identify important claims, numbers, product capabilities, or assumptions that
  should be checked independently before acting on them.
- If none are present, say so.

Do not treat promotional or opinionated claims as verified facts. Attribute
claims to the speaker when appropriate. Do not invent details.
{report_detail}
{focus_instruction}

TRANSCRIPT:
{transcript}
"""

    try:
        response = client.responses.create(
            model=model,
            input=prompt,
            reasoning=reasoning,
            text={"verbosity": verbosity},
            max_output_tokens=max_output_tokens,
        )
    except OpenAIError as error:
        raise RuntimeError(f"OpenAI could not create a summary: {error}") from error

    analysis = response.output_text.strip()
    if not analysis:
        raise RuntimeError("OpenAI returned an empty summary. Please try again.")

    return analysis, model


def save_analysis(
    youtube_url: str,
    video_id: str,
    transcript: str,
    analysis: str,
    report_mode: str,
    model: str,
) -> Path:
    """Write the generated analysis to an easy-to-find text file."""
    OUTPUT_FOLDER.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    output_path = OUTPUT_FOLDER / f"{video_id}-{timestamp}.txt"
    file_text = f"""AI PODCAST SUMMARY
YouTube URL: {youtube_url}
Video ID: {video_id}
Generated at (UTC): {timestamp}
Model: {model}
Report mode: {report_mode}
Transcript characters: {len(transcript)}

{analysis}
"""
    output_path.write_text(file_text, encoding="utf-8")
    return output_path


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return HOME_PAGE.read_text(encoding="utf-8")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/summarize", response_model=SummaryResponse)
def create_summary(request: SummaryRequest) -> SummaryResponse:
    try:
        video_id = extract_video_id(request.youtube_url)
        transcript = get_transcript(video_id)
        analysis, model = summarize_transcript(
            transcript, request.report_mode, request.focus
        )
        saved_path = save_analysis(
            request.youtube_url,
            video_id,
            transcript,
            analysis,
            request.report_mode,
            model,
        )
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return SummaryResponse(
        video_id=video_id,
        analysis=analysis,
        report_mode=request.report_mode,
        model=model,
        saved_to=str(saved_path),
    )

# orchestator

Multi-agent "marketing team" bot for Telegram: copywriting, strategy, and calendar. Built with LangGraph and observable with [Opik](https://www.comet.com/docs/opik/).

## Capabilities

- **Copy**: Suggests email copy and marketing text from your brief.
- **Strategy**: Helps with marketing strategy, channels, and campaigns.
- **Calendar**: Checks your Google Calendar for today's agenda (or a given date).
- **Email**: Drafts and sends email via Gmail. The email agent suggests the content when you give only an idea (e.g. "recomiéndame un mensaje y envíalo a X"); you get a summary and confirm before sending.

## Requirements

- Python 3.11+
- OpenAI API key
- Telegram Bot Token ([@BotFather](https://t.me/BotFather))
- (Optional) Opik API key for tracing – [sign up](https://www.comet.com/signup) or self-host
- (For calendar) Google Cloud project with Calendar API and OAuth2 credentials

## Setup

### 1. Clone and install

```bash
cd orchestator
pip install -e .
# Or: pip install -r requirements.txt  (if using requirements.txt)
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your OPENAI_API_KEY and TELEGRAM_BOT_TOKEN
```

### 3. Opik (observability)

```bash
opik configure
```

This sets `OPIK_API_KEY` (and optionally `OPIK_URL` for self-hosted). All LangGraph runs are traced to Opik automatically.

### 4. Google Calendar and Gmail (for calendar and email agents)

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/).
2. Enable the **Google Calendar API** and the **Gmail API**.
3. Create OAuth 2.0 credentials:
   - **Desktop app**: no extra config.
   - **Web application**: in "Authorized redirect URIs" add exactly `http://localhost:8080/` and save.
4. In `.env` set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` (copy from the console; check for typos, e.g. letter `l` vs digit `1`).
5. From the project root with venv activated, run:

   ```bash
   python3 scripts/setup_calendar_oauth.py
   ```

   A browser will open; sign in with your Google account and accept the Calendar and Gmail (send) permissions. The script will print a new `GOOGLE_REFRESH_TOKEN`. Copy it into `.env`. If you already had a token with only Calendar scope, run the script again to add Gmail send scope and update your token.

6. Do not change `GOOGLE_CLIENT_ID` or `GOOGLE_CLIENT_SECRET` after generating the token; if you do, run the script again to get a new refresh token.

**If you see "invalid_grant" or "Bad Request"**: The refresh token is no longer valid (expired, revoked, or client ID/secret was changed). Fix any typo in Client ID/Secret, then run `python3 scripts/setup_calendar_oauth.py` again, complete the browser flow, and replace `GOOGLE_REFRESH_TOKEN` in `.env` with the new value. Restart the bot.

## Run locally (polling)

```bash
export BOT_MODE=polling
python -m src.main
```

Then open your bot in Telegram and send a message (e.g. "What do I have today?" or "Write a short email for a product launch").

## Run in production (webhook)

Set `BOT_MODE=webhook` and `WEBHOOK_URL=https://your-public-url.com/webhook`. The app will expose an HTTP server on `PORT` and register the webhook with Telegram. See [Deployment](#deployment) below.

## Deployment (Railway / Fly.io)

The **Dockerfile** runs `python -m src.main`. Set `BOT_MODE=webhook`, `PORT` (often provided by the platform), and `WEBHOOK_URL` to your public URL + `/webhook`.

### Railway

1. Create a project at [railway.app](https://railway.app), connect this repo.
2. Add variables: `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, `OPIK_API_KEY`, `GOOGLE_*` (if using calendar), and:
   - `BOT_MODE=webhook`
   - `WEBHOOK_URL=https://<your-app>.railway.app/webhook` (replace with your Railway app URL)
   - `PORT` is usually set by Railway automatically.
3. Deploy; Railway builds the Dockerfile and runs the bot. The app will register the webhook on startup.

### Fly.io

1. Install [flyctl](https://fly.io/docs/hands-on/install-flyctl/) and run `fly launch` in the repo.
2. Set secrets: `fly secrets set TELEGRAM_BOT_TOKEN=... OPENAI_API_KEY=...` (and others from `.env.example`).
3. Set `BOT_MODE=webhook` and `WEBHOOK_URL=https://<your-app>.fly.dev/webhook` in `fly.toml` or as secrets.
4. Ensure the app listens on `PORT` (default 8080); in `fly.toml` set `internal_port = 8080` and expose with `protocol = "tcp"` / `port = 443` as needed.
5. Deploy with `fly deploy`.

Do not commit `.env`; use the platform's secret or env UI.

## Project structure

- `src/main.py` – Entrypoint: build graph, start bot (polling or webhook).
- `src/config.py` – Settings from env.
- `src/graph/` – LangGraph orchestrator (planner, agents, synthesizer). Agent capabilities are declared in `src/graph/skills.py` (skills per node and tools).
- `src/agents/` – LLM and prompts for each agent.
- `src/bot/` – Telegram handlers and webhook server.
- `src/calendar/` – Google Calendar auth and client.
- `src/gmail/` – Gmail send (uses same OAuth as Calendar).
- `scripts/setup_calendar_oauth.py` – One-time OAuth to get Google tokens (Calendar + Gmail send).
- `scripts/seed_opik_prompts.py` – One-time seed of agent prompts into Opik's prompt library (see [Prompt management (Opik)](#prompt-management-opik)).

## Prompt management (Opik)

When `OPIK_API_KEY` is set, the app loads agent system prompts from Opik's prompt library (with in-memory cache). If Opik is not configured or a fetch fails, it falls back to the defaults in `src/agents/prompts.py`.

**One-time seed (recommended):** From the repo root with Opik configured, run:

```bash
python3 scripts/seed_opik_prompts.py
```

This creates or updates 7 Text prompts in Opik with names `orchestrator-planner`, `orchestrator-copy`, `orchestrator-strategy`, `orchestrator-calendar`, `orchestrator-email`, `orchestrator-email-from-draft`, and `orchestrator-synthesizer`. You can then edit any prompt in the Opik UI (Prompt library → click the prompt → Edit). Changes take effect after the app restarts (prompts are cached for the process lifetime).

**Manual option:** Create Text prompts in the Opik Prompt library with the exact names above and paste the matching content from `src/agents/prompts.py`.

## Next steps with Opik

- **Datasets**: In the Opik UI, create datasets for "copy" (input: brief, output: criteria for good copy) and "strategy" (input: marketing question, output: criteria for a good answer). Optionally run the graph over dataset items and log results as experiments.
- **Metrics**: Use built-in metrics (Answer Relevance, G-Eval, Usefulness, etc.) on those experiments. For the calendar agent, evaluate tool correctness and trajectory (e.g. that the correct date was queried).
- **Prompt versions**: Use Opik's prompt versioning and tags (e.g. "production") or commit IDs for A/B tests and rollbacks.
- **Production**: Use Opik's online evaluation rules, dashboards, and alerts to monitor quality and errors in production.

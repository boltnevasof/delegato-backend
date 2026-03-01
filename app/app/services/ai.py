import httpx
from loguru import logger

from app.core.config import settings


class AIService:
    CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

    async def generate_soul_and_agent_md(self, business_description: str) -> dict:
        soul_md = await self._call_claude(
            system="You are an AI assistant that generates SOUL.md files for AI agents. "
                   "SOUL.md defines the agent's personality, tone, values, and behavioral guidelines. "
                   "Write in Russian. Be specific and actionable.",
            user=f"Generate a SOUL.md for an AI agent serving this business:\n\n{business_description}",
        )
        agent_md = await self._call_claude(
            system="You are an AI assistant that generates AGENT.md files for AI agents. "
                   "AGENT.md defines the agent's capabilities, response templates, and operational rules. "
                   "Write in Russian. Be specific and actionable.",
            user=f"Generate an AGENT.md for an AI agent serving this business:\n\n{business_description}",
        )
        return {"soul_md": soul_md, "agent_md": agent_md}

    async def enhance_content(self, field: str, content: str) -> str:
        return await self._call_claude(
            system=f"You are an AI assistant that improves {field} files for AI agents. "
                   f"Enhance the content: improve clarity, add detail, fix grammar. "
                   f"Keep the same language. Return only the improved content.",
            user=f"Improve this {field} content:\n\n{content}",
        )

    async def _call_claude(self, system: str, user: str) -> str:
        headers = {
            "x-api-key": settings.CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": "claude-sonnet-4-5-20250929",
            "max_tokens": 4096,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.post(self.CLAUDE_API_URL, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return data["content"][0]["text"]
            except Exception as e:
                logger.error("Claude API call failed: {error}", error=str(e))
                raise RuntimeError(f"Claude API error: {e}")

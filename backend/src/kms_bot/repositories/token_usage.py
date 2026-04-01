from __future__ import annotations

from typing import Any

from kms_bot.repositories.base import BaseRepository


class TokenUsageRepository(BaseRepository):
    """持久化和查询 LLM token 使用记录。"""

    def record(
        self,
        *,
        timestamp: str,
        query: str,
        mode: str,
        provider: str,
        stage: str,
        prompt_tokens: int,
        completion_tokens: int,
        model: str | None = None,
    ) -> None:
        self.execute(
            """
            INSERT INTO token_usage
                (timestamp, query, mode, provider, stage, prompt_tokens, completion_tokens, model)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (timestamp, query, mode, provider, stage, prompt_tokens, completion_tokens, model),
        )

    def get_summary(self) -> dict[str, Any]:
        """返回 token 使用汇总统计。"""
        totals = self.fetch_one(
            """
            SELECT COALESCE(SUM(prompt_tokens), 0) AS total_prompt,
                   COALESCE(SUM(completion_tokens), 0) AS total_completion,
                   COUNT(*) AS total_requests
            FROM token_usage
            """
        )

        daily_rows = self.fetch_all(
            """
            SELECT DATE(timestamp) AS date,
                   SUM(prompt_tokens) AS prompt_tokens,
                   SUM(completion_tokens) AS completion_tokens,
                   COUNT(*) AS requests
            FROM token_usage
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 30
            """
        )

        by_provider_rows = self.fetch_all(
            """
            SELECT provider,
                   SUM(prompt_tokens) AS prompt_tokens,
                   SUM(completion_tokens) AS completion_tokens,
                   COUNT(*) AS requests
            FROM token_usage
            GROUP BY provider
            """
        )

        by_mode_rows = self.fetch_all(
            """
            SELECT mode,
                   SUM(prompt_tokens) AS prompt_tokens,
                   SUM(completion_tokens) AS completion_tokens,
                   COUNT(*) AS requests
            FROM token_usage
            GROUP BY mode
            """
        )

        total_prompt = int(totals["total_prompt"]) if totals else 0
        total_completion = int(totals["total_completion"]) if totals else 0

        return {
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_tokens": total_prompt + total_completion,
            "total_requests": int(totals["total_requests"]) if totals else 0,
            "daily": [
                {
                    "date": r["date"],
                    "prompt_tokens": int(r["prompt_tokens"]),
                    "completion_tokens": int(r["completion_tokens"]),
                    "requests": int(r["requests"]),
                }
                for r in daily_rows
            ],
            "by_provider": {
                r["provider"]: {
                    "prompt_tokens": int(r["prompt_tokens"]),
                    "completion_tokens": int(r["completion_tokens"]),
                    "requests": int(r["requests"]),
                }
                for r in by_provider_rows
            },
            "by_mode": {
                r["mode"]: {
                    "prompt_tokens": int(r["prompt_tokens"]),
                    "completion_tokens": int(r["completion_tokens"]),
                    "requests": int(r["requests"]),
                }
                for r in by_mode_rows
            },
        }

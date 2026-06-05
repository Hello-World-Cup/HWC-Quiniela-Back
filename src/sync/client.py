import httpx

API_BASE = "https://v3.football.api-sports.io"
LEAGUE_ID = 1
SEASON = 2026
BATCH_SIZE = 20


class ApiFootballClient:
    def __init__(self, api_key: str) -> None:
        self._headers = {"x-apisports-key": api_key}

    async def get_fixtures_by_ids(self, ids: list[int]) -> list[dict]:
        """Fetch fixtures by API-Football fixture IDs (batches of BATCH_SIZE)."""
        results: list[dict] = []
        for i in range(0, len(ids), BATCH_SIZE):
            batch = ids[i : i + BATCH_SIZE]
            ids_param = "-".join(str(fid) for fid in batch)
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{API_BASE}/fixtures",
                    headers=self._headers,
                    params={"ids": ids_param},
                    timeout=15.0,
                )
                r.raise_for_status()
                results.extend(r.json().get("response", []))
        return results

    async def get_all_fixtures(self) -> list[dict]:
        """Fetch all WC2026 fixtures — used for one-time fixture mapping."""
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{API_BASE}/fixtures",
                headers=self._headers,
                params={"league": LEAGUE_ID, "season": SEASON},
                timeout=30.0,
            )
            r.raise_for_status()
            return r.json().get("response", [])

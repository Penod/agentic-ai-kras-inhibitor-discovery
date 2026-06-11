from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


CHEMBL_API_BASE = "https://www.ebi.ac.uk/chembl/api/data"


class ChEMBLClient:
    def __init__(self, base_url: str = CHEMBL_API_BASE, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_json(self, endpoint: str, params: dict[str, str | int]) -> dict[str, Any]:
        url = f"{self.base_url}/{endpoint}.json?{urlencode(params)}"
        request = Request(url, headers={"User-Agent": "kras-mutant-inhibitor-discovery/0.1"})
        with urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def iter_activities(
        self,
        target_chembl_id: str,
        *,
        limit: int = 1000,
        max_records: int | None = None,
    ) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        offset = 0
        while True:
            payload = self.get_json(
                "activity",
                {
                    "target_chembl_id": target_chembl_id,
                    "limit": limit,
                    "offset": offset,
                },
            )
            batch = payload.get("activities", [])
            if not batch:
                break
            records.extend(batch)
            if max_records is not None and len(records) >= max_records:
                return records[:max_records]
            page_meta = payload.get("page_meta", {})
            next_url = page_meta.get("next")
            if not next_url:
                break
            offset += limit
        return records

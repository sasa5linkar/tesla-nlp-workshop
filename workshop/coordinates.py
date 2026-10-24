"""Opt-in, bounded lookup of public Wikidata Earth coordinates; no text queries."""
import json
import math
import re
import threading
import time
from collections import OrderedDict
from datetime import datetime, timezone

API_URL = "https://www.wikidata.org/w/api.php"
MAX_QIDS = 20
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
CACHE_TTL = 24 * 3600
CACHE_SIZE = 256
_CACHE = OrderedDict()
_LOCK = threading.Lock()


def valid_qid(value):
    return value if isinstance(value, str) and re.fullmatch(r"Q[1-9][0-9]{0,15}", value) else ""


def location_qids(result):
    return sorted({
        entity["qid"] for entity in result["entities"]
        if entity["label"] == "LOC" and valid_qid(entity.get("qid"))
    })


def _earth_point(entity):
    claims = entity.get("claims", {}).get("P625", [])
    claims = sorted(claims, key=lambda claim: claim.get("rank") != "preferred")
    for claim in claims:
        if claim.get("rank") == "deprecated":
            continue
        snak = claim.get("mainsnak", {})
        if snak.get("snaktype") != "value":
            continue
        value = snak.get("datavalue", {}).get("value", {})
        if not isinstance(value, dict) or value.get("globe") not in {
            "http://www.wikidata.org/entity/Q2", "https://www.wikidata.org/entity/Q2",
        }:
            continue
        lat, lon = value.get("latitude"), value.get("longitude")
        if (type(lat) in (int, float) and type(lon) in (int, float)
                and math.isfinite(lat) and math.isfinite(lon)
                and -90 <= lat <= 90 and -180 <= lon <= 180):
            return {"latitude": lat, "longitude": lon}
    return None


def lookup_coordinates(qids):
    """Call only after consent. One request, 20 IDs, 8 MiB and finite timeouts.

    The in-memory TTL/LRU cache holds public coordinates only, never source text.
    Network/proxy/certificate settings are inherited, with no retries or fallback.
    """
    requested = sorted({qid for qid in qids if valid_qid(qid)})
    selected = requested[:MAX_QIDS]
    now = time.monotonic()
    found, missing = {}, []
    with _LOCK:
        for qid in selected:
            cached = _CACHE.get(qid)
            if cached and now - cached[0] < CACHE_TTL:
                found[qid] = cached[1]
                _CACHE.move_to_end(qid)
            else:
                missing.append(qid)
    if missing:
        import httpx

        # No labels, full text, mention forms or user/session identifiers are sent.
        params = {"action": "wbgetentities", "ids": "|".join(missing), "props": "claims", "format": "json"}
        with httpx.Client(
            timeout=httpx.Timeout(15, connect=5), follow_redirects=False,
            headers={"User-Agent": "TeslaNLPWorkshop/0.1 (https://github.com/sasa5linkar/tesla-nlp-workshop)"},
        ) as client:
            started = time.monotonic()
            with client.stream("GET", API_URL, params=params) as response:
                response.raise_for_status()
                chunks, size = [], 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > MAX_RESPONSE_BYTES or time.monotonic() - started > 20:
                        raise ValueError("Coordinate response exceeds lookup limits")
                    chunks.append(chunk)
        payload = json.loads(b"".join(chunks))
        entities = payload.get("entities")
        if not isinstance(entities, dict):
            raise ValueError("Unexpected Wikidata response")
        checked_at = datetime.now(timezone.utc).isoformat()
        for qid in missing:
            entity = entities.get(qid, {})
            point = _earth_point(entity) if entity.get("id") == qid and "missing" not in entity else None
            found[qid] = ({
                **point, "qid": qid, "source": f"https://www.wikidata.org/wiki/{qid}#P625",
                "retrieved_at": checked_at,
            } if point else None)
        with _LOCK:
            for qid in missing:
                _CACHE[qid] = (time.monotonic(), found[qid])
                _CACHE.move_to_end(qid)
            while len(_CACHE) > CACHE_SIZE:
                _CACHE.popitem(last=False)
    return {
        "points": [found[qid] for qid in selected if found[qid]],
        "requested_qids": selected, "without_coordinates": [qid for qid in selected if not found[qid]],
        "omitted_count": max(0, len(requested) - MAX_QIDS),
        "source": API_URL, "license": "Wikidata structured data: CC0",
    }

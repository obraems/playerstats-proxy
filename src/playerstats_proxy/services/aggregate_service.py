from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import DefaultDict, Dict

from playerstats_proxy.models.schemas import AggregateStatsResponse


def _coerce_non_negative_int(value: object) -> int:
    # Convertit en int >= 0, sinon 0
    try:
        v = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0
    return v if v > 0 else 0


def _get_stats_root(player: dict) -> dict:
    # Accède au dict "stats" vanilla: player["stats"]["stats"]
    stats_wrapper = player.get("stats") or {}
    stats_root = stats_wrapper.get("stats") or {}
    return stats_root if isinstance(stats_root, dict) else {}


def compute_aggregate(players: list[dict]) -> Dict[str, Dict[str, int]]:
    # Calcule la somme de toutes les stats : section -> stat_key -> total
    totals: DefaultDict[str, DefaultDict[str, int]] = defaultdict(lambda: defaultdict(int))

    for p in players:
        stats_root = _get_stats_root(p)

        for section, section_map in stats_root.items():
            if not isinstance(section_map, dict):
                continue

            section_str = str(section)
            for stat_key, raw_value in section_map.items():
                stat_key_str = str(stat_key)
                totals[section_str][stat_key_str] += _coerce_non_negative_int(raw_value)

    # Convertit en dict simple
    return {section: dict(values) for section, values in totals.items()}


def build_aggregate_response(
    aggregate: Dict[str, Dict[str, int]],
    players_count: int,
    min_value: int,
    limit_per_section: int,
) -> AggregateStatsResponse:
    # Filtre et limite (si demandé), avec ordre stable (valeur desc puis clé)
    out: Dict[str, Dict[str, int]] = {}

    for section, mapping in aggregate.items():
        # Filtre par min_value
        filtered = [(k, v) for k, v in mapping.items() if v >= min_value]

        # Tri pour stabilité et pour rendre l'output lisible
        filtered.sort(key=lambda kv: (-kv[1], kv[0]))

        if limit_per_section > 0:
            filtered = filtered[:limit_per_section]

        if filtered:
            out[section] = {k: v for k, v in filtered}

    return AggregateStatsResponse(
        players=players_count,
        min_value=min_value,
        limit_per_section=limit_per_section,
        updated_at=datetime.now(timezone.utc),
        stats=out,
    )

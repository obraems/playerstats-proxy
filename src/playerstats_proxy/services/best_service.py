from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Tuple

from playerstats_proxy.models.schemas import BestStatEntry, BestStatsResponse


MaxInfo = Tuple[int, int]  # (max_value, winners_count)
MaxMap = Dict[Tuple[str, str], MaxInfo]  # (section, stat_key) -> MaxInfo


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


def compute_maxima(players: list[dict]) -> MaxMap:
    # Calcule, pour chaque (section, stat_key), la valeur max et le nombre de gagnants (ties)
    maxima: MaxMap = {}

    for p in players:
        stats_root = _get_stats_root(p)

        for section, section_map in stats_root.items():
            if not isinstance(section_map, dict):
                continue

            for stat_key, raw_value in section_map.items():
                value = _coerce_non_negative_int(raw_value)
                key = (str(section), str(stat_key))

                current = maxima.get(key)
                if current is None:
                    maxima[key] = (value, 1)
                    continue

                current_max, winners_count = current
                if value > current_max:
                    maxima[key] = (value, 1)
                elif value == current_max:
                    maxima[key] = (current_max, winners_count + 1)

    return maxima


def _find_player(players: list[dict], player_name: str) -> dict | None:
    # Recherche par nom (case-insensitive)
    needle = player_name.strip().lower()
    for p in players:
        name = str(p.get("name") or "").strip().lower()
        if name == needle:
            return p
    return None


def build_best_stats(
    players: list[dict],
    maxima: MaxMap,
    player_name: str,
    min_value: int,
    include_zeros: bool,
    max_results: int,
) -> BestStatsResponse:
    target = _find_player(players, player_name)
    if target is None:
        raise KeyError(f"Player not found: {player_name}")

    uuid = str(target.get("uuid") or "")
    name = str(target.get("name") or "")

    stats_root = _get_stats_root(target)

    results: list[BestStatEntry] = []

    for section, section_map in stats_root.items():
        if not isinstance(section_map, dict):
            continue

        for stat_key, raw_value in section_map.items():
            value = _coerce_non_negative_int(raw_value)

            if not include_zeros and value == 0:
                continue
            if value < min_value:
                continue

            max_value, winners_count = maxima.get((str(section), str(stat_key)), (0, 1))
            if value == max_value and (include_zeros or max_value > 0):
                results.append(
                    BestStatEntry(
                        section=str(section),
                        stat_key=str(stat_key),
                        value=value,
                        max_value=max_value,
                        winners_count=winners_count,
                        tied=(winners_count > 1),
                    )
                )

    # Tri par valeur décroissante puis clé pour stabilité
    results.sort(key=lambda r: (-r.value, r.section, r.stat_key))

    limited = results[:max_results]

    return BestStatsResponse(
        uuid=uuid,
        name=name,
        min_value=min_value,
        include_zeros=include_zeros,
        max_results=max_results,
        updated_at=datetime.now(timezone.utc),
        results=limited,
    )

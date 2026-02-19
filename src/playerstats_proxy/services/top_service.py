from __future__ import annotations

from datetime import datetime, timezone

from playerstats_proxy.models.schemas import TopEntry, TopResponse


def _read_stat_value(player: dict, section: str, stat_key: str) -> int:
    # Navigation robuste dans la structure du JSON upstream
    stats_wrapper = player.get("stats") or {}
    stats_root = stats_wrapper.get("stats") or {}
    section_map = stats_root.get(section) or {}
    value = section_map.get(stat_key, 0)

    try:
        value_int = int(value)
    except (TypeError, ValueError):
        value_int = 0

    return max(0, value_int)


def _compute_percent(value: int, total_value: int) -> float:
    # Calcule un pourcentage sur le total (0 si total=0)
    if total_value <= 0:
        return 0.0
    return round((value / total_value) * 100.0, 6)


def build_top(
    players: list[dict],
    section: str,
    stat_key: str,
    limit: int,
    include_zeros: bool,
    total_value: int,
) -> TopResponse:
    entries: list[TopEntry] = []

    for p in players:
        name = str(p.get("name") or "")
        uuid = str(p.get("uuid") or "")
        if not name or not uuid:
            continue

        value = _read_stat_value(p, section, stat_key)
        if value == 0 and not include_zeros:
            continue

        entries.append(
            TopEntry(
                uuid=uuid,
                name=name,
                value=value,
                section=section,
                stat_key=stat_key,
                total_value=total_value,
                percent_of_total=_compute_percent(value, total_value),
            )
        )

    # Tri décroissant sur la valeur, puis par nom pour stabiliser
    entries.sort(key=lambda e: (-e.value, e.name.lower()))
    limited = entries[: max(1, limit)]

    return TopResponse(
        section=section,
        stat_key=stat_key,
        limit=max(1, limit),
        include_zeros=include_zeros,
        updated_at=datetime.now(timezone.utc),
        total_value=max(0, int(total_value)),
        results=limited,
    )

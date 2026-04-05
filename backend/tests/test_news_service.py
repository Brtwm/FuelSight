from __future__ import annotations

from app.services.news_service import NewsService


def test_build_fixture_news_is_deterministic_and_sorted() -> None:
    service = NewsService(session=None)  # type: ignore[arg-type]
    rows = service._build_fixture_news()

    assert len(rows) >= 3
    assert rows[0]["published_at"] >= rows[1]["published_at"]
    assert rows[0]["ref_id"].startswith("gdelt_")
    assert rows[0]["id"] != rows[1]["id"]


def test_digest_text_and_bullets_for_empty_rows() -> None:
    assert NewsService._build_summary_text([]) == "В выбранном периоде новости не найдены."
    assert NewsService._build_bullet_points([]) == ["Новостных сигналов за период не обнаружено."]

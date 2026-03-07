from datetime import date

from sealimg.ids import ImageIdGenerator
from sealimg.profiles import merge_profile


def test_image_id_generator_increments_within_day() -> None:
    gen = ImageIdGenerator(prefix="IMG")
    day = date(2026, 3, 6)
    assert gen.next_id(day=day) == "IMG-2026-03-06-0001"
    assert gen.next_id(day=day) == "IMG-2026-03-06-0002"


def test_image_id_generator_respects_existing_ids() -> None:
    gen = ImageIdGenerator(prefix="IMG")
    day = date(2026, 3, 6)
    existing = {"IMG-2026-03-06-0007", "IMG-2026-03-06-0003"}
    assert gen.next_id(day=day, existing_ids=existing) == "IMG-2026-03-06-0008"


def test_profile_merge_precedence_and_depth() -> None:
    defaults = {
        "long_edge": 2560,
        "jpeg_quality": 82,
        "wm_visible": {"enabled": True, "style": "diag-low"},
    }
    selected = {"jpeg_quality": 88, "wm_visible": {"style": "center"}}
    cli = {"wm_visible": {"enabled": False}, "bundle": True}
    merged = merge_profile(defaults, selected, cli)

    assert merged["long_edge"] == 2560
    assert merged["jpeg_quality"] == 88
    assert merged["wm_visible"]["style"] == "center"
    assert merged["wm_visible"]["enabled"] is False
    assert merged["bundle"] is True

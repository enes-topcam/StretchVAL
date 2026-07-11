"""Aspect ratio hesabi (saf fonksiyon) testleri."""

from backend.display import aspect_ratio


def test_known_aspect_ratios():
    assert aspect_ratio(1280, 960) == "4:3"
    assert aspect_ratio(1280, 1024) == "5:4"
    assert aspect_ratio(1920, 1080) == "16:9"
    assert aspect_ratio(1680, 1050) == "16:10"


def test_zero_height_is_safe():
    assert aspect_ratio(1280, 0) == "?"

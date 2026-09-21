from app.brand_builder import _validate_public_url, build_brand_draft


def test_ssrf_blocks_private():
    for bad in (
        "http://127.0.0.1/",
        "http://localhost/x",
        "http://10.1.2.3/",
        "http://192.168.0.5/",
        "file:///etc/passwd",
    ):
        try:
            _validate_public_url(bad)
            assert False, f"should block {bad}"
        except ValueError:
            pass


def test_allows_public_https():
    assert _validate_public_url("https://example.com/about").startswith("https://example.com")


def test_draft_labeled():
    d = build_brand_draft(
        website_url="https://example.com",
        brand_notes="Name: Demo\nBe warm.",
        site={
            "title": "Demo | Home",
            "text": "We offer residential cleaning. Our team provides weekly service.",
            "url": "https://example.com",
            "error": None,
        },
    )
    assert "[DRAFT" in d["prompt"]
    assert d["label"] == "draft"
    assert d["faq"]

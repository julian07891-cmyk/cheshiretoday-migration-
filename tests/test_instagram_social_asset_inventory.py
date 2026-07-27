from pathlib import Path

from backend.app.instagram_social_asset import INSTAGRAM_TOP_STORY_FORMAT
from backend.app.social_asset_constants import (
    INSTAGRAM_GRAPHIC_FORMATS,
    INSTAGRAM_GRAPHIC_MASTERS,
)


def test_phase_one_inventory_is_exact_and_cross_layer_visible():
    assert INSTAGRAM_GRAPHIC_FORMATS == frozenset({("story", "top-story")})
    assert set(INSTAGRAM_GRAPHIC_MASTERS) == set(INSTAGRAM_GRAPHIC_FORMATS)
    assert INSTAGRAM_TOP_STORY_FORMAT in INSTAGRAM_GRAPHIC_FORMATS
    server = Path("backend/server.py").read_text(encoding="utf-8")
    service = Path("frontend/src/services/instagramSocialAsset.js").read_text(encoding="utf-8")
    dialog = Path("frontend/src/components/admin/SocialPublishingDialog.jsx").read_text(encoding="utf-8")
    assert '/admin/social-assets/instagram/story/{article_id}' in server
    assert '/api/admin/social-assets/instagram/story/' in service
    assert "platform: 'instagram', format: 'story', layout: 'top-story'" in service
    assert 'value="story"' in dialog
    assert 'value="top-story"' in dialog
    for unsupported in ("feed", "reels", "threads"):
        assert ("instagram", unsupported) not in INSTAGRAM_GRAPHIC_FORMATS


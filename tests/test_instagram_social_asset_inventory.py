from pathlib import Path

from backend.app.instagram_social_asset import (
    INSTAGRAM_FEED_FORMAT,
    INSTAGRAM_REELS_COVER_FORMAT,
    INSTAGRAM_TOP_STORY_FORMAT,
)
from backend.app.social_asset_constants import (
    INSTAGRAM_GRAPHIC_FORMATS,
    INSTAGRAM_GRAPHIC_MASTERS,
)


def test_instagram_inventory_is_exact_and_cross_layer_visible():
    expected = frozenset({
        ("story", "top-story"),
        ("feed", "local-news"),
        ("reels-cover", "local-news"),
    })
    assert INSTAGRAM_GRAPHIC_FORMATS == expected
    assert set(INSTAGRAM_GRAPHIC_MASTERS) == set(INSTAGRAM_GRAPHIC_FORMATS)
    assert INSTAGRAM_TOP_STORY_FORMAT in INSTAGRAM_GRAPHIC_FORMATS
    assert INSTAGRAM_FEED_FORMAT in INSTAGRAM_GRAPHIC_FORMATS
    assert INSTAGRAM_REELS_COVER_FORMAT in INSTAGRAM_GRAPHIC_FORMATS
    server = Path("backend/server.py").read_text(encoding="utf-8")
    service = Path("frontend/src/services/instagramSocialAsset.js").read_text(encoding="utf-8")
    dialog = Path("frontend/src/components/admin/SocialPublishingDialog.jsx").read_text(encoding="utf-8")
    assert '/admin/social-assets/instagram/story/{article_id}' in server
    assert '/admin/social-assets/instagram/feed/{article_id}' in server
    assert '/admin/social-assets/instagram/reels-cover/{article_id}' in server
    assert '/api/admin/social-assets/instagram/${format}/' in service
    assert "platform: 'instagram', format: 'story', layout: 'top-story'" in service
    assert "platform: 'instagram', format: 'feed', layout: 'local-news'" in service
    assert "platform: 'instagram', format: 'reels-cover', layout: 'local-news'" in service
    assert "value: 'story', label: 'Story', layout: 'Top Story'" in dialog
    assert "value: 'feed', label: 'Feed', layout: 'Local News'" in dialog
    assert "value: 'reels-cover', label: 'Reels Cover', layout: 'Local News'" in dialog
    for unsupported in ("reels", "threads"):
        assert ("instagram", unsupported) not in INSTAGRAM_GRAPHIC_FORMATS

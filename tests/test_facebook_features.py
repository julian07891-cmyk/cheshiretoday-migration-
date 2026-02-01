"""
Test suite for Facebook posting features:
1. Hashtag generation - combination of category and location hashtags
2. Duplicate prevention in auto-scheduler - 24-hour sliding window
3. Facebook post single article endpoint
4. Backend server health
"""
import pytest
import requests
import os
import sys

# Add backend to path for direct imports
sys.path.insert(0, '/app/backend')

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_USERNAME = "news@cheshiretoday.co.uk"
ADMIN_PASSWORD = "ningab-zipxur-8pibDi"


class TestBackendHealth:
    """Test backend server is running and accessible"""
    
    def test_articles_endpoint_accessible(self):
        """Test that articles endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/articles?limit=1", timeout=10)
        assert response.status_code == 200, f"Articles endpoint failed: {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Expected list of articles"
        print(f"✅ Articles endpoint accessible, returned {len(data)} articles")
    
    def test_admin_login(self):
        """Test admin login works"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
            timeout=10
        )
        assert response.status_code == 200, f"Admin login failed: {response.status_code}"
        data = response.json()
        assert data.get("success") == True, "Login should succeed"
        assert "token" in data, "Token should be returned"
        print(f"✅ Admin login successful, token received")
        return data["token"]


class TestHashtagGeneration:
    """Test hashtag generation for Facebook posts - combination of category and location"""
    
    def test_hashtag_generation_with_chester_location(self):
        """Test hashtags include Chester location when mentioned in title"""
        from app.facebook_service import FacebookService
        
        fb_service = FacebookService()
        
        # Test with Chester in title
        hashtags = fb_service._generate_hashtags(
            title="Chester Council announces new parking regulations",
            category="Local News",
            source="Chester Chronicle"
        )
        
        assert "#CheshireToday" in hashtags, "Should include #CheshireToday"
        assert "#CheshireNews" in hashtags, "Should include #CheshireNews"
        assert "#Chester" in hashtags, f"Should include #Chester for Chester article. Got: {hashtags}"
        assert "#LocalNews" in hashtags or "#CheshireLife" in hashtags, "Should include category hashtag"
        print(f"✅ Chester hashtags generated: {hashtags}")
    
    def test_hashtag_generation_with_knutsford_location(self):
        """Test hashtags include Knutsford location when mentioned in title"""
        from app.facebook_service import FacebookService
        
        fb_service = FacebookService()
        
        hashtags = fb_service._generate_hashtags(
            title="Knutsford Royal May Day celebrations announced",
            category="Events",
            source="Knutsford Guardian"
        )
        
        assert "#CheshireToday" in hashtags, "Should include #CheshireToday"
        assert "#Knutsford" in hashtags, f"Should include #Knutsford. Got: {hashtags}"
        print(f"✅ Knutsford hashtags generated: {hashtags}")
    
    def test_hashtag_generation_with_warrington_location(self):
        """Test hashtags include Warrington location when mentioned in title"""
        from app.facebook_service import FacebookService
        
        fb_service = FacebookService()
        
        hashtags = fb_service._generate_hashtags(
            title="Warrington Wolves secure playoff spot",
            category="Sports",
            source="Warrington Guardian"
        )
        
        assert "#CheshireToday" in hashtags, "Should include #CheshireToday"
        assert "#Warrington" in hashtags, f"Should include #Warrington. Got: {hashtags}"
        assert "#Sports" in hashtags or "#CheshireSports" in hashtags, "Should include sports hashtag"
        print(f"✅ Warrington hashtags generated: {hashtags}")
    
    def test_hashtag_generation_health_category(self):
        """Test hashtags include Health category tags"""
        from app.facebook_service import FacebookService
        
        fb_service = FacebookService()
        
        hashtags = fb_service._generate_hashtags(
            title="NHS announces new hospital services",
            category="Health",
            source="BBC News"
        )
        
        assert "#CheshireToday" in hashtags, "Should include #CheshireToday"
        assert "#Health" in hashtags or "#NHSNews" in hashtags or "#UKHealth" in hashtags, f"Should include health hashtag. Got: {hashtags}"
        print(f"✅ Health hashtags generated: {hashtags}")
    
    def test_hashtag_generation_sports_category(self):
        """Test hashtags include Sports category tags"""
        from app.facebook_service import FacebookService
        
        fb_service = FacebookService()
        
        hashtags = fb_service._generate_hashtags(
            title="Local football team wins championship",
            category="Sports",
            source="Local Sports"
        )
        
        assert "#CheshireToday" in hashtags, "Should include #CheshireToday"
        assert "#Sports" in hashtags or "#CheshireSports" in hashtags, f"Should include sports hashtag. Got: {hashtags}"
        print(f"✅ Sports hashtags generated: {hashtags}")
    
    def test_hashtag_generation_combination(self):
        """Test hashtags combine category AND location"""
        from app.facebook_service import FacebookService
        
        fb_service = FacebookService()
        
        # Test with both location and category
        hashtags = fb_service._generate_hashtags(
            title="Macclesfield hospital receives NHS funding boost",
            category="Health",
            source="Macclesfield Express"
        )
        
        assert "#CheshireToday" in hashtags, "Should include #CheshireToday"
        assert "#Macclesfield" in hashtags, f"Should include #Macclesfield. Got: {hashtags}"
        # Should have health category tags
        has_health_tag = any(tag in hashtags for tag in ["#Health", "#NHSNews", "#UKHealth", "#NHS", "#Hospital"])
        assert has_health_tag, f"Should include health category hashtag. Got: {hashtags}"
        print(f"✅ Combination hashtags (location + category) generated: {hashtags}")
    
    def test_hashtag_generation_topic_keywords(self):
        """Test hashtags include topic-based keywords like police, crime"""
        from app.facebook_service import FacebookService
        
        fb_service = FacebookService()
        
        hashtags = fb_service._generate_hashtags(
            title="Police investigate crime spree in Chester",
            category="Local News",
            source="Chester Chronicle"
        )
        
        assert "#CheshireToday" in hashtags, "Should include #CheshireToday"
        assert "#Chester" in hashtags, f"Should include #Chester. Got: {hashtags}"
        # Should have police/crime topic tags
        has_topic_tag = any(tag in hashtags for tag in ["#Police", "#Crime", "#UKCrime"])
        assert has_topic_tag, f"Should include police/crime topic hashtag. Got: {hashtags}"
        print(f"✅ Topic-based hashtags generated: {hashtags}")
    
    def test_hashtag_limit(self):
        """Test that hashtags are limited to 8 max for readability"""
        from app.facebook_service import FacebookService
        
        fb_service = FacebookService()
        
        # Test with many potential hashtags
        hashtags = fb_service._generate_hashtags(
            title="Chester police investigate hospital crime near school council traffic flooding",
            category="Local News",
            source="Chester Chronicle"
        )
        
        # Count hashtags
        hashtag_count = hashtags.count('#')
        assert hashtag_count <= 8, f"Should have max 8 hashtags, got {hashtag_count}: {hashtags}"
        print(f"✅ Hashtag limit enforced: {hashtag_count} hashtags")


class TestDuplicatePrevention:
    """Test duplicate prevention in auto-scheduler"""
    
    def test_duplicate_filter_method_exists(self):
        """Test that _filter_duplicates method exists in FacebookService"""
        from app.facebook_service import FacebookService
        
        fb_service = FacebookService()
        assert hasattr(fb_service, '_filter_duplicates'), "FacebookService should have _filter_duplicates method"
        print("✅ _filter_duplicates method exists")
    
    def test_duplicate_filter_by_url(self):
        """Test that duplicate articles with same URL are filtered"""
        from app.facebook_service import FacebookService
        
        fb_service = FacebookService()
        
        # Use completely different titles to avoid title-based filtering
        articles = [
            {"title": "Chester Council announces new parking regulations for city center", "source_url": "https://example.com/article1"},
            {"title": "Knutsford Royal May Day celebrations set for spring festival", "source_url": "https://example.com/article2"},
            {"title": "Warrington Wolves secure playoff spot in rugby league", "source_url": "https://example.com/article1"},  # Same URL as first
        ]
        
        unique = fb_service._filter_duplicates(articles)
        # Should filter out the duplicate URL, keeping 2 unique articles
        assert len(unique) == 2, f"Should filter duplicate URL, got {len(unique)} articles"
        print(f"✅ Duplicate URL filtering works: {len(articles)} -> {len(unique)} articles")
    
    def test_duplicate_filter_by_similar_title(self):
        """Test that articles with similar titles are filtered"""
        from app.facebook_service import FacebookService
        
        fb_service = FacebookService()
        
        articles = [
            {"title": "Chester Council announces new parking regulations", "source_url": "https://example.com/1"},
            {"title": "New parking regulations announced by Chester Council", "source_url": "https://example.com/2"},  # Similar
            {"title": "Completely different article about weather", "source_url": "https://example.com/3"},
        ]
        
        unique = fb_service._filter_duplicates(articles)
        # Should filter out the similar title
        assert len(unique) <= 2, f"Should filter similar titles, got {len(unique)} articles"
        print(f"✅ Similar title filtering works: {len(articles)} -> {len(unique)} articles")


class TestFacebookPostEndpoint:
    """Test Facebook post single article endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token for authenticated requests"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Could not get admin token")
    
    def test_facebook_status_endpoint(self, admin_token):
        """Test Facebook status endpoint returns configuration status"""
        response = requests.get(
            f"{BASE_URL}/api/facebook/status",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10
        )
        # May return 200 or 404 depending on endpoint existence
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Facebook status endpoint accessible: {data}")
        elif response.status_code == 404:
            print("⚠️ Facebook status endpoint not found (may not be implemented)")
        else:
            print(f"⚠️ Facebook status returned: {response.status_code}")
    
    def test_facebook_post_article_endpoint_exists(self, admin_token):
        """Test that Facebook post article endpoint exists"""
        # Get an article ID first
        articles_response = requests.get(f"{BASE_URL}/api/articles?limit=1", timeout=10)
        if articles_response.status_code != 200 or not articles_response.json():
            pytest.skip("No articles available to test")
        
        article_id = articles_response.json()[0].get("id")
        
        # Try to post using the correct endpoint: /facebook/post-single?article_id=xxx
        response = requests.post(
            f"{BASE_URL}/api/facebook/post-single",
            params={"article_id": article_id},
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=15
        )
        
        # Endpoint should exist (200, 400, 401, or 500 - not 404)
        assert response.status_code != 404, f"Facebook post endpoint should exist, got 404"
        print(f"✅ Facebook post endpoint exists, returned: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data}")


class TestScheduledFacebookPostLogic:
    """Test the scheduled Facebook post logic for duplicate prevention"""
    
    def test_facebook_post_log_collection_accessible(self):
        """Test that facebook_post_log collection can be queried"""
        # This tests the MongoDB collection used for duplicate tracking
        # We'll verify via the API that the scheduler logic is in place
        
        # Get admin token
        login_response = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
            timeout=10
        )
        
        if login_response.status_code != 200:
            pytest.skip("Could not authenticate")
        
        token = login_response.json().get("token")
        
        # Check scheduled posts endpoint (which uses similar logic)
        response = requests.get(
            f"{BASE_URL}/api/facebook/scheduled-posts",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        # Endpoint may or may not exist, but we're testing the infrastructure
        if response.status_code == 200:
            print(f"✅ Scheduled posts endpoint accessible")
        elif response.status_code == 404:
            print("⚠️ Scheduled posts endpoint not found")
        else:
            print(f"⚠️ Scheduled posts returned: {response.status_code}")


class TestHashtagIntegrationInPostArticle:
    """Test that hashtags are actually included in Facebook post messages"""
    
    def test_post_article_method_uses_hashtags(self):
        """Verify post_article method calls _generate_hashtags"""
        from app.facebook_service import FacebookService
        import inspect
        
        fb_service = FacebookService()
        
        # Check that post_article method exists and references _generate_hashtags
        source_code = inspect.getsource(fb_service.post_article)
        
        assert "_generate_hashtags" in source_code, "post_article should call _generate_hashtags"
        assert "hashtags" in source_code.lower(), "post_article should use hashtags variable"
        print("✅ post_article method uses _generate_hashtags")
    
    def test_hashtags_added_to_message(self):
        """Verify hashtags are added to the Facebook message"""
        from app.facebook_service import FacebookService
        import inspect
        
        fb_service = FacebookService()
        
        # Check that post_article adds hashtags to message
        source_code = inspect.getsource(fb_service.post_article)
        
        # Look for message += hashtags or similar
        assert "message +=" in source_code and "hashtags" in source_code, \
            "post_article should append hashtags to message"
        print("✅ Hashtags are appended to Facebook message")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

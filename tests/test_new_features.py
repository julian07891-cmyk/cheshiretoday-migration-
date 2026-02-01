"""
Test suite for new features:
1. Comments system with email-based login
2. Newsletter segmentation with category and frequency preferences
3. Reading time (frontend feature - tested via API article content)
"""

import pytest
import requests
import os
import random
import string
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cheshire-fix.preview.emergentagent.com').rstrip('/')

# Generate unique test email for each test run
def generate_test_email():
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{random_suffix}@example.com"

class TestNewsletterCategories:
    """Test newsletter categories endpoint"""
    
    def test_get_newsletter_categories(self):
        """GET /api/newsletter/categories returns category list"""
        response = requests.get(f"{BASE_URL}/api/newsletter/categories")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "categories" in data, "Response should contain 'categories'"
        assert "frequencies" in data, "Response should contain 'frequencies'"
        
        # Validate categories structure
        categories = data["categories"]
        assert len(categories) >= 5, f"Expected at least 5 categories, got {len(categories)}"
        
        # Check category structure
        for cat in categories:
            assert "id" in cat, "Category should have 'id'"
            assert "name" in cat, "Category should have 'name'"
            assert "description" in cat, "Category should have 'description'"
        
        # Validate frequencies structure
        frequencies = data["frequencies"]
        assert len(frequencies) >= 3, f"Expected at least 3 frequencies, got {len(frequencies)}"
        
        # Check frequency IDs
        freq_ids = [f["id"] for f in frequencies]
        assert "daily" in freq_ids, "Should have 'daily' frequency"
        assert "weekly" in freq_ids, "Should have 'weekly' frequency"
        assert "breaking_only" in freq_ids, "Should have 'breaking_only' frequency"
        
        print(f"✅ Newsletter categories: {len(categories)} categories, {len(frequencies)} frequencies")


class TestNewsletterPreferences:
    """Test newsletter preferences CRUD"""
    
    def test_subscribe_with_preferences(self):
        """POST /api/subscribe with preferences"""
        test_email = generate_test_email()
        
        payload = {
            "email": test_email,
            "preferences": {
                "categories": ["Local News", "Sports", "Tech"],
                "frequency": "weekly"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/subscribe",
            json=payload
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Subscribe should succeed"
        
        print(f"✅ Subscribed {test_email} with custom preferences")
        
        # Verify preferences were saved
        prefs_response = requests.get(f"{BASE_URL}/api/newsletter/preferences/{test_email}")
        
        assert prefs_response.status_code == 200, f"Expected 200, got {prefs_response.status_code}"
        
        prefs_data = prefs_response.json()
        assert prefs_data.get("success") == True
        assert prefs_data.get("email") == test_email
        
        saved_prefs = prefs_data.get("preferences", {})
        assert "Local News" in saved_prefs.get("categories", []), "Should have Local News category"
        assert saved_prefs.get("frequency") == "weekly", "Should have weekly frequency"
        
        print(f"✅ Verified preferences for {test_email}")
    
    def test_update_newsletter_preferences(self):
        """PUT /api/newsletter/preferences updates subscriber preferences"""
        test_email = generate_test_email()
        
        # First subscribe
        subscribe_response = requests.post(
            f"{BASE_URL}/api/subscribe",
            json={"email": test_email}
        )
        assert subscribe_response.status_code == 200
        
        # Update preferences
        update_payload = {
            "email": test_email,
            "preferences": {
                "categories": ["UK News", "Business", "Health"],
                "frequency": "breaking_only"
            }
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/newsletter/preferences",
            json=update_payload
        )
        
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}: {update_response.text}"
        
        data = update_response.json()
        assert data.get("success") == True, "Update should succeed"
        
        # Verify update
        prefs_response = requests.get(f"{BASE_URL}/api/newsletter/preferences/{test_email}")
        prefs_data = prefs_response.json()
        
        saved_prefs = prefs_data.get("preferences", {})
        assert "UK News" in saved_prefs.get("categories", []), "Should have UK News category"
        assert saved_prefs.get("frequency") == "breaking_only", "Should have breaking_only frequency"
        
        print(f"✅ Updated and verified preferences for {test_email}")
    
    def test_get_preferences_nonexistent_email(self):
        """GET /api/newsletter/preferences/{email} returns 404 for non-subscriber"""
        fake_email = "nonexistent_" + generate_test_email()
        
        response = requests.get(f"{BASE_URL}/api/newsletter/preferences/{fake_email}")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        
        print(f"✅ Correctly returns 404 for non-existent subscriber")


class TestCommentsRegisterVerify:
    """Test comments registration and verification flow"""
    
    def test_register_commenter(self):
        """POST /api/comments/register sends verification code"""
        test_email = generate_test_email()
        
        payload = {
            "email": test_email,
            "name": "Test User"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/comments/register",
            json=payload
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Registration should succeed"
        assert "message" in data, "Should have message"
        assert test_email in data.get("message", ""), "Message should mention email"
        
        print(f"✅ Registration successful for {test_email}")
    
    def test_register_commenter_short_name(self):
        """POST /api/comments/register rejects short names"""
        test_email = generate_test_email()
        
        payload = {
            "email": test_email,
            "name": "A"  # Too short
        }
        
        response = requests.post(
            f"{BASE_URL}/api/comments/register",
            json=payload
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        print(f"✅ Correctly rejects short name")
    
    def test_verify_invalid_code(self):
        """POST /api/comments/verify rejects invalid code"""
        test_email = generate_test_email()
        
        # First register
        requests.post(
            f"{BASE_URL}/api/comments/register",
            json={"email": test_email, "name": "Test User"}
        )
        
        # Try to verify with wrong code
        verify_response = requests.post(
            f"{BASE_URL}/api/comments/verify",
            json={"email": test_email, "code": "000000"}
        )
        
        assert verify_response.status_code == 400, f"Expected 400, got {verify_response.status_code}"
        
        print(f"✅ Correctly rejects invalid verification code")
    
    def test_verify_no_registration(self):
        """POST /api/comments/verify rejects unregistered email"""
        fake_email = "never_registered_" + generate_test_email()
        
        response = requests.post(
            f"{BASE_URL}/api/comments/verify",
            json={"email": fake_email, "code": "123456"}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        print(f"✅ Correctly rejects verification for unregistered email")


class TestCommentsArticle:
    """Test comments retrieval for articles"""
    
    def test_get_article_comments(self):
        """GET /api/comments/article/{id} returns comments"""
        # First get an article ID
        articles_response = requests.get(f"{BASE_URL}/api/articles?limit=1")
        
        if articles_response.status_code != 200:
            pytest.skip("Could not fetch articles")
        
        articles = articles_response.json()
        if not articles or len(articles) == 0:
            pytest.skip("No articles available")
        
        article_id = articles[0].get("id")
        if not article_id:
            pytest.skip("Article has no ID")
        
        # Get comments for article
        response = requests.get(f"{BASE_URL}/api/comments/article/{article_id}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("success") == True, "Should succeed"
        assert "comments" in data, "Should have 'comments' field"
        assert isinstance(data["comments"], list), "Comments should be a list"
        assert "total" in data, "Should have 'total' field"
        
        print(f"✅ Got {len(data['comments'])} comments for article {article_id[:8]}...")
    
    def test_get_comments_nonexistent_article(self):
        """GET /api/comments/article/{id} returns empty for non-existent article"""
        fake_id = "nonexistent-article-id-12345"
        
        response = requests.get(f"{BASE_URL}/api/comments/article/{fake_id}")
        
        # Should return 200 with empty comments, not 404
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("success") == True
        assert data.get("comments") == [], "Should return empty comments list"
        
        print(f"✅ Returns empty comments for non-existent article")


class TestCommentsAuth:
    """Test comments authentication requirements"""
    
    def test_create_comment_unauthorized(self):
        """POST /api/comments requires authentication"""
        # Get an article ID
        articles_response = requests.get(f"{BASE_URL}/api/articles?limit=1")
        
        if articles_response.status_code != 200:
            pytest.skip("Could not fetch articles")
        
        articles = articles_response.json()
        if not articles or len(articles) == 0:
            pytest.skip("No articles available")
        
        article_id = articles[0].get("id")
        
        # Try to create comment without auth
        response = requests.post(
            f"{BASE_URL}/api/comments",
            json={
                "article_id": article_id,
                "content": "Test comment"
            }
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        print(f"✅ Correctly requires authentication for posting comments")
    
    def test_like_comment_unauthorized(self):
        """POST /api/comments/{id}/like requires authentication"""
        response = requests.post(f"{BASE_URL}/api/comments/fake-comment-id/like")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        print(f"✅ Correctly requires authentication for liking comments")
    
    def test_delete_comment_unauthorized(self):
        """DELETE /api/comments/{id} requires authentication"""
        response = requests.delete(f"{BASE_URL}/api/comments/fake-comment-id")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        print(f"✅ Correctly requires authentication for deleting comments")
    
    def test_get_me_unauthorized(self):
        """GET /api/comments/me requires authentication"""
        response = requests.get(f"{BASE_URL}/api/comments/me")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        print(f"✅ Correctly requires authentication for /me endpoint")


class TestArticleContent:
    """Test article content for reading time calculation"""
    
    def test_articles_have_content(self):
        """Articles should have content for reading time calculation"""
        response = requests.get(f"{BASE_URL}/api/articles?limit=5")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        articles = response.json()
        assert len(articles) > 0, "Should have articles"
        
        for article in articles:
            assert "content" in article, "Article should have content"
            content = article.get("content", "")
            assert len(content) > 50, f"Article content should be substantial, got {len(content)} chars"
            
            # Calculate reading time (same logic as frontend)
            words = len(content.split())
            reading_time = max(1, words // 200)
            
            print(f"  - '{article.get('title', 'Unknown')[:40]}...' - {words} words, ~{reading_time} min read")
        
        print(f"✅ All {len(articles)} articles have content for reading time calculation")


class TestCommentsLogout:
    """Test comments logout endpoint"""
    
    def test_logout_without_token(self):
        """POST /api/comments/logout works without token"""
        response = requests.post(f"{BASE_URL}/api/comments/logout")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("success") == True
        
        print(f"✅ Logout works without token")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

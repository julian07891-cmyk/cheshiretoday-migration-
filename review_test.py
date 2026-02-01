#!/usr/bin/env python3
"""
Review Request Testing Script
Tests the specific items mentioned in the review request
"""

import requests
import json
import sys

# Get backend URL from frontend .env
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading frontend .env: {e}")
        return "http://localhost:8001"

BASE_URL = get_backend_url()
API_URL = f"{BASE_URL}/api"

def test_article_count_verification():
    """Test 1: Article Count Verification (20 articles per refresh)"""
    print("\n📊 TEST 1: ARTICLE COUNT VERIFICATION (20 ARTICLES PER REFRESH)")
    print("=" * 80)
    
    try:
        print(f"🌐 Calling: POST {API_URL}/admin/clear-and-refresh")
        print("   Expected: Should import exactly 20 articles")
        
        response = requests.post(f"{API_URL}/admin/clear-and-refresh", 
                               timeout=180,
                               headers={'Content-Type': 'application/json'})
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📄 Response: {json.dumps(result, indent=2)}")
            
            # Check if response contains 'imported: 20'
            imported = result.get('imported', result.get('imported_articles', 0))
            
            print(f"📈 Articles imported: {imported}")
            
            if imported == 20:
                print(f"✅ SUCCESS: Exactly 20 articles imported as expected")
                return True
            else:
                print(f"❌ FAILED: Expected 20 articles, got {imported}")
                return False
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return False

def test_sports_article_limit():
    """Test 2: Sports Article Limit (max 3 per refresh)"""
    print("\n⚽ TEST 2: SPORTS ARTICLE LIMIT (MAX 3 PER REFRESH)")
    print("=" * 80)
    
    try:
        print(f"🌐 Calling: GET {API_URL}/articles?limit=100")
        print("   Expected: ≤3 sports articles after refresh")
        
        response = requests.get(f"{API_URL}/articles?limit=100", timeout=30)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            articles = response.json()
            
            if not isinstance(articles, list):
                print(f"❌ FAILED: Expected list, got: {type(articles)}")
                return False
            
            # Count articles with category="Sports"
            sports_articles = [a for a in articles if a.get('category') == 'Sports']
            sports_count = len(sports_articles)
            
            print(f"📈 Total articles found: {len(articles)}")
            print(f"⚽ Sports articles found: {sports_count}")
            
            # Show sports articles
            if sports_articles:
                print(f"📋 Sports articles:")
                for i, article in enumerate(sports_articles, 1):
                    title = article.get('title', 'Unknown Title')
                    print(f"   {i}. {title}")
            
            if sports_count <= 3:
                print(f"✅ SUCCESS: Sports articles ({sports_count}) ≤ 3 limit")
                return True
            else:
                print(f"❌ FAILED: Sports articles ({sports_count}) > 3 limit")
                return False
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return False

def test_warrington_guardian_rss():
    """Test 3: Warrington Guardian RSS Feed Fix"""
    print("\n📰 TEST 3: WARRINGTON GUARDIAN RSS FEED FIX")
    print("=" * 80)
    
    try:
        print(f"🌐 Calling: GET {API_URL}/real-news/local?limit=50")
        print("   Expected: Response should include articles with source='Warrington Guardian'")
        
        response = requests.get(f"{API_URL}/real-news/local?limit=50", timeout=30)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📄 Response structure: {list(result.keys()) if isinstance(result, dict) else type(result)}")
            
            articles = []
            if isinstance(result, dict) and 'articles' in result:
                articles = result['articles']
            elif isinstance(result, list):
                articles = result
            
            if not articles:
                print(f"⚠️  No articles returned")
                return False
            
            print(f"📈 Total local articles found: {len(articles)}")
            
            # Look for Warrington Guardian articles
            warrington_articles = [a for a in articles if 'warrington guardian' in a.get('source', '').lower()]
            warrington_count = len(warrington_articles)
            
            print(f"📰 Warrington Guardian articles found: {warrington_count}")
            
            # Show all unique sources
            sources = set()
            for article in articles:
                source = article.get('source', 'Unknown')
                sources.add(source)
            
            print(f"📋 All sources found:")
            for source in sorted(sources):
                count = len([a for a in articles if a.get('source') == source])
                print(f"   • {source}: {count} articles")
            
            # Show Warrington Guardian articles if found
            if warrington_articles:
                print(f"📋 Warrington Guardian articles:")
                for i, article in enumerate(warrington_articles[:3], 1):  # Show first 3
                    title = article.get('title', 'Unknown Title')
                    print(f"   {i}. {title}")
            
            if warrington_count > 0:
                print(f"✅ SUCCESS: Warrington Guardian RSS feed working")
                return True
            else:
                print(f"❌ FAILED: No Warrington Guardian articles found")
                return False
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return False

def test_local_news_sources():
    """Test 4: Local News Sources Verification"""
    print("\n🏘️  TEST 4: LOCAL NEWS SOURCES VERIFICATION")
    print("=" * 80)
    
    expected_sources = ['Cheshire Live', 'Warrington Guardian', 'Manchester Evening News']
    
    try:
        print(f"🌐 Calling: GET {API_URL}/real-news/local?limit=50")
        print(f"   Expected sources: {', '.join(expected_sources)}")
        
        response = requests.get(f"{API_URL}/real-news/local?limit=50", timeout=30)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            articles = []
            if isinstance(result, dict) and 'articles' in result:
                articles = result['articles']
            elif isinstance(result, list):
                articles = result
            
            if not articles:
                print(f"⚠️  No articles returned")
                return False
            
            print(f"📈 Total local articles found: {len(articles)}")
            
            # Check for each expected source
            found_sources = []
            missing_sources = []
            
            for expected_source in expected_sources:
                source_articles = [a for a in articles if expected_source.lower() in a.get('source', '').lower()]
                if source_articles:
                    found_sources.append(expected_source)
                    print(f"✅ {expected_source}: {len(source_articles)} articles found")
                else:
                    missing_sources.append(expected_source)
                    print(f"❌ {expected_source}: No articles found")
            
            # Show all unique sources found
            all_sources = set()
            for article in articles:
                source = article.get('source', 'Unknown')
                all_sources.add(source)
            
            print(f"\n📋 All sources in response:")
            for source in sorted(all_sources):
                count = len([a for a in articles if a.get('source') == source])
                print(f"   • {source}: {count} articles")
            
            # Test result
            if len(found_sources) >= 2:  # Allow some flexibility
                print(f"\n✅ SUCCESS: Multiple local sources verified ({len(found_sources)}/{len(expected_sources)})")
                return True
            else:
                print(f"\n❌ FAILED: Insufficient local sources ({len(found_sources)}/{len(expected_sources)})")
                return False
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return False

def test_content_generation():
    """Test 5: Content Generation with Perplexity (>500 chars)"""
    print("\n📝 TEST 5: CONTENT GENERATION WITH PERPLEXITY (>500 CHARS)")
    print("=" * 80)
    
    try:
        print(f"🌐 Calling: GET {API_URL}/articles")
        print("   Expected: Articles should have detailed content (>500 chars)")
        
        response = requests.get(f"{API_URL}/articles", timeout=30)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            articles = response.json()
            
            if not isinstance(articles, list) or len(articles) == 0:
                print(f"❌ FAILED: No articles to verify")
                return False
            
            print(f"📈 Total articles found: {len(articles)}")
            
            # Check content length for each article
            detailed_count = 0
            short_count = 0
            
            for i, article in enumerate(articles[:10], 1):  # Check first 10 articles
                title = article.get('title', 'Unknown Title')
                content = article.get('content', '')
                content_length = len(content)
                
                is_detailed = content_length > 500
                status = "✅ DETAILED" if is_detailed else "❌ SHORT"
                
                print(f"{i:2d}. {title[:50]}...")
                print(f"    Content length: {content_length} chars - {status}")
                
                if is_detailed:
                    detailed_count += 1
                else:
                    short_count += 1
            
            # Calculate success rate
            total_checked = min(10, len(articles))
            success_rate = (detailed_count / total_checked) * 100 if total_checked > 0 else 0
            
            print(f"\n📊 CONTENT LENGTH ANALYSIS:")
            print(f"   📈 Articles checked: {total_checked}")
            print(f"   ✅ Detailed content (>500 chars): {detailed_count}")
            print(f"   ❌ Short content (≤500 chars): {short_count}")
            print(f"   📊 Success rate: {success_rate:.1f}%")
            
            # Test result - expect at least 80% to have detailed content
            if success_rate >= 80:
                print(f"\n✅ SUCCESS: Most articles have detailed content ({success_rate:.1f}%)")
                return True
            else:
                print(f"\n❌ FAILED: Too many articles with short content ({success_rate:.1f}%)")
                return False
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return False

def main():
    """Run all review request tests"""
    print(f"🚀 CHESHIRE TODAY NEWS WEBSITE - REVIEW REQUEST TESTING")
    print(f"📍 Testing API at: {API_URL}")
    print(f"🎯 Focus: Recent fixes verification")
    print("=" * 80)
    
    tests = [
        ("Article Count Verification (20 per refresh)", test_article_count_verification),
        ("Sports Article Limit (max 3)", test_sports_article_limit),
        ("Warrington Guardian RSS Feed", test_warrington_guardian_rss),
        ("Local News Sources Verification", test_local_news_sources),
        ("Content Generation (>500 chars)", test_content_generation),
    ]
    
    passed = 0
    failed = 0
    failed_tests = []
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {test_name}: PASSED")
            else:
                failed += 1
                failed_tests.append(test_name)
                print(f"\n❌ {test_name}: FAILED")
        except Exception as e:
            failed += 1
            failed_tests.append(f"{test_name} (Exception: {str(e)})")
            print(f"\n❌ {test_name}: FAILED - Exception: {str(e)}")
    
    # Print summary
    print("\n" + "=" * 80)
    print(f"📊 REVIEW REQUEST TEST SUMMARY")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed_tests:
        print(f"\n🔍 FAILED TESTS:")
        for test in failed_tests:
            print(f"   • {test}")
    
    success_rate = (passed / (passed + failed)) * 100 if (passed + failed) > 0 else 0
    print(f"\n📈 Success Rate: {success_rate:.1f}%")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
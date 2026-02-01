#!/usr/bin/env python3
"""
Cheshire Today - Duplicate Images Analysis
Specific test to check for duplicate images across ALL articles on production
As requested in the review request
"""

import requests
import json
from collections import defaultdict
import sys

# Production URL as specified in review request
PRODUCTION_URL = "https://cheshiretoday.co.uk"
API_URL = f"{PRODUCTION_URL}/api"

def extract_image_identifier(image_url):
    """Extract unique identifier from image URL for duplicate detection"""
    if not image_url:
        return "no_image"
    
    # For Unsplash URLs, extract the photo ID
    if 'unsplash.com/photo-' in image_url:
        try:
            # Extract ID from URL like: https://images.unsplash.com/photo-1599974331560-c4d5c209a005
            photo_part = image_url.split('photo-')[1]
            photo_id = photo_part.split('-')[0] if '-' in photo_part else photo_part.split('?')[0]
            return photo_id
        except:
            pass
    
    # For other URLs, use the full URL as identifier
    # Remove query parameters for better matching
    base_url = image_url.split('?')[0]
    return base_url

def main():
    print("🔍 CHESHIRE TODAY - DUPLICATE IMAGES ANALYSIS")
    print("=" * 60)
    print(f"🌐 Production URL: {PRODUCTION_URL}")
    print(f"📡 API Endpoint: {API_URL}")
    print()
    
    try:
        # Step 1: Fetch all articles from production
        print("📥 Step 1: Fetching all articles from production...")
        response = requests.get(f"{API_URL}/articles?skip=0&limit=100", timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch articles: HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
        
        articles = response.json()
        
        if not isinstance(articles, list):
            print(f"❌ Expected list of articles, got: {type(articles)}")
            return False
        
        print(f"✅ Successfully fetched {len(articles)} articles")
        print()
        
        # Step 2: Extract image URLs and categorize articles
        print("📊 Step 2: Analyzing images and categories...")
        
        image_usage = defaultdict(list)  # image_id -> list of articles
        category_counts = defaultdict(int)
        articles_with_images = 0
        articles_without_images = 0
        
        for article in articles:
            # Count categories
            category = article.get('category', 'Unknown')
            category_counts[category] += 1
            
            # Process images
            image_url = article.get('image', '')
            if image_url:
                articles_with_images += 1
                image_id = extract_image_identifier(image_url)
                
                image_usage[image_id].append({
                    'id': article.get('id', 'Unknown'),
                    'title': article.get('title', 'Unknown Title'),
                    'category': category,
                    'image_url': image_url
                })
            else:
                articles_without_images += 1
        
        print(f"   📰 Articles with images: {articles_with_images}")
        print(f"   🚫 Articles without images: {articles_without_images}")
        print()
        
        # Step 3: Identify duplicates
        print("🔍 Step 3: Identifying duplicate images...")
        
        duplicates = {}
        unique_images = 0
        
        for image_id, article_list in image_usage.items():
            if len(article_list) > 1:
                duplicates[image_id] = article_list
            else:
                unique_images += 1
        
        # Calculate articles needing new images (all but one per duplicate)
        articles_needing_new_images = sum(len(articles) - 1 for articles in duplicates.values())
        
        print(f"   🖼️  Total unique images: {len(image_usage)}")
        print(f"   ✅ Images used only once: {unique_images}")
        print(f"   🔄 Duplicate images found: {len(duplicates)}")
        print(f"   🛠️  Articles needing new images: {articles_needing_new_images}")
        print()
        
        # Step 4: Summary as requested
        print("📋 SUMMARY:")
        print(f"   📈 Total articles checked: {len(articles)}")
        print(f"   🖼️  Total unique images: {len(image_usage)}")
        print(f"   🔄 Number of duplicate images found: {len(duplicates)}")
        print(f"   🛠️  How many articles need new images: {articles_needing_new_images}")
        print()
        
        # Step 5: Category breakdown
        print("📊 ARTICLES BY CATEGORY:")
        for category, count in sorted(category_counts.items()):
            print(f"   • {category}: {count} articles")
        print()
        
        # Step 6: Detailed duplicate list (top 5 most duplicated)
        if duplicates:
            print("🔍 TOP 5 MOST DUPLICATED IMAGES:")
            sorted_duplicates = sorted(duplicates.items(), 
                                     key=lambda x: len(x[1]), 
                                     reverse=True)
            
            for i, (image_id, article_list) in enumerate(sorted_duplicates[:5], 1):
                usage_count = len(article_list)
                sample_url = article_list[0]['image_url']
                
                print(f"\n{i}. Image ID: {image_id}")
                print(f"   Image URL: {sample_url}")
                print(f"   Used {usage_count} times")
                print(f"   Articles using this image:")
                
                for j, article in enumerate(article_list, 1):
                    print(f"      {j}. [{article['category']}] {article['title']}")
            
            # Show complete list if there are more duplicates
            if len(duplicates) > 5:
                print(f"\n📝 COMPLETE LIST OF ALL {len(duplicates)} DUPLICATE IMAGES:")
                for image_id, article_list in sorted_duplicates:
                    usage_count = len(article_list)
                    categories = [a['category'] for a in article_list]
                    print(f"   • {image_id}: used {usage_count} times (categories: {', '.join(set(categories))})")
        else:
            print("✅ NO DUPLICATE IMAGES FOUND!")
            print("   All articles have unique images.")
        
        print()
        
        # Final result
        if len(duplicates) == 0:
            print("🎉 RESULT: SUCCESS - No duplicate images found!")
            return True
        else:
            print(f"⚠️  RESULT: {len(duplicates)} duplicate images found affecting {articles_needing_new_images} articles")
            print("   Recommendation: Update duplicate images to ensure uniqueness")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
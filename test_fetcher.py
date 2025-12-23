#!/usr/bin/env python3
"""
Test script for the Zhihu fetcher.
This script can be run manually to test if the scraper is working.
"""

import json
from fetcher import fetch

def test_fetch():
    """Test the fetch function and print results."""
    print("=" * 60)
    print("Testing Zhihu Fetcher")
    print("=" * 60)
    
    try:
        data = fetch()
        
        print(f"\n✓ Successfully fetched {len(data)} items\n")
        
        # Display first 3 items as a sample
        print("Sample items:")
        print("-" * 60)
        for i, item in enumerate(data[:3], 1):
            print(f"\n{i}. {item['title']}")
            print(f"   Link: {item['link']}")
            print(f"   Hot: {item['hot']}")
            desc = item.get('description') or ''
            if desc:
                desc = desc[:100] + "..." if len(desc) > 100 else desc
                print(f"   Description: {desc}")
        
        print("\n" + "=" * 60)
        print(f"✓ Test passed! Fetched {len(data)} items successfully.")
        print("=" * 60)
        
        # Validate data structure
        errors = []
        for i, item in enumerate(data, 1):
            if not item.get('link'):
                errors.append(f"Item {i}: Missing link")
            if not item.get('title'):
                errors.append(f"Item {i}: Missing title")
            if not item.get('hot'):
                errors.append(f"Item {i}: Missing hot value")
        
        if errors:
            print("\n⚠ Warnings:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(errors) > 5:
                print(f"  ... and {len(errors) - 5} more")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error:")
        print(f"  {type(e).__name__}: {e}")
        print("\n" + "=" * 60)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_fetch()
    exit(0 if success else 1)

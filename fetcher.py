import requests
from bs4 import BeautifulSoup

headers = {
    "authority": "www.zhihu.com",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    "referer": "https://www.zhihu.com/",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1"
}


def fetch_by_html():
    try:
        res = requests.get("https://www.zhihu.com/hot", headers=headers, timeout=10)
        if res.status_code != 200:
            print(f"HTML request failed with status code: {res.status_code}")
            raise Exception(f"HTTP status code {res.status_code}")
        
        html = res.text
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try to find the main tag
        main_tags = soup.findAll('main')
        if not main_tags:
            print("No <main> tag found in HTML")
            raise Exception("No main tag found")
        
        main_tag = main_tags[0]
        list_tag = None
        
        # Find the first div child
        for child in main_tag.children:
            if child.name == 'div':
                list_tag = child
                break
        
        if list_tag is None:
            print("Failed to find list tag (div under main)")
            raise Exception("No list div found")
        
        results = []
        items_found = 0
        
        for item in list_tag.children:
            try:
                if item.name != "a":
                    continue
                
                items_found += 1
                link = item.attrs.get('href', '')
                if not link:
                    print(f"Item {items_found}: No href found")
                    continue
                
                texts = []
                is_second_div = False
                
                for tag in item.children:
                    if tag.name == 'div':
                        if is_second_div:
                            for sub_tag in tag.children:
                                if sub_tag.name in ['div', 'h1', 'h2']:
                                    text = sub_tag.text.strip()
                                    if text:
                                        texts.append(text)
                        else:
                            is_second_div = True
                
                if len(texts) >= 2:
                    if len(texts) == 2:
                        result = {
                            "link": link,
                            "title": texts[0],
                            "description": "",
                            "hot": texts[1]
                        }
                    else:
                        result = {
                            "link": link,
                            "title": texts[0],
                            "description": texts[1],
                            "hot": texts[2] if len(texts) > 2 else ""
                        }
                    results.append(result)
                else:
                    print(f"Item {items_found}: Only found {len(texts)} text elements")
                    
            except Exception as e:
                print(f"Error parsing HTML item {items_found}: {e}")
                continue
        
        if len(results) == 0:
            print(f"No results parsed from HTML (found {items_found} items)")
            raise Exception("No items successfully parsed from HTML")
        
        print(f"Successfully parsed {len(results)} items from HTML")
        return results
        
    except Exception as e:
        print(f"fetch_by_html error: {e}")
        raise


def fetch_by_api():
    try:
        res = requests.get("https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total", headers=headers, timeout=10)
        if res.status_code != 200:
            print(f"API request failed with status code: {res.status_code}")
            raise Exception(f"API returned status code {res.status_code}")
        
        data = res.json()
        
        # Check if response has expected structure
        if 'data' not in data:
            print(f"Unexpected API response structure: {list(data.keys())}")
            raise Exception("API response missing 'data' field")
        
        results = []
        for item in data['data']:
            try:
                # Handle both question and answer types
                target = item.get('target', {})
                item_id = target.get('id', '')
                
                if not item_id:
                    print(f"Warning: Empty item_id, skipping item")
                    continue
                
                # Determine the link based on the type
                target_type = target.get('type', 'question')
                if target_type == 'answer':
                    question_id = target.get('question', {}).get('id', '')
                    if question_id:
                        link = f"https://www.zhihu.com/question/{question_id}/answer/{item_id}"
                    else:
                        link = f"https://www.zhihu.com/question/{item_id}"
                else:
                    link = f"https://www.zhihu.com/question/{item_id}"
                
                # Get title, preferring target.title over question.title
                title = target.get('title')
                if not title:
                    title = target.get('question', {}).get('title', 'Unknown')
                
                result = {
                    "link": link,
                    "title": title,
                    "description": target.get('excerpt', ''),
                    "hot": item.get('detail_text', '')
                }
                results.append(result)
            except Exception as e:
                print(f"Error parsing API item: {e}")
                continue
        
        if len(results) == 0:
            raise Exception("No items parsed from API response")
        
        return results
    except Exception as e:
        print(f"fetch_by_api error: {e}")
        raise


def fetch():
    # Try API first (more reliable)
    print("Attempting to fetch from API...")
    try:
        data = fetch_by_api()
        print(f"Successfully fetched {len(data)} items from API")
        return data
    except Exception as e:
        print(f"API fetch failed: {e}")
    
    # Fallback to HTML parsing
    print("Attempting to fetch from HTML...")
    try:
        data = fetch_by_html()
        print(f"Successfully fetched {len(data)} items from HTML")
        return data
    except Exception as e:
        print(f"HTML fetch failed: {e}")
        raise Exception("Both API and HTML fetching failed")

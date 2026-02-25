import requests
from bs4 import BeautifulSoup
import time

# Updated headers to better mimic a real browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0"
}


def create_session():
    """Create a session with cookies by visiting the main page first."""
    session = requests.Session()
    session.headers.update(headers)

    try:
        # Visit main page first to get cookies
        print("Initializing session by visiting zhihu.com...")
        response = session.get("https://www.zhihu.com", timeout=15, allow_redirects=True)
        print(f"Session initialized with status code: {response.status_code}")
        # Add a small delay to mimic human behavior
        time.sleep(1)
        return session
    except Exception as e:
        print(f"Warning: Failed to initialize session: {e}")
        return session


def fetch_by_html():
    try:
        # Create a session with cookies
        session = create_session()

        # Make the request to hot page
        res = session.get("https://www.zhihu.com/hot", timeout=15, allow_redirects=True)
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
        # Create a session with cookies
        session = create_session()

        # Update headers for API request
        api_headers = headers.copy()
        api_headers.update({
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.zhihu.com/hot",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        })

        res = session.get("https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total",
                         headers=api_headers, timeout=15, allow_redirects=True)
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
    # Try API first (more reliable when it works)
    print("Attempting to fetch from API...")
    try:
        data = fetch_by_api()
        print(f"Successfully fetched {len(data)} items from API")
        return data
    except Exception as e:
        print(f"API fetch failed: {e}")

    # Add a delay before trying HTML parsing
    print("Waiting 2 seconds before trying HTML parsing...")
    time.sleep(2)

    # Fallback to HTML parsing
    print("Attempting to fetch from HTML...")
    try:
        data = fetch_by_html()
        print(f"Successfully fetched {len(data)} items from HTML")
        return data
    except Exception as e:
        print(f"HTML fetch failed: {e}")
        raise Exception("Both API and HTML fetching failed")

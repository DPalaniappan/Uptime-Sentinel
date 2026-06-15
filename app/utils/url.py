from urllib.parse import urlparse, urlunparse

def normalize_url(url_string: str) -> str:
    if not url_string:
        return ""
        
    # 1. Clean whitespace and lowercase the core domain
    clean_url = url_string.strip()
    
    if not clean_url.startswith(('http://', 'https://')):
        clean_url = 'https://' + clean_url

    try:
        parsed = urlparse(clean_url)
        
        # Lowercase only the hostname (e.g., GOOGLE.COM -> google.com)
        # We leave the path casing alone because some servers are case-sensitive!
        hostname = parsed.netloc.lower()
        
        # 2. Extract the path and strip ONLY trailing junk punctuation characters
        # This keeps '/about', '/blog/posts/12', but kills accidental trailing commas/slashes
        path = parsed.path.rstrip(',. ')
        
        # Normalize trailing slashes: 'google.com/' becomes 'google.com'
        if path == '/':
            path = ""

        # 3. Rebuild the clean URL
        return urlunparse((
            parsed.scheme,
            hostname,
            path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
    except Exception:
        return url_string

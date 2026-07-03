import logging
import urllib.parse
import xml.etree.ElementTree as ET
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TrendFinder")

class TrendFinder:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def fetch_rss_feed(self, url):
        """Fetches and parses an RSS feed."""
        try:
            logger.info(f"Fetching RSS feed: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return ET.fromstring(response.content)
            else:
                logger.warning(f"Failed to fetch {url}, status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching RSS feed {url}: {e}")
        return None

    def get_google_trends(self):
        """Fetches Google Trends daily search trends for India."""
        url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=IN"
        root = self.fetch_rss_feed(url)
        trends = []
        if root is not None:
            # Google Trends RSS uses custom namespaces
            namespaces = {
                'ht': 'https://trends.google.com/trends/trendingsearches/daily'
            }
            for item in root.findall('.//item'):
                title = item.find('title')
                approx_traffic = item.find('.//ht:approx_traffic', namespaces)
                description = item.find('description')
                
                title_text = title.text if title is not None else ""
                traffic_text = approx_traffic.text if approx_traffic is not None else "Unknown"
                desc_text = description.text if description is not None else ""
                
                # Simple popularity score calculation
                score = 50  # base score
                if "+" in traffic_text:
                    try:
                        num = int(traffic_text.replace("+", "").replace(",", "").strip())
                        score = num // 1000  # e.g., 100k+ -> 100 points
                    except ValueError:
                        pass
                
                trends.append({
                    "title": title_text,
                    "description": desc_text,
                    "traffic": traffic_text,
                    "source": "Google Trends",
                    "score": score
                })
        return trends

    def get_reddit_trends(self):
        """Fetches trends from technology, AI, and futurology subreddits."""
        subreddits = ["technology", "artificial", "singularity", "futurology", "chatgpt"]
        trends = []
        namespaces = {'atom': 'http://www.w3.org/2005/Atom'}
        
        for sub in subreddits:
            url = f"https://www.reddit.com/r/{sub}/.rss"
            root = self.fetch_rss_feed(url)
            if root is not None:
                for entry in root.findall('.//atom:entry', namespaces):
                    title = entry.find('atom:title', namespaces)
                    category = entry.find('atom:category', namespaces)
                    
                    title_text = title.text if title is not None else ""
                    cat_text = category.attrib.get('label', '') if category is not None else "General"
                    
                    # Score tech and AI channels higher to prioritize them
                    score = 45 if sub in ["technology", "artificial", "singularity", "chatgpt"] else 30
                    
                    trends.append({
                        "title": title_text,
                        "description": f"Trending in Reddit r/{sub} (Category: {cat_text})",
                        "traffic": f"High r/{sub} Activity",
                        "source": f"Reddit r/{sub}",
                        "score": score
                    })
        return trends

    def get_news_trends(self):
        """Fetches global technology news from BBC Technology RSS."""
        url = "http://feeds.bbci.co.uk/news/technology/rss.xml"
        root = self.fetch_rss_feed(url)
        trends = []
        if root is not None:
            for item in root.findall('.//item'):
                title = item.find('title')
                description = item.find('description')
                
                title_text = title.text if title is not None else ""
                desc_text = description.text if description is not None else ""
                
                trends.append({
                    "title": title_text,
                    "description": desc_text,
                    "traffic": "Breaking Tech News",
                    "source": "BBC Tech News",
                    "score": 20  # Base news score
                })
        return trends

    def get_combined_trends(self):
        """Fetches trends from all sources and returns them sorted by popularity score."""
        all_trends = []
        
        # Google Trends
        try:
            google_trends = self.get_google_trends()
            all_trends.extend(google_trends)
        except Exception as e:
            logger.error(f"Failed to retrieve Google Trends: {e}")
            
        # Reddit Trends
        try:
            reddit_trends = self.get_reddit_trends()
            all_trends.extend(reddit_trends)
        except Exception as e:
            logger.error(f"Failed to retrieve Reddit Trends: {e}")

        # News Trends
        try:
            news_trends = self.get_news_trends()
            all_trends.extend(news_trends)
        except Exception as e:
            logger.error(f"Failed to retrieve News Trends: {e}")

        # Remove empty titles and sort by score descending
        valid_trends = [t for t in all_trends if t["title"].strip()]
        sorted_trends = sorted(valid_trends, key=lambda x: x["score"], reverse=True)
        
        # De-duplicate items with similar titles
        seen = set()
        deduped = []
        for item in sorted_trends:
            norm_title = "".join(c for c in item["title"].lower() if c.isalnum())
            if norm_title not in seen:
                seen.add(norm_title)
                deduped.append(item)
                
        return deduped

if __name__ == "__main__":
    finder = TrendFinder()
    trends = finder.get_combined_trends()
    print(f"Discovered {len(trends)} trending topics:")
    for idx, t in enumerate(trends[:10], 1):
        print(f"{idx}. [{t['source']}] {t['title']} (Score: {t['score']}, Traffic: {t['traffic']})")

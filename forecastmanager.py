import requests
import re
import html
import global_vars
import xml.etree.ElementTree as ET

def retrieve_forecast():
    url = "https://api.weather.gov/gridpoints/MLB/26,68/forecast?units=us"
    
    try:
        r = requests.get(url, headers=global_vars.globalRequestHeader)  # keep as Response object
        if r.status_code != 200:
            print(f"⚠️ API returned status {r.status_code}: {r.text[:200]}")
            return []

        try:
            return r.json()
        except requests.exceptions.JSONDecodeError:
            print("⚠️ Response was not valid JSON!")
            print(f"Response text: {r.text[:200]}")  # Log first 200 chars
            return []
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Request failed: {e}")
        return []
    
def fetch_forecast():
    r = retrieve_forecast()
    
    if not r or "properties" not in r:
        return []
    
    forecastInfo = []
    props = r["properties"]
    periods = props["periods"]
    
    forecastInfo.append(periods[0])
    forecastInfo.append(periods[1])
    forecastInfo.append(periods[2])
    forecastInfo.append(periods[3])
    
    return forecastInfo

def format_nhc_html(html_text):
    """
    Converts NHC HTML text to Discord-friendly markdown.
    - <br> becomes newlines
    - Remove other HTML tags
    - Unescape HTML entities
    """

    # Replace <br> and <br/> with newlines
    text = re.sub(r'<br\s*/?>', '\n', html_text, flags=re.IGNORECASE)
    # Remove all other HTML tags
    text = re.sub(r'<.*?>', '', text)
    # Unescape HTML entities
    text = html.unescape(text)
    # Remove leading/trailing whitespace and collapse multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text

def get_hurricane_forecast(xml_content=None):
    """
    Fetches the Atlantic 7-day outlook image URL and discussion text from the NHC RSS feed.
    If xml_content is provided, parses from that string instead of fetching from the web.
    Returns (image_url, formatted_discussion_text)
    """
    rss_url = "https://www.nhc.noaa.gov/gtwo.xml"
    if xml_content is None:
        response = requests.get(rss_url)
        response.raise_for_status()
        xml_content = response.content

    root = ET.fromstring(xml_content)

    image_url = None
    discussion_text = None

    # Find the Atlantic Outlook item
    for item in root.findall(".//item"):
        title = item.findtext("title")
        if title and "Atlantic Outlook" in title:
            description = item.findtext("description")
            if description:
                # Extract the 7-day image URL from the description
                match = re.search(r'<img\s+src="([^"]+)"\s+alt="Atlantic 7-Day Graphical Outlook Image"', description)
                if match:
                    image_url = match.group(1)
                # Extract the discussion text (strip HTML tags)
                # The discussion is inside <div class='textproduct'>...</div>
                discussion_match = re.search(
                    r"<div class='textproduct'>(.*?)</div>", description, re.DOTALL
                )
                if discussion_match:
                    discussion_html = discussion_match.group(1)
                    # Format the HTML text for Discord
                    discussion_text = format_nhc_html(discussion_html)
            break
    return image_url, discussion_text
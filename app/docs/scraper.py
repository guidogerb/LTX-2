import os
import argparse
import requests
import hashlib
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from markdownify import markdownify as md


def get_filename_from_url(url, content):
    parsed = urlparse(url)
    original_name = os.path.basename(parsed.path)
    name, ext = os.path.splitext(original_name)
    if not ext:
        ext = ".jpg"
    file_hash = hashlib.md5(content).hexdigest()[:8]
    safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()
    if not safe_name:
        safe_name = "image"
    return f"{safe_name}_{file_hash}{ext}"


def download_resource(url, base_url, media_folder):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    try:
        abs_url = urljoin(base_url, url)
        response = requests.get(abs_url, headers=headers, timeout=10)
        response.raise_for_status()
        filename = get_filename_from_url(abs_url, response.content)
        file_path = os.path.join(media_folder, filename)
        with open(file_path, 'wb') as f:
            f.write(response.content)
        return filename
    except Exception as e:
        # Silently fail on bad images or print warning
        return None


def scrape_page_to_markdown(url, output_folder="output"):
    media_folder_name = "media"
    media_path = os.path.join(output_folder, media_folder_name)
    os.makedirs(media_path, exist_ok=True)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }

    print(f"Fetching {url}...")
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page: {e}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')

    for tag in soup(['script', 'style', 'noscript', 'iframe', 'svg']):
        tag.decompose()

    print("Processing images...")
    images = soup.find_all('img')

    for img in images:
        src = img.get('src')
        if not src:
            continue
        local_filename = download_resource(src, url, media_path)
        if local_filename:
            img['src'] = f"{media_folder_name}/{local_filename}"
            if img.has_attr('srcset'):
                del img['srcset']

    print("Converting to Markdown...")
    markdown_content = md(str(soup), heading_style="ATX")

    page_title = soup.title.string if soup.title else "scraped_page"
    safe_title = "".join([c for c in page_title if c.isalnum() or c in (' ', '-', '_')]).strip()
    output_filename = f"{safe_title}.md"
    output_path = os.path.join(output_folder, output_filename)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"Success! Saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape a website to Markdown with local images.")
    parser.add_argument("url", help="The URL of the website to scrape")
    parser.add_argument("-o", "--output", default="output", help="The output folder (default: output)")

    args = parser.parse_args()

    scrape_page_to_markdown(args.url, args.output)
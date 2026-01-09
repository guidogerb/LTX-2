***

# Web Page to Markdown Scraper

A Python 3.12 application that scrapes a single webpage, downloads all associated images to a local folder, and converts the page content into a clean, offline-ready Markdown file.

## Features

*   **Markdown Conversion:** Converts HTML content to formatted Markdown (ATX style headers).
*   **Offline Media:** Automatically finds, downloads, and saves images to a local `media/` directory.
*   **Link Rewriting:** Updates image links in the Markdown to point to the downloaded local files.
*   **Smart Filenames:** Uses content hashing to prevent duplicate files and ensures safe filenames.
*   **Cleanup:** Automatically strips `<script>`, `<style>`, `<iframe`, and other non-content tags before conversion.

## Prerequisites

*   **Python 3.12** or higher.
*   The following Python libraries:
    *   `requests`
    *   `beautifulsoup4`
    *   `markdownify`

## Installation

1.  **Clone or Download** the repository to your local machine.
2.  **Install dependencies** using pip:

```bash
pip install requests beautifulsoup4 markdownify
```

## Usage

Run the script from your terminal using the following syntax:

```bash
python scraper.py [URL] [OPTIONS]
```

### Arguments

| Argument | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `url` | The full URL of the webpage you want to scrape. | **Yes** | N/A |
| `-o`, `--output` | The directory where files will be saved. | No | `./output` |

### Examples

**1. Basic Usage:**
Scrape a page and save it to the default `output` folder:

```bash
python scraper.py https://en.wikipedia.org/wiki/Python_(programming_language)
```

**2. Custom Output Location:**
Scrape a page and save it to a specific folder named `my_notes`:

```bash
python scraper.py https://example.com/article -o my_notes
```

## Output Structure

After running the script, your output directory will look like this:

```text
output/
├── media/
│   ├── image_a1b2c3d4.jpg
│   ├── logo_9z8y7x6w.png
│   └── graph_12345678.jpg
└── Page_Title_Here.md
```

Inside `Page_Title_Here.md`, images will be referenced like this:
`![Image Alt Text](media/image_a1b2c3d4.jpg)`

## Limitations

*   **Static Content Only:** This tool uses `requests`, which fetches the HTML source code. It **will not** work well on Single Page Applications (SPAs) or websites that require JavaScript to load the main content (e.g., dynamic React/Vue apps).
*   **Paywalls/Auth:** The script does not handle login authentication or paywalls.


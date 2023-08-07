from flask import Flask, render_template
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from tabulate import tabulate
from pagespeed import calculatePageSpeed
import matplotlib
import matplotlib.pyplot as plt
from tags import extractTags
from meta import extractMeta
import weasyprint
from graph import generateGraph
from drive import uploadToGoogleDrive

tabulate.PRESERVE_WHITESPACE = True

matplotlib.use('agg')

app = Flask(__name__, static_folder='static')


def removeTrailSlash(s):
    if s.endswith('/'):
        s = s[:-1]
    return s


def web_crawler(url, depth=10):
    location = urlparse(url)
    base_url = location.scheme + "://" + location.netloc
    visited_urls = set()
    queue = [(url, 0)]
    results = []

    while queue:
        current_url, current_depth = queue.pop(0)
        formattedUrl = removeTrailSlash(current_url)

        if formattedUrl in visited_urls or current_depth > depth:
            continue

        try:
            response = requests.get(url)
            response.raise_for_status()

            visited_urls.add(formattedUrl)

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract main tags h1 / h2
            tags = extractTags(soup)

            # Extract meta tags
            metadata = extractMeta(soup)

            # Calculate page speed
            loading_time = calculatePageSpeed(url)

            results.append([
                url,
                loading_time,
                tags['h1_headings'],
                tags['h2_headings'],
                metadata
            ])

            links = soup.find_all('a')

            for link in links:
                href = link.get('href')

                if href and href.startswith(('/', base_url)):
                    absolute_url = urljoin(base_url, href)
                    queue.append((absolute_url, current_depth + 1))

        except requests.exceptions.RequestException as e:
            print(f"Error crawling {formattedUrl}: {e}")

    return results


# Start the web crawler from a given URL
parser = argparse.ArgumentParser()
parser.add_argument('--url', dest='url', type=str, help='A given url to crawl')
args = parser.parse_args()


@app.route('/')
def index():
    crawler_results = web_crawler(args.url)

    table = []
    urls = []
    loading_times = []

    print(crawler_results)

    for result in crawler_results:
        table.append([
            f"{result[0]}",
            f"{result[1]:.2f}",
            "\n".join(result[2]),
            "\n".join(result[3]),
            result[4]['description'],
            "\n".join(result[4]['keywords'])
        ])
        urls.append(result[0])
        loading_times.append(result[1])

    chart_file = generateGraph()

    return render_template(
        'index.html',
        table=tabulate(table, tablefmt="html", numalign="right"),
        chart_file=chart_file
    )


@app.route('/generate_report')
def generate_report():
    crawler_results = web_crawler(args.url)

    table = []
    urls = []
    loading_times = []

    for result in crawler_results:
        table.append([
            f"{result[0]}",
            f"{result[1]:.2f}",
            "\n".join(result[2]),
            "\n".join(result[3]),
            result[4]['description'],
            "\n".join(result[4]['keywords'])
        ])
        urls.append(result[0])
        loading_times.append(result[1])

    chart_file = generateGraph()

    # Generate the HTML report
    report_html = render_template('report_template.html', table=tabulate(
        table, tablefmt="html"), chart_file=chart_file)

    # Convert the HTML report to PDF using weasyprint
    report_pdf = weasyprint.HTML(string=report_html).write_pdf()

    # Save the PDF report
    pdf_file = 'static/reports/web_crawler_report.pdf'

    with open(pdf_file, 'wb') as f:
        f.write(report_pdf)

    # Upload the PDF report to Google Drive
    uploadToGoogleDrive(pdf_file)

    return f'Report generated, saved locally, and uploaded to Google Drive'


if __name__ == '__main__':
    app.run(port=8000, debug=True)

import argparse
import os
from urllib.parse import urljoin, urlparse

import matplotlib
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
from celery import Celery
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from tabulate import tabulate

from graph import generateGraph
from meta import extractMeta
from pagespeed import calculatePageSpeed
from tags import extractTags

load_dotenv()

headers = ["URL", "Loading time (s)", "H1 headings",
           "H2 headings", "Description", "Keywords"]

# Start the web crawler from a given URL
parser = argparse.ArgumentParser()
parser.add_argument('--url', dest='url', type=str, help='A given url to crawl')
args, unknown = parser.parse_known_args()


tabulate.PRESERVE_WHITESPACE = True

matplotlib.use('agg')

print(os.getenv('REDIS_SERVER'))

# app is the Flask application object that you will use to run the web server.
# celery is the Celery object that you will use to run the Celery worker.
# Note that the CELERY_BROKER_URL configuration here is set to the Redis server that you're running locally
# on your machine. You can change this to any other message broker that you want to use.
# The celery object takes the application name as an argument and sets the broker argument to the one you specified in the configuration.
# To add the Flask configuration to the Celery configuration, you update it with the conf.update method.
app = Flask(__name__, static_folder='static')
app.config["CELERY_BROKER_URL"] = os.getenv('REDIS_SERVER')
celery = Celery(
    app.name,
    backend='rpc://',
    broker=app.config['CELERY_BROKER_URL']
)
celery.conf.update(app.config)


def remove_trail_slash(s):
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
        (current_url, current_depth) = queue.pop(0)

        print('analysing [' + str(current_depth) + ']: ' + current_url)
        print(visited_urls)

        if current_url in visited_urls or current_depth > depth:
            continue

        try:
            response = requests.get(url)
            response.raise_for_status()

            visited_urls.add(current_url)

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract main tags h1 / h2
            tags = extractTags(soup)

            # Extract meta tags
            metadata = extractMeta(soup)

            # Calculate page speed
            loading_time = calculatePageSpeed(url)

            results.append([
                current_url,
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
            print(f"Error crawling {current_url}: {e}")

    return results


@app.route('/')
def index():
    return render_template('index.html', url=args.url)


@celery.task(bind=True)
def crawl(self, url):
    crawler_results = web_crawler(url)

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

    chart_file = generateGraph(urls, loading_times)
    table = tabulate(table, headers=headers,
                     tablefmt="html", numalign="right")
    total = len(crawler_results)
    average_loading_time = f"{sum(loading_times) / len(loading_times):.2f}"

    response = dict(
        chart_file=chart_file,
        table=table,
        total=total,
        average_loading_time=average_loading_time
    )

    self.update_state(state='SUCCESS', meta={'result': response})

    return response


@app.route('/start_crawling', methods=['POST'])
def start_crawling():
    data = request.get_json()
    task = crawl.apply_async(args=[data['url']])
    return jsonify({'task_id': task.id})


@app.route('/check_progress/<task_id>', methods=['GET'])
def check_progress(task_id):
    task = crawl.AsyncResult(task_id)

    if task.state == 'SUCCESS':
        result = task.result
    else:
        result = None

    return jsonify({"state": task.state, "result": result})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)

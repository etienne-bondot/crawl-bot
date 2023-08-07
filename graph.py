import matplotlib.pyplot as plt


def generateGraph(urls, loading_times, chart_file='static/images/loading_times_chart.png'):
    # Generate the loading time chart
    plt.figure(figsize=(10, 6))
    plt.bar(urls, loading_times, color='skyblue')
    plt.xticks(rotation=45, ha='right')
    plt.ylabel('Loading Time (seconds)')
    plt.xlabel('URL')
    plt.title('Loading Time by URL')
    plt.tight_layout()

    plt.savefig(chart_file)
    plt.close()

    return chart_file

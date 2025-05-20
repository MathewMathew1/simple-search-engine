
import json
import bisect

from decorator import measure_time

k = 1.5
b = 0.75
MINIMUM_LOOKING_SCORE = 1
MAX_RESULTS = 100

def load_articles(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

articles = load_articles('articles.json')

searchWord = "Machine Learning is hard"


def set_average_length(articles):
    total_title_words = 0
    total_content_words = 0
    for article in articles:
        total_title_words += len(article["title"].split())
        total_content_words += len(article["content"].split())

    average_title_length = total_title_words / len(articles)
    average_content_length = total_content_words / len(articles)
    return average_title_length, average_content_length

@measure_time
def lookUpDocuments_basic(search, articles):
    keywords = search.split()
    results = []

    for article in articles:
        title_words = article["title"].split()
        content_words = article["content"].split()

        title_matches = sum(1 for word in title_words if word in keywords)
        content_matches = sum(1 for word in content_words if word in keywords)

        bm25_title = title_matches * (k + 1) / (title_matches + k * (1 - b + b * (len(title_words) / averageTitleLength)))
        bm25_content = content_matches * (k + 1) / (content_matches + k * (1 - b + b * (len(content_words) / averageTitleLength)))

        total_score = bm25_title + bm25_content

        if total_score >= MINIMUM_LOOKING_SCORE:
            results.append({"article": article, "score": total_score})

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:MAX_RESULTS]

@measure_time
def lookUpDocuments_trim_on_insert(search, articles):
    keywords = search.split()
    results = []

    for article in articles:
        title_words = article["title"].split()
        content_words = article["content"].split()

        title_matches = sum(1 for word in title_words if word in keywords)
        content_matches = sum(1 for word in content_words if word in keywords)

        bm25_title = title_matches * (k + 1) / (title_matches + k * (1 - b + b * (len(title_words) / averageTitleLength)))
        bm25_content = content_matches * (k + 1) / (content_matches + k * (1 - b + b * (len(content_words) / averageTitleLength)))

        total_score = bm25_title + bm25_content

        if total_score >= MINIMUM_LOOKING_SCORE:
            results.append({"article": article, "score": total_score})
            if len(results) > MAX_RESULTS:
                results.sort(key=lambda x: x["score"], reverse=True)
                results.pop()  # remove the lowest one

    return results


@measure_time
def lookUpDocuments_bisect(search, articles):
    keywords = search.split()
    results = []  # List of tuples: (score, article)

    for article in articles:
        title_words = article["title"].split()
        content_words = article["content"].split()

        title_matches = sum(1 for word in title_words if word in keywords)
        content_matches = sum(1 for word in content_words if word in keywords)

        bm25_title = title_matches * (k + 1) / (title_matches + k * (1 - b + b * (len(title_words) / averageTitleLength)))
        bm25_content = content_matches * (k + 1) / (content_matches + k * (1 - b + b * (len(content_words) / averageTitleLength)))

        total_score = bm25_title + bm25_content

        if total_score >= MINIMUM_LOOKING_SCORE:
            scores = [x[0] for x in results]
            idx = bisect.bisect_left(scores, total_score)
            results.insert(idx, (total_score, article))
            if len(results) > MAX_RESULTS:
                results.pop(0)  # remove the lowest (at start)

    # Reverse to make highest score first
    results.reverse()
    return [{"score": score, "article": article} for score, article in results]




averageTitleLength, averageWordsLength = set_average_length(articles)
print(len(lookUpDocuments_basic("Machine Learning is hard", articles)))
print(len(lookUpDocuments_bisect("Machine Learning is hard", articles)))
print(len(lookUpDocuments_trim_on_insert("Machine Learning is hard", articles)))
#print(lookUpDocuments("Bro this is wild", articles))
#print(lookUpDocuments("I like Django, movie not framework", articles))
#print(lookUpDocuments("I like Django", articles))
       
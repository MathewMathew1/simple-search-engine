
import json
import bisect
from multiprocessing import Pool, cpu_count
import math
from decorator import measure_time

k = 1.5
b = 0.75
MINIMUM_LOOKING_SCORE = 1
MAX_RESULTS = 100

def load_articles(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)



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


def score_articles_chunk(args):
    search, articles_chunk, averageTitleLength, averageWordsLength, k, b, MINIMUM_LOOKING_SCORE = args
    keywords = search.split()
    scored = []

    for article in articles_chunk:
        title_words = article["title"].split()
        content_words = article["content"].split()

        title_matches = sum(1 for word in title_words if word in keywords)
        content_matches = sum(1 for word in content_words if word in keywords)

        bm25_title = title_matches * (k + 1) / (title_matches + k * (1 - b + b * (len(title_words) / averageTitleLength))) if title_matches else 0
        bm25_content = content_matches * (k + 1) / (content_matches + k * (1 - b + b * (len(content_words) / averageWordsLength))) if content_matches else 0

        total_score = bm25_title + bm25_content

        if total_score >= MINIMUM_LOOKING_SCORE:
            scored.append({"article": article, "score": total_score})

    return scored

def compute_score(article_data, keywords, k, b, avg_title_len, avg_content_len, min_score):
    title_matches = len(article_data["title_tokens"] & keywords)
    content_matches = len(article_data["content_tokens"] & keywords)

    bm25_title = (
        title_matches * (k + 1) /
        (title_matches + k * (1 - b + b * (article_data["title_len"] / avg_title_len)))
    ) if title_matches else 0

    bm25_content = (
        content_matches * (k + 1) /
        (content_matches + k * (1 - b + b * (article_data["content_len"] / avg_content_len)))
    ) if content_matches else 0

    total_score = bm25_title + bm25_content
    return {"article": article_data["article"], "score": total_score} if total_score >= min_score else None





@measure_time
def lookUpDocuments_parallel(search, articles, averageTitleLength, averageWordsLength, k, b, MINIMUM_LOOKING_SCORE, num_workers=None):
    if num_workers is None:
        num_workers = min(cpu_count(), 8)
    print(num_workers)
    chunk_size = math.ceil(len(articles) / num_workers)
    chunks = [articles[i:i+chunk_size] for i in range(0, len(articles), chunk_size)]

    args_list = [
        (search, chunk, averageTitleLength, averageWordsLength, k, b, MINIMUM_LOOKING_SCORE)
        for chunk in chunks
    ]

    with Pool(processes=num_workers) as pool:
        results = pool.map(score_articles_chunk, args_list)

    all_scored = [item for sublist in results for item in sublist]
    all_scored.sort(key=lambda x: x["score"], reverse=True)

    return all_scored[:MAX_RESULTS]



def preprocess_articles(articles):
    data = []
    for article in articles:
        title_tokens = article["title"].split()
        content_tokens = article["content"].split()

        data.append({
            "id": article["id"],
            "title": article["title"],
            "title_len": len(title_tokens),
            "title_tokens": set(title_tokens),
            "content_len": len(content_tokens),
            "content_tokens": set(content_tokens),
            "article": article,
        })
    return data

def score_all_articles_numpy_style(query, preprocessed_data, k, b, avg_title_len, avg_content_len, min_score):
    keywords = set(query.split())
    results = []

    for article_data in preprocessed_data:
        result = compute_score(article_data, keywords, k, b, avg_title_len, avg_content_len, min_score)
        if result:
            results.append(result)

    return sorted(results, key=lambda x: x["score"], reverse=True)[:MAX_RESULTS]



if __name__ == "__main__":
    articles = load_articles('articles.json')
    averageTitleLength, averageWordsLength = set_average_length(articles)

    k = 1.5
    b = 0.75
    MINIMUM_LOOKING_SCORE = 0.2
    MAX_RESULTS = 100

    query = "Machine Learning is hard"
    results = lookUpDocuments_parallel(query, articles, averageTitleLength, averageWordsLength, k, b, MINIMUM_LOOKING_SCORE)

    print(f"Total: {len(results)}")
    for item in results:
        print({"id": item["article"]["id"], "title": item["article"]["title"], "score": round(item["score"], 4)})


#print(lookUpDocuments("Bro this is wild", articles))
#print(lookUpDocuments("I like Django, movie not framework", articles))
#print(lookUpDocuments("I like Django", articles))
       
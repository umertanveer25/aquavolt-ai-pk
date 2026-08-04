import requests
import urllib.parse
import json

queries = {
    "Microsoft FarmBeats": "FarmBeats AND (IoT OR agriculture)",
    "Google Mineral / AI Agriculture": "(\"Alphabet\" OR \"Google\") AND agriculture AND \"machine learning\"",
    "IBM Watson Agriculture": "\"IBM\" AND agriculture AND \"Watson\""
}

results_out = []

for giant, query in queries.items():
    url = f"https://api.openalex.org/works?search={urllib.parse.quote(query)}&filter=publication_year:2017-2026&sort=cited_by_count:desc&per-page=3"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        results = data.get('results', [])
        print(f"\n--- {giant} ---")
        if not results:
             print("No major papers found.")
        for work in results:
            title = work.get('title', 'Unknown Title')
            year = work.get('publication_year', 'n.d.')
            doi = work.get('doi', 'No DOI')
            citations = work.get('cited_by_count', 0)
            print(f"[{year}] {title} (Citations: {citations}) - {doi}")
    except Exception as e:
        print(f"Error fetching data for {giant}: {e}")

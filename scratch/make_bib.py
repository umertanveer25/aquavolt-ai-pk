import json

with open('scratch/openalex_results.json', 'r', encoding='utf-8') as f:
    works = json.load(f)

bib_content = ''
for i, w in enumerate(works):
    ref_id = f'ref{i+1}'
    title = w.get('title', 'Unknown Title')
    if title:
        title = title.replace('{', '').replace('}', '')
    year = w.get('publication_year', '2024')
    doi = w.get('doi', '')
    
    authors_list = w.get('authorships', [])
    author_names = []
    for a in authors_list:
        name = a.get('author', {}).get('display_name', '')
        if name:
            author_names.append(name)
    author_str = ' and '.join(author_names) if author_names else 'Unknown Author'
    
    venue = w.get('primary_location', {}).get('source', {})
    journal = venue.get('display_name', 'Unknown Journal') if venue else 'Unknown Journal'
    
    bib_content += f'@article{{{ref_id},\n'
    bib_content += f'  title={{{title}}},\n'
    bib_content += f'  author={{{author_str}}},\n'
    bib_content += f'  journal={{{journal}}},\n'
    bib_content += f'  year={{{year}}},\n'
    if doi:
        clean_doi = doi.replace("https://doi.org/", "")
        bib_content += f'  doi={{{clean_doi}}}\n'
    bib_content += f'}}\n\n'

with open('aquavolt_paper.bib', 'w', encoding='utf-8') as f:
    f.write(bib_content)
print('aquavolt_paper.bib created successfully.')

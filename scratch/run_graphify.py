import sys, json, os
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path("C:/Users/umert/aquavolt-ai-pk")
GRAPHIFY_OUT = PROJECT_ROOT / "graphify-out"
GRAPHIFY_OUT.mkdir(exist_ok=True)

(GRAPHIFY_OUT / ".graphify_python").write_text(sys.executable, encoding="utf-8")
(GRAPHIFY_OUT / ".graphify_root").write_text(str(PROJECT_ROOT), encoding="utf-8")

# Step 2: Detect
from graphify.detect import detect
detect_res = detect(PROJECT_ROOT)
(GRAPHIFY_OUT / ".graphify_detect.json").write_text(json.dumps(detect_res, ensure_ascii=False), encoding="utf-8")

# Step 3: AST extract
from graphify.extract import collect_files, extract
code_files = []
for f in detect_res.get('files', {}).get('code', []):
    p = Path(f)
    code_files.extend(collect_files(p) if p.is_dir() else [p])
ast_res = extract(code_files, cache_root=PROJECT_ROOT) if code_files else {'nodes':[],'edges':[],'input_tokens':0,'output_tokens':0}
(GRAPHIFY_OUT / ".graphify_ast.json").write_text(json.dumps(ast_res, indent=2, ensure_ascii=False), encoding="utf-8")

# Merge
merged = {
    'nodes': ast_res['nodes'],
    'edges': ast_res['edges'],
    'hyperedges': [],
    'input_tokens': 0,
    'output_tokens': 0,
}
(GRAPHIFY_OUT / ".graphify_extract.json").write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")

# Build and generate
from graphify.build import build_from_json
from graphify.cluster import cluster, score_all
from graphify.analyze import god_nodes, surprising_connections, suggest_questions
from graphify.report import generate
from graphify.export import to_json

G = build_from_json(merged, root=PROJECT_ROOT, directed=False)
if G.number_of_nodes() == 0:
    print("Graph empty.")
    sys.exit(1)

communities = cluster(G)
cohesion = score_all(G, communities)
gods = god_nodes(G)
surprises = surprising_connections(G, communities)
labels = {cid: 'Community ' + str(cid) for cid in communities}
questions = suggest_questions(G, communities, labels)

to_json(G, communities, str(GRAPHIFY_OUT / "graph.json"))
report = generate(G, communities, cohesion, labels, gods, surprises, detect_res, {'input':0,'output':0}, PROJECT_ROOT, suggested_questions=questions)
(GRAPHIFY_OUT / "GRAPH_REPORT.md").write_text(report, encoding="utf-8")

print("GRAPHIFY SUCCESS: Report and graph.json generated in graphify-out.")

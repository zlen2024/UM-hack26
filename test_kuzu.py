import json
from backend.database import init_graph_db, get_graph_conn

init_graph_db()
conn = get_graph_conn()

cypher_queries = [
    "MERGE (n:Entity {id: 'john_doe'}) ON MATCH SET n.label = 'Person', n.properties = '{\"name\": \"John Doe\"}' ON CREATE SET n.label = 'Person', n.properties = '{\"name\": \"John Doe\"}'",
    "MERGE (n:Entity {id: 'xiaomi_phone'}) ON MATCH SET n.label = 'Product', n.properties = '{\"brand\": \"Xiaomi\"}' ON CREATE SET n.label = 'Product', n.properties = '{\"brand\": \"Xiaomi\"}'",
    "MATCH (a:Entity {id: 'john_doe'}), (b:Entity {id: 'xiaomi_phone'}) MERGE (a)-[r:RelatedTo {relationship_type: 'LIKES'}]->(b) ON MATCH SET r.properties = '{}' ON CREATE SET r.properties = '{}'"
]

for q in cypher_queries:
    print(f"Executing: {q}")
    try:
        conn.execute(q)
        print("Success")
    except Exception as e:
        print(f"Error: {e}")

print("Fetching nodes...")
res = conn.execute("MATCH (n:Entity) RETURN n.id, n.label, n.properties")
while res.has_next():
    print(res.get_next())

print("Fetching edges...")
res = conn.execute("MATCH (a:Entity)-[r:RelatedTo]->(b:Entity) RETURN a.id, b.id, r.relationship_type, r.properties")
while res.has_next():
    print(res.get_next())

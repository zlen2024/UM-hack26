import os
import ladybug as lb

class KnowledgeDB:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.getenv("KNOWLEDGE_DB_PATH", "knowledge.lbug")
        
        self.db = lb.Database(db_path)
        self.conn = lb.Connection(self.db)
        self.init_schema()

    def init_schema(self):
        # Create Entity node table
        try:
            self.conn.execute("CREATE NODE TABLE Entity(id STRING, label STRING, properties STRING, PRIMARY KEY(id))")
        except RuntimeError as e:
            if "already exists" not in str(e).lower():
                raise e
        
        # Create RelatedTo relationship table
        try:
            self.conn.execute("CREATE REL TABLE RelatedTo(FROM Entity TO Entity, type STRING, properties STRING)")
        except RuntimeError as e:
            if "already exists" not in str(e).lower():
                raise e

    def execute_cypher(self, query: str):
        result = self.conn.execute(query)
        
        # Check if the query returned any data
        if not result.has_next():
            return []
            
        cols = result.get_column_names()
        rows = []
        while result.has_next():
            rows.append(dict(zip(cols, result.get_next())))
        return rows

    def get_all_graph_data(self):
        nodes_result = self.execute_cypher("MATCH (n:Entity) RETURN n.id as id, n.label as label, n.properties as properties")
        edges_result = self.execute_cypher("MATCH (a:Entity)-[r:RelatedTo]->(b:Entity) RETURN a.id as source, b.id as target, r.type as type, r.properties as properties")
        return {
            "nodes": nodes_result,
            "edges": edges_result
        }

    def close(self):
        self.conn.close()

# Initialize a global instance
knowledge_db = KnowledgeDB()

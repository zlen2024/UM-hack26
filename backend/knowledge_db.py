import os
import ladybug as lb

class KnowledgeDB:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.getenv("KNOWLEDGE_DB_PATH", "knowledge.lbug")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
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

    def add_node(self, node_id: str, label: str, properties: str):
        # Using string replacement to escape single quotes, assuming well-formed inputs
        safe_id = node_id.replace("'", "\\'")
        safe_label = label.replace("'", "\\'")
        safe_props = properties.replace("'", "\\'")
        query = f"MERGE (n:Entity {{id: '{safe_id}'}}) ON CREATE SET n.label = '{safe_label}', n.properties = '{safe_props}' ON MATCH SET n.label = '{safe_label}', n.properties = '{safe_props}'"
        return self.execute_cypher(query)

    def update_node(self, node_id: str, label: str, properties: str):
        safe_id = node_id.replace("'", "\\'")
        safe_label = label.replace("'", "\\'")
        safe_props = properties.replace("'", "\\'")
        query = f"MATCH (n:Entity {{id: '{safe_id}'}}) SET n.label = '{safe_label}', n.properties = '{safe_props}'"
        return self.execute_cypher(query)

    def delete_node(self, node_id: str):
        safe_id = node_id.replace("'", "\\'")
        query = f"MATCH (n:Entity {{id: '{safe_id}'}}) DETACH DELETE n"
        return self.execute_cypher(query)

    def add_edge(self, source_id: str, target_id: str, edge_type: str, properties: str):
        safe_source = source_id.replace("'", "\\'")
        safe_target = target_id.replace("'", "\\'")
        safe_type = edge_type.replace("'", "\\'")
        safe_props = properties.replace("'", "\\'")
        query = f"MATCH (a:Entity {{id: '{safe_source}'}}), (b:Entity {{id: '{safe_target}'}}) MERGE (a)-[r:RelatedTo]->(b) ON CREATE SET r.type = '{safe_type}', r.properties = '{safe_props}' ON MATCH SET r.type = '{safe_type}', r.properties = '{safe_props}'"
        return self.execute_cypher(query)

    def update_edge(self, source_id: str, target_id: str, edge_type: str, properties: str):
        safe_source = source_id.replace("'", "\\'")
        safe_target = target_id.replace("'", "\\'")
        safe_type = edge_type.replace("'", "\\'")
        safe_props = properties.replace("'", "\\'")
        query = f"MATCH (a:Entity {{id: '{safe_source}'}})-[r:RelatedTo {{type: '{safe_type}'}}]->(b:Entity {{id: '{safe_target}'}}) SET r.properties = '{safe_props}'"
        return self.execute_cypher(query)

    def delete_edge(self, source_id: str, target_id: str, edge_type: str):
        safe_source = source_id.replace("'", "\\'")
        safe_target = target_id.replace("'", "\\'")
        safe_type = edge_type.replace("'", "\\'")
        query = f"MATCH (a:Entity {{id: '{safe_source}'}})-[r:RelatedTo {{type: '{safe_type}'}}]->(b:Entity {{id: '{safe_target}'}}) DELETE r"
        return self.execute_cypher(query)

    def close(self):
        self.conn.close()

class KnowledgeDBFactory:
    _instances = {}

    @classmethod
    def get_instance(cls, user_id: str) -> KnowledgeDB:
        if user_id not in cls._instances:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base_dir, "data", "lbug", f"{user_id}.lbug")
            cls._instances[user_id] = KnowledgeDB(db_path)
        return cls._instances[user_id]

import os
import ladybug as lb

class KnowledgeDB:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.getenv("KNOWLEDGE_DB_PATH", "knowledge.lbug")
        
        # Ensure directory exists
        dir_name = os.path.dirname(db_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        
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

    def get_relevant_context(self, text: str) -> str:
        """Extract relevant facts from the graph based on the user's text."""
        import re
        import logging
        
        logger = logging.getLogger("CS_Agent_Workflow")
        
        # Grab words 3 characters or longer (to catch names like "Ali", "Abu", etc.)
        words = re.findall(r'\b\w{3,}\b', text.lower())
        
        if not words:
            return ""
            
        facts = []
        logger.info(f"[KG Retrieval] Searching for keywords: {words}")
        
        for word in words:
            safe_word = word.replace("'", "\\'")
            
            # Find matching nodes
            try:
                node_query = f"MATCH (n:Entity) WHERE lower(n.id) CONTAINS '{safe_word}' OR lower(n.label) CONTAINS '{safe_word}' RETURN n.id, n.label LIMIT 3"
                nodes = self.execute_cypher(node_query)
                for node in nodes:
                    facts.append(f"Node: {node.get('n.id')} (Type: {node.get('n.label')})")
                    
                # Find matching edges (1-hop)
                edge_query = f"MATCH (a:Entity)-[r:RelatedTo]->(b:Entity) WHERE lower(a.id) CONTAINS '{safe_word}' OR lower(b.id) CONTAINS '{safe_word}' RETURN a.id, r.type, b.id LIMIT 5"
                edges = self.execute_cypher(edge_query)
                for edge in edges:
                    facts.append(f"Fact: {edge.get('a.id')} is {edge.get('r.type')} {edge.get('b.id')}")
            except Exception as e:
                # Catch Ladybug syntax or execution errors and continue
                logger.error(f"[KG Retrieval] Error querying KG for '{safe_word}': {e}")
                continue
                
        # Deduplicate and format
        unique_facts = list(set(facts))
        if not unique_facts:
            logger.info(f"[KG Retrieval] No relevant facts found.")
            return ""
            
        logger.info(f"[KG Retrieval] Found {len(unique_facts)} relevant facts.")
        return "=== CUSTOMER KNOWLEDGE GRAPH ===\n" + "\n".join(unique_facts) + "\n\n"

    def close(self):
        self.conn.close()

class KnowledgeDBFactory:
    _instances = {}

    @classmethod
    def get_instance(cls, user_id) -> KnowledgeDB:
        user_id_str = str(user_id)
        if user_id_str not in cls._instances:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base_dir, "data", "lbug", f"{user_id_str}.lbug")
            cls._instances[user_id_str] = KnowledgeDB(db_path)
        return cls._instances[user_id_str]

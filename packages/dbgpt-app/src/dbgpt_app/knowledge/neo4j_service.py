"""Neo4j Knowledge Graph Query Service."""

import logging
from typing import List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("neo4j package not available. Install with: pip install neo4j")


@dataclass
class Neo4jConfig:
    """Neo4j connection configuration."""
    host: str = "192.168.102.59"
    port: int = 7687
    user: str = "neo4j"
    password: str = "tWsM@neo4j2023"
    database: str = "neo4j"
    
    @property
    def uri(self) -> str:
        return f"bolt://{self.host}:{self.port}"


class Neo4jQueryService:
    """Service for querying Neo4j knowledge graph."""
    
    def __init__(self, config: Neo4jConfig = None):
        """Initialize Neo4j query service."""
        self.config = config or Neo4jConfig()
        self.driver = None
        self._connect()
    
    def _connect(self):
        """Connect to Neo4j database."""
        if not NEO4J_AVAILABLE:
            logger.error("Neo4j package not available")
            return
            
        try:
            self.driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.user, self.config.password)
            )
            # Test connection
            with self.driver.session(database=self.config.database) as session:
                session.run("RETURN 1")
            logger.info(f"Connected to Neo4j at {self.config.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.driver = None
    
    def is_connected(self) -> bool:
        """Check if connected to Neo4j."""
        return self.driver is not None
    
    def query_graph(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Query Neo4j graph with natural language query converted to Cypher.
        
        Args:
            query: Natural language query
            limit: Maximum number of results to return
            
        Returns:
            List of graph results as dictionaries
        """
        if not self.is_connected():
            return []
            
        try:
            # Simple keyword-based Cypher generation
            cypher_query = self._generate_cypher_query(query, limit)
            
            with self.driver.session(database=self.config.database) as session:
                result = session.run(cypher_query)
                records = []
                
                for record in result:
                    record_dict = {}
                    for key in record.keys():
                        value = record[key]
                        # Convert Neo4j types to serializable types
                        if hasattr(value, '_properties'):
                            record_dict[key] = dict(value._properties)
                        elif hasattr(value, 'properties'):
                            record_dict[key] = dict(value.properties)
                        else:
                            record_dict[key] = value
                    records.append(record_dict)
                
                return records
                
        except Exception as e:
            logger.error(f"Error querying Neo4j: {e}")
            return []
    
    def _generate_cypher_query(self, query: str, limit: int) -> str:
        """
        Generate Cypher query from natural language query.
        This is a simple keyword-based approach.
        """
        query_lower = query.lower()
        
        # Basic patterns for different types of queries
        if any(word in query_lower for word in ['relation', 'relationship', 'connect', 'link']):
            # Query for relationships
            cypher = f"""
            MATCH (n)-[r]->(m)
            WHERE toLower(toString(n)) CONTAINS $query OR toLower(toString(m)) CONTAINS $query
            RETURN n, r, m
            LIMIT {limit}
            """
        elif any(word in query_lower for word in ['node', 'entity', 'person', 'company']):
            # Query for nodes
            cypher = f"""
            MATCH (n)
            WHERE any(prop in keys(n) WHERE toLower(toString(n[prop])) CONTAINS $query)
            RETURN n
            LIMIT {limit}
            """
        else:
            # General search query
            cypher = f"""
            MATCH (n)
            WHERE any(prop in keys(n) WHERE toLower(toString(n[prop])) CONTAINS $query)
            OPTIONAL MATCH (n)-[r]->(m)
            RETURN n, r, m
            LIMIT {limit}
            """
        
        # For now, we'll use a simple string replacement instead of parameterized query
        # In production, you should use proper parameterization
        simple_cypher = cypher.replace('$query', f"'{query_lower}'")
        
        logger.info(f"Generated Cypher query: {simple_cypher}")
        return simple_cypher
    
    def format_results(self, results: List[Dict[str, Any]]) -> str:
        """Format Neo4j query results as readable text."""
        if not results:
            return "No results found in the knowledge graph."
        
        formatted_lines = ["Knowledge Graph Results:"]
        
        for i, record in enumerate(results, 1):
            formatted_lines.append(f"\n{i}. ")
            
            for key, value in record.items():
                if isinstance(value, dict):
                    # Format node/relationship properties
                    props = []
                    for prop_key, prop_value in value.items():
                        if prop_value:
                            props.append(f"{prop_key}: {prop_value}")
                    if props:
                        formatted_lines.append(f"   {key}: {', '.join(props)}")
                elif value:
                    formatted_lines.append(f"   {key}: {value}")
        
        return "\n".join(formatted_lines)
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
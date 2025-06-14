#!/usr/bin/env python3
"""Simple Neo4j Query Service - Lightweight wrapper for basic Neo4j operations."""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("Neo4j driver not available. Install with: pip install neo4j")


class SimpleNeo4jQueryService:
    """Simplified Neo4j Query Service for basic operations."""
    
    def __init__(self, uri: str = "bolt://192.168.102.59:7687", 
                 user: str = "neo4j", 
                 password: str = "tWsM@neo4j2023"):
        """Initialize simple Neo4j service."""
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self._connected = False
        
        if NEO4J_AVAILABLE:
            self._initialize()
        else:
            logger.error("Neo4j driver not available")
    
    def _initialize(self):
        """Initialize Neo4j connection."""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            self._connected = True
            logger.info(f"Successfully connected to Neo4j at {self.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self._connected = False
    
    def is_connected(self) -> bool:
        """Check if connected to Neo4j."""
        return self._connected and self.driver is not None
    
    def query_graph(self, question: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Query Neo4j database with simplified approach.
        
        Args:
            question: Natural language question
            limit: Maximum number of results
            
        Returns:
            List of query results
        """
        if not self.is_connected():
            logger.warning("Neo4j not connected")
            return []
        
        try:
            # Simple keyword-based query mapping
            cypher_query = self._generate_simple_cypher(question, limit)
            logger.info(f"Generated Cypher query: {cypher_query}")
            
            with self.driver.session() as session:
                result = session.run(cypher_query)
                records = []
                for record in result:
                    records.append(dict(record))
                
                # Enhanced logging with detailed result information
                logger.info(f"Neo4j query successful: returned {len(records)} results")
                if records:
                    logger.info(f"Query result preview: {str(records[0])[:200]}...")  # First record preview
                    logger.debug(f"Full Cypher query executed: {cypher_query}")
                    logger.debug(f"Complete result set: {records}")
                else:
                    logger.info("Neo4j query returned no results")
                
                return records
                
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return []
    
    def _generate_simple_cypher(self, question: str, limit: int) -> str:
        """Generate simple Cypher query based on keywords."""
        question_lower = question.lower()
        
        # Basic keyword matching for Chinese historical figures
        if any(keyword in question_lower for keyword in ['毛主席', '毛泽东']):
            return f"MATCH (p:人物) WHERE p.nodeName CONTAINS '毛泽东' OR p.人物名称 CONTAINS '毛泽东' RETURN p LIMIT {limit}"
        elif any(keyword in question_lower for keyword in ['曾国藩']):
            return f"MATCH (p:人物) WHERE p.nodeName CONTAINS '曾国藩' OR p.人物名称 CONTAINS '曾国藩' RETURN p LIMIT {limit}"
        elif any(keyword in question_lower for keyword in ['孙中山']):
            return f"MATCH (p:人物) WHERE p.nodeName CONTAINS '孙中山' OR p.人物名称 CONTAINS '孙中山' RETURN p LIMIT {limit}"
        elif any(keyword in question_lower for keyword in ['历史人物', '人物']):
            return f"MATCH (p:人物) RETURN p LIMIT {limit}"
        elif any(keyword in question_lower for keyword in ['出生地', '地方']):
            return f"MATCH (p:人物) WHERE p.出生地 IS NOT NULL RETURN p.nodeName, p.出生地 LIMIT {limit}"
        else:
            # Default query - return some people
            return f"MATCH (p:人物) RETURN p LIMIT {limit}"
    
    def format_results(self, results: List[Dict[str, Any]]) -> str:
        """Format query results as readable text."""
        if not results:
            return "未找到相关信息。"
        
        formatted_text = "查询结果：\n"
        for i, record in enumerate(results, 1):
            if 'p' in record:
                person = record['p']
                if hasattr(person, '_properties'):
                    props = person._properties
                    name = props.get('nodeName', props.get('人物名称', '未知'))
                    career = props.get('职业', '未知')
                    birthplace = props.get('出生地', '未知')
                    achievements = props.get('主要成就', '未知')
                    
                    formatted_text += f"{i}. 姓名: {name}\n"
                    formatted_text += f"   职业: {career}\n"
                    formatted_text += f"   出生地: {birthplace}\n"
                    formatted_text += f"   主要成就: {achievements}\n\n"
                else:
                    formatted_text += f"{i}. {str(person)}\n"
            else:
                # Handle other record formats
                formatted_text += f"{i}. {str(record)}\n"
        
        return formatted_text.strip()
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            try:
                self.driver.close()
                logger.info("Neo4j connection closed")
            except Exception as e:
                logger.error(f"Error closing Neo4j connection: {e}")
            finally:
                self.driver = None
                self._connected = False

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
        """Generate simple Cypher query based on keywords for various node types."""
        question_lower = question.lower()
        
        # 人物查询
        if any(keyword in question_lower for keyword in ['毛主席', '毛泽东']):
            return f"MATCH (n:人物) WHERE n.nodeName CONTAINS '毛泽东' OR n.人物名称 CONTAINS '毛泽东' RETURN n LIMIT {limit}"
        elif any(keyword in question_lower for keyword in ['曾国藩']):
            return f"MATCH (n:人物) WHERE n.nodeName CONTAINS '曾国藩' OR n.人物名称 CONTAINS '曾国藩' RETURN n LIMIT {limit}"
        elif any(keyword in question_lower for keyword in ['孙中山']):
            return f"MATCH (n:人物) WHERE n.nodeName CONTAINS '孙中山' OR n.人物名称 CONTAINS '孙中山' RETURN n LIMIT {limit}"
        elif any(keyword in question_lower for keyword in ['历史人物', '人物']):
            return f"MATCH (n:人物) RETURN n LIMIT {limit}"
        
        # 地点查询
        elif any(keyword in question_lower for keyword in ['地点', '地方', '城市']):
            return f"MATCH (n:地点) RETURN n LIMIT {limit}"
        elif any(keyword in question_lower for keyword in ['出生地']):
            return f"MATCH (n:人物) WHERE n.出生地 IS NOT NULL RETURN n.nodeName, n.出生地 LIMIT {limit}"
        
        # 事件查询
        elif any(keyword in question_lower for keyword in ['事件', '历史事件']):
            return f"MATCH (n:事件) RETURN n LIMIT {limit}"
        
        # 战役查询
        elif any(keyword in question_lower for keyword in ['战役', '军事行动', '战争']):
            return f"MATCH (n:战役阶段) RETURN n LIMIT {limit}"
        
        # 组织查询
        elif any(keyword in question_lower for keyword in ['组织', '部队']):
            return f"MATCH (n:组织) RETURN n LIMIT {limit}"
            
        # 国家查询
        elif any(keyword in question_lower for keyword in ['国家']):
            return f"MATCH (n:国家) RETURN n LIMIT {limit}"
            
        # 政策查询
        elif any(keyword in question_lower for keyword in ['政策', '政权']):
            return f"MATCH (n:政策) RETURN n LIMIT {limit}"
            
        # 文献查询
        elif any(keyword in question_lower for keyword in ['文献', '古籍']):
            return f"MATCH (n:文献) RETURN n LIMIT {limit}"
            
        # 朝代查询
        elif any(keyword in question_lower for keyword in ['朝代', '王朝']):
            return f"MATCH (n:朝代) RETURN n LIMIT {limit}"
            
        # 一带一路项目查询
        elif any(keyword in question_lower for keyword in ['一带一路', '项目']):
            return f"MATCH (n:一带一路项目) RETURN n LIMIT {limit}"
        
        # 非物质文化遗产查询
        elif any(keyword in question_lower for keyword in ['非遗', '文化遗产', '传承']):
            return f"MATCH (n:非物质文化遗产项目) RETURN n LIMIT {limit}"
        
        else:
            # Default query - search across all node types
            return f"MATCH (n) WHERE ANY(prop IN keys(n) WHERE toString(n[prop]) CONTAINS '{question[:10]}') RETURN n LIMIT {limit}"
    
    def format_results(self, results: List[Dict[str, Any]]) -> str:
        """Format query results as readable text for various node types."""
        if not results:
            return "未找到相关信息。"
        
        formatted_text = "查询结果：\n"
        for i, record in enumerate(results, 1):
            # Process each node in the record
            for key, node in record.items():
                if hasattr(node, '_properties') and hasattr(node, 'labels'):
                    props = node._properties
                    labels = list(node.labels)
                    
                    # Get node name - try multiple possible name fields
                    node_name = (props.get('nodeName') or 
                               props.get('人物名称') or 
                               props.get('名称') or 
                               props.get('name') or 
                               props.get('title') or 
                               props.get('标题') or '未知')
                    
                    # Add node info with label
                    label_text = labels[0] if labels else '节点'
                    formatted_text += f"{i}. {node_name} ({label_text})\n"
                    
                    # Add key properties based on node type
                    if '人物' in labels:
                        career = props.get('职业', '未知')
                        birthplace = props.get('出生地', '未知')
                        achievements = props.get('主要成就', '未知')
                        formatted_text += f"   职业: {career}\n"
                        formatted_text += f"   出生地: {birthplace}\n"
                        formatted_text += f"   主要成就: {achievements}\n"
                    else:
                        # For other node types, show all non-empty properties (except resourceId)
                        for prop_key, prop_value in props.items():
                            if (prop_key not in ['nodeName', '人物名称', '名称', 'name', 'title', '标题', 'resourceId'] 
                                and prop_value and str(prop_value).strip()):
                                formatted_text += f"   {prop_key}: {prop_value}\n"
                    
                    formatted_text += "\n"
                else:
                    # Handle other record formats
                    formatted_text += f"{i}. {str(node)}\n"
        
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

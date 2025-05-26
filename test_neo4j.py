#!/usr/bin/env python3
"""Test script for Neo4j integration."""

import sys
import os

# Add the packages to Python path
sys.path.insert(0, '/home/yannic/work/github/DB-GPT/packages/dbgpt-app/src')

def test_neo4j_connection():
    """Test Neo4j connection and basic functionality."""
    try:
        from dbgpt_app.knowledge.neo4j_service import Neo4jQueryService
        
        print("Testing Neo4j connection...")
        neo4j_service = Neo4jQueryService()
        
        if neo4j_service.is_connected():
            print("✅ Successfully connected to Neo4j!")
            
            # Test a simple query
            test_query = "test query"
            results = neo4j_service.query_graph(test_query, limit=3)
            
            print(f"Query results: {len(results)} records found")
            if results:
                formatted_results = neo4j_service.format_results(results)
                print("Formatted results:")
                print(formatted_results)
            else:
                print("No results returned from test query")
                
        else:
            print("❌ Failed to connect to Neo4j")
            print("This is expected if Neo4j server is not running")
            
        # Clean up
        neo4j_service.close()
        print("✅ Test completed successfully")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_neo4j_connection()

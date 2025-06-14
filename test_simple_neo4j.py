#!/usr/bin/env python3
"""Test script for simplified Neo4j integration."""

import sys
import os

def test_simple_neo4j():
    """Test simplified Neo4j service."""
    try:
        from simple_neo4j_service import SimpleNeo4jQueryService
        
        print("🔗 Testing simplified Neo4j connection...")
        neo4j_service = SimpleNeo4jQueryService()
        
        if neo4j_service.is_connected():
            print("✅ Successfully connected to Neo4j!")
            
            # Test various query patterns
            test_queries = [
                "毛主席有哪些事迹",
                "曾国藩的成就",
                "历史人物的出生地",
                "孙中山的贡献"
            ]
            
            for query in test_queries:
                print(f"\n📋 Testing query: {query}")
                results = neo4j_service.query_graph(query, limit=3)
                
                if results:
                    print(f"✅ Query returned {len(results)} results")
                    formatted_results = neo4j_service.format_results(results)
                    print("📄 Formatted results:")
                    print(formatted_results[:200] + "..." if len(formatted_results) > 200 else formatted_results)
                else:
                    print("⚠️  No results returned")
                    
        else:
            print("❌ Failed to connect to Neo4j")
            print("This is expected if Neo4j server is not running at 192.168.102.59:7687")
            
        # Clean up
        neo4j_service.close()
        print("\n✅ Test completed successfully")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_neo4j()

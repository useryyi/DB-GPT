"""
Neo4j connector example.

This example shows how to use the Neo4j connector to interact with a Neo4j database.
"""

import os
import sys

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dbgpt_ext.datasource.conn_neo4j import Neo4jConnector, Neo4jParameters


def main():
    """Run the Neo4j connector example."""
    # Create a new Neo4j connector from parameters
    parameters = Neo4jParameters(
        host="192.168.102.59",
        port=7687,
        user="neo4j",
        password="tWsM@neo4j2023",  # Replace with your actual password
        database="neo4j",
    )
    
    # Create the connector from parameters
    connector = Neo4jConnector.from_parameters(parameters)
    
    try:
        # Get system information
        try:
            system_info = connector.get_system_info()
            print("System Info:")
            for key, value in system_info.items():
                print(f"  {key}: {value}")
        except Exception as e:
            print(f"Error getting system info: {e}")
        
        # Get node labels and relationship types (tables)
        print("\nNode Labels and Relationship Types:")
        try:
            table_names = list(connector.get_table_names())
            if not table_names:
                print("  No tables/labels found or database is empty")
            else:
                for table_name in table_names:
                    print(f"  {table_name}")
        except Exception as e:
            print(f"  Error retrieving table names: {e}")
            table_names = []  # 确保后续代码不会因为table_names未定义而出错
          # Run a simple Cypher query
        print("\nRunning Cypher query: MATCH (n) RETURN n.name LIMIT 5")
        try:
            results = connector.run("MATCH (n) RETURN n.name LIMIT 5")
            for record in results:
                print(f"  {record}")
        except Exception as e:
            print(f"  Error running query: {e}")
            # 尝试更通用的查询
            try:
                print("  Trying more generic query: RETURN 1 as test")
                results = connector.run("RETURN 1 as test")
                for record in results:
                    print(f"  {record}")
            except Exception as e2:
                print(f"  Error running generic query: {e2}")
        
        # Run a streaming query
        print("\nRunning streaming query: MATCH (n) RETURN n.name LIMIT 5")
        try:
            count = 0
            for record in connector.run_stream("MATCH (n) RETURN n.name LIMIT 5"):
                print(f"  {record}")
                count += 1
            print(f"  Retrieved {count} records")
        except Exception as e:
            print(f"  Error running stream query: {e}")
            # 尝试更通用的查询
            try:
                print("  Trying more generic streaming query: RETURN 1 as test")
                count = 0
                for record in connector.run_stream("RETURN 1 as test"):
                    print(f"  {record}")
                    count += 1
                print(f"  Retrieved {count} records")
            except Exception as e2:
                print(f"  Error running generic stream query: {e2}")
          # Get columns (properties) for a node label
        # 首先尝试找到一个存在的标签
        try:
            # 如果前面成功获取了标签，尝试使用其中一个
            label_to_try = None
            if 'table_names' in locals() and table_names:
                for label in table_names:
                    if "_node" in label:
                        label_to_try = label
                        break
            
            # 如果没有找到合适的标签，使用默认值
            if not label_to_try:
                label_to_try = "Person_node"  # 默认尝试的标签
            
            print(f"\nProperties for {label_to_try}:")
            try:
                properties = connector.get_columns(label_to_try)
                if not properties:
                    print(f"  No properties found for {label_to_try}")
                else:
                    for prop in properties:
                        print(f"  {prop['name']} ({prop['type']})")
            except Exception as e:
                print(f"  Error getting properties: {e}")
            
            # Get indexes for a node label
            print(f"\nIndexes for {label_to_try}:")
            try:
                indexes = connector.get_indexes(label_to_try)
                if not indexes:
                    print(f"  No indexes found for {label_to_try}")
                else:
                    for idx in indexes:
                        print(f"  {idx['name']}: {', '.join(idx['column_names'])}")
            except Exception as e:
                print(f"  Error getting indexes: {e}")
        
        except Exception as e:
            print(f"  Error processing label operations: {e}")
            
    except Exception as main_e:
        print(f"Unexpected error in main process: {main_e}")
        
    finally:
        # Close the connector
        try:
            connector.close()
            print("\nConnection closed.")
        except Exception as e:
            print(f"\nError closing connection: {e}")


if __name__ == "__main__":
    main()

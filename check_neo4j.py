from neo4j import GraphDatabase
import sys

passwords = ["password", "neo4j", "123456", "", "owalabuy", "miniworld", "admin", "root"]
uri = "bolt://localhost:7687"

for pwd in passwords:
    try:
        driver = GraphDatabase.driver(uri, auth=("neo4j", pwd), connection_timeout=3)
        with driver.session() as session:
            result = session.run("RETURN 1 AS test")
            if result.single()["test"] == 1:
                print(f"✓ 密码正确: '{pwd}'")
                driver.close()
                sys.exit(0)
    except Exception as e:
        if "authentication failure" not in str(e).lower():
            print(f"? 其他错误: {e}")
        continue

print("✗ 所有常见密码都失败")

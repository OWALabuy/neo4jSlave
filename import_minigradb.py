#!/usr/bin/env python3
"""
MiniGraDB 数据导入脚本
将 CSV 导出文件导入到 Neo4j
"""
import csv
import sys
from pathlib import Path
from neo4j import GraphDatabase

# 配置
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "miniworld")
EXPORT_DIR = Path("/home/owalabuy/awa/MiniGraDB/MiniGraDB/neo4j_export_20250917_143741")
BATCH_SIZE = 500


def safe_int(value):
    """安全转换为整数，处理浮数字符串如 '11000.0'"""
    if not value:
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def clear_database(driver):
    """清空数据库"""
    with driver.session() as session:
        print("清空数据库...")
        session.run("MATCH (n) DETACH DELETE n")
        print("数据库已清空")


def import_nodes_items(driver):
    """导入物品节点"""
    csv_file = EXPORT_DIR / "nodes_items.csv"
    if not csv_file.exists():
        print(f"跳过: {csv_file} 不存在")
        return
    
    with driver.session() as session, open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        batch = []
        count = 0
        
        for row in reader:
            # 处理空值 - EggItemID 可能是浮点数格式如 '13011.0'
            egg_item_id = None
            if row['EggItemID']:
                try:
                    egg_item_id = int(float(row['EggItemID']))
                except (ValueError, TypeError):
                    egg_item_id = None
            
            batch.append({
                'id': int(row['ID']),
                'name': row['Name'],
                'type': float(row['Type']) if row['Type'] else None,
                'disc': row['Disc'] if row['Disc'] else None,
                'getway': row['GetWay'] if row['GetWay'] else None,
                'egg_item_id': egg_item_id
            })
            
            if len(batch) >= BATCH_SIZE:
                session.run("""
                    UNWIND $batch AS row
                    CREATE (n:item {
                        ID: row.id,
                        Name: row.name,
                        Type: row.type,
                        Disc: row.disc,
                        GetWay: row.getway,
                        EggItemID: row.egg_item_id
                    })
                """, batch=batch)
                count += len(batch)
                print(f"  已导入 {count} 个物品节点...")
                batch = []
        
        if batch:
            session.run("""
                UNWIND $batch AS row
                CREATE (n:item {
                    ID: row.id,
                    Name: row.name,
                    Type: row.type,
                    Disc: row.disc,
                    GetWay: row.getway,
                    EggItemID: row.egg_item_id
                })
            """, batch=batch)
            count += len(batch)
        
        print(f"✓ 共导入 {count} 个物品节点")


def import_nodes_blocks(driver):
    """导入方块节点"""
    csv_file = EXPORT_DIR / "nodes_blocks.csv"
    if not csv_file.exists():
        return
    
    with driver.session() as session, open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        batch = []
        count = 0
        
        for row in reader:
            batch.append({
                'id': int(row['ID']),
                'mine_tool': float(row['MineTool']) if row['MineTool'] else None,
                'tool_level': float(row['ToolLevel']) if row['ToolLevel'] else None
            })
            
            if len(batch) >= BATCH_SIZE:
                session.run("""
                    UNWIND $batch AS row
                    CREATE (n:block {
                        ID: row.id,
                        MineTool: row.mine_tool,
                        ToolLevel: row.tool_level
                    })
                """, batch=batch)
                count += len(batch)
                print(f"  已导入 {count} 个方块节点...")
                batch = []
        
        if batch:
            session.run("""
                UNWIND $batch AS row
                CREATE (n:block {
                    ID: row.id,
                    MineTool: row.mine_tool,
                    ToolLevel: row.tool_level
                })
            """, batch=batch)
            count += len(batch)
        
        print(f"✓ 共导入 {count} 个方块节点")


def import_nodes_monsters(driver):
    """导入生物节点"""
    csv_file = EXPORT_DIR / "nodes_monsters.csv"
    if not csv_file.exists():
        return
    
    with driver.session() as session, open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        batch = []
        count = 0
        
        for row in reader:
            batch.append({
                'id': int(row['ID']),
                'life': float(row['Life']) if row['Life'] else None,
                'attack': float(row['Attack']) if row['Attack'] else None
            })
            
            if len(batch) >= BATCH_SIZE:
                session.run("""
                    UNWIND $batch AS row
                    CREATE (n:monster {
                        ID: row.id,
                        Life: row.life,
                        Attack: row.attack
                    })
                """, batch=batch)
                count += len(batch)
                print(f"  已导入 {count} 个生物节点...")
                batch = []
        
        if batch:
            session.run("""
                UNWIND $batch AS row
                CREATE (n:monster {
                    ID: row.id,
                    Life: row.life,
                    Attack: row.attack
                })
            """, batch=batch)
            count += len(batch)
        
        print(f"✓ 共导入 {count} 个生物节点")


def import_nodes_groups(driver):
    """导入分组节点"""
    csv_file = EXPORT_DIR / "nodes_groups.csv"
    if not csv_file.exists():
        return
    
    with driver.session() as session, open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        batch = []
        count = 0
        
        for row in reader:
            batch.append({'id': int(row['ItemGroup'])})  # 列名是 ItemGroup
            
            if len(batch) >= BATCH_SIZE:
                session.run("""
                    UNWIND $batch AS row
                    CREATE (n:group {ID: row.id})
                """, batch=batch)
                count += len(batch)
                batch = []
        
        if batch:
            session.run("""
                UNWIND $batch AS row
                CREATE (n:group {ID: row.id})
            """, batch=batch)
            count += len(batch)
        
        print(f"✓ 共导入 {count} 个分组节点")


def import_nodes_recipes(driver):
    """导入配方节点"""
    csv_file = EXPORT_DIR / "nodes_recipes.csv"
    if not csv_file.exists():
        return
    
    with driver.session() as session, open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        batch = []
        count = 0
        
        for row in reader:
            batch.append({
                'id': safe_int(row['ID']),
                'is_follow_me': safe_int(row['IsFollowMe']),
                'station_label': row['StationLabel'] if row['StationLabel'] else None
            })
            
            if len(batch) >= BATCH_SIZE:
                session.run("""
                    UNWIND $batch AS row
                    CREATE (n:recipe {
                        ID: row.id,
                        IsFollowMe: row.is_follow_me,
                        StationLabel: row.station_label
                    })
                """, batch=batch)
                count += len(batch)
                batch = []
        
        if batch:
            session.run("""
                UNWIND $batch AS row
                CREATE (n:recipe {
                    ID: row.id,
                    IsFollowMe: row.is_follow_me,
                    StationLabel: row.station_label
                })
            """, batch=batch)
            count += len(batch)
        
        print(f"✓ 共导入 {count} 个配方节点")


def import_relationships(driver, rel_name, rel_type, from_label, to_label, csv_mapping):
    """通用关系导入函数"""
    csv_file = EXPORT_DIR / f"rel_{rel_name}.csv"
    if not csv_file.exists():
        return 0
    
    with driver.session() as session, open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        batch = []
        count = 0
        
        for row in reader:
            data = {}
            for key, value in csv_mapping.items():
                if value in row and row[value]:
                    # 使用 safe_int 处理可能为浮点数的整数
                    if key in ['from_id', 'to_id', 'count', 'containerId', 'CountMin', 'CountMax', 'Prob']:
                        data[key] = safe_int(row[value])
                    else:
                        data[key] = row[value]
                else:
                    data[key] = None
            batch.append(data)
            
            if len(batch) >= BATCH_SIZE:
                # 构建动态属性字符串
                props = ", ".join([f"{k}: row.{k}" for k in csv_mapping.keys() if k not in ['from_id', 'to_id']])
                if props:
                    query = f"""
                        UNWIND $batch AS row
                        MATCH (a:{from_label} {{ID: row.from_id}})
                        MATCH (b:{to_label} {{ID: row.to_id}})
                        CREATE (a)-[r:{rel_type} {{{props}}}]->(b)
                    """
                else:
                    query = f"""
                        UNWIND $batch AS row
                        MATCH (a:{from_label} {{ID: row.from_id}})
                        MATCH (b:{to_label} {{ID: row.to_id}})
                        CREATE (a)-[r:{rel_type}]->(b)
                    """
                session.run(query, batch=batch)
                count += len(batch)
                print(f"  已导入 {count} 条 {rel_type} 关系...")
                batch = []
        
        if batch:
            props = ", ".join([f"{k}: row.{k}" for k in csv_mapping.keys() if k not in ['from_id', 'to_id']])
            if props:
                query = f"""
                    UNWIND $batch AS row
                    MATCH (a:{from_label} {{ID: row.from_id}})
                    MATCH (b:{to_label} {{ID: row.to_id}})
                    CREATE (a)-[r:{rel_type} {{{props}}}]->(b)
                """
            else:
                query = f"""
                    UNWIND $batch AS row
                    MATCH (a:{from_label} {{ID: row.from_id}})
                    MATCH (b:{to_label} {{ID: row.to_id}})
                    CREATE (a)-[r:{rel_type}]->(b)
                """
            session.run(query, batch=batch)
            count += len(batch)
        
        print(f"✓ 共导入 {count} 条 {rel_type} 关系")
        return count


def main():
    print("=" * 60)
    print("MiniGraDB 数据导入工具")
    print("=" * 60)
    
    try:
        driver = GraphDatabase.driver(URI, auth=AUTH)
        
        # 测试连接
        with driver.session() as session:
            result = session.run("RETURN 1 AS test")
            result.single()
            print("✓ Neo4j 连接成功")
        
        # 清空数据库
        clear_database(driver)
        
        print("\n--- 导入节点 ---")
        import_nodes_items(driver)
        import_nodes_blocks(driver)
        import_nodes_monsters(driver)
        import_nodes_groups(driver)
        import_nodes_recipes(driver)
        
        print("\n--- 导入关系 ---")
        # 导入各种关系
        import_relationships(driver, "in_group", "IN_GROUP", "item", "group", 
                            {'from_id': 'itemId', 'to_id': 'groupId'})
        
        import_relationships(driver, "block_handminedrops", "HAND_MINE_DROPS", "block", "item",
                            {'from_id': 'blockId', 'to_id': 'itemId', 'Prob': 'Prob', 'CountMin': 'CountMin', 'CountMax': 'CountMax'})
        
        import_relationships(driver, "block_toolminedrops", "TOOL_MINE_DROPS", "block", "item",
                            {'from_id': 'blockId', 'to_id': 'itemId', 'Prob': 'Prob', 'CountMin': 'CountMin', 'CountMax': 'CountMax'})
        
        import_relationships(driver, "block_precisedrop", "PRECISE_DROP", "block", "item",
                            {'from_id': 'blockId', 'to_id': 'itemId'})
        
        import_relationships(driver, "monster_drops", "DROPS", "monster", "item",
                            {'from_id': 'monsterId', 'to_id': 'itemId', 'Prob': 'Prob', 'CountMin': 'CountMin', 'CountMax': 'CountMax', 'Conditions': 'Conditions', 'Source': 'Source'})
        
        import_relationships(driver, "recipe_consumes", "CONSUMES", "recipe", "item",
                            {'from_id': 'recipeId', 'to_id': 'targetId', 'Count': 'count', 'ContainerID': 'containerId'})
        
        import_relationships(driver, "recipe_produces", "PRODUCES", "recipe", "item",
                            {'from_id': 'recipeId', 'to_id': 'targetId', 'Count': 'count'})
        
        import_relationships(driver, "item_place", "PLACE", "item", "block",
                            {'from_id': 'itemId', 'to_id': 'blockId'})
        
        import_relationships(driver, "item_summon", "SUMMON", "item", "monster",
                            {'from_id': 'itemId', 'to_id': 'monsterId'})
        
        import_relationships(driver, "item_fuel_for_device", "FUEL_FOR", "item", "item",
                            {'from_id': 'itemId', 'to_id': 'Device', 'Heat': 'Heat', 'ProvideHeat': 'ProvideHeat', 'Combustion': 'Combustion'})
        
        print("\n--- 统计 ---")
        with driver.session() as session:
            # 统计节点
            result = session.run("MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count ORDER BY count DESC")
            print("节点统计:")
            for record in result:
                print(f"  {record['label']}: {record['count']}")
            
            # 统计关系
            result = session.run("MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS count ORDER BY count DESC")
            print("\n关系统计:")
            for record in result:
                print(f"  {record['type']}: {record['count']}")
        
        print("\n✓ 数据导入完成!")
        driver.close()
        
    except Exception as e:
        print(f"✗ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

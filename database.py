import os
import apsw
import json
import shutil

DATA_PATH = "D:/app-data/umapd/Umamusume/umamusume_Data/Persistent"
DB_KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"

def db2list(db_name="meta"):
    db_path = os.path.join(DATA_PATH, db_name)
    if not os.path.exists(db_path):
        print(f"错误：数据库文件 {db_path} 不存在。请检查 DATA_PATH 和 db_name。")
        return []
    try:
        conn = apsw.Connection(db_path, flags=apsw.SQLITE_OPEN_READWRITE)
        conn.pragma("hexkey", DB_KEY)
        cursor = conn.cursor()

        data_list = []
        for m, n, h, d, e in cursor.execute("SELECT m,n,h,d,e FROM a"):
            if d:
                data_list.append({
                    "type": m, 
                    "path": n, 
                    "url": h, 
                    "dependencies": d.split(";"), 
                    "key": e
                })
            else:
                data_list.append({
                    "type": m, 
                    "path": n, 
                    "url": h, 
                    "key": e
                })
        
        conn.close()
        print(f"成功从数据库读取 {len(data_list)} 条数据")
        return data_list
    except apsw.NotADBError:
        print(f"错误：文件 {db_path} 不是一个有效的数据库文件。")
        return []
    except Exception as e:
        print(f"从数据库读取数据时发生错误：{str(e)}")
        return []

def list2json(data_list, json_file="meta.json"):
    try:
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data_list, f, ensure_ascii=False, indent=4)
        print(f"成功将 {len(data_list)} 条数据写入 {json_file}")
    except Exception as e:
        print(f"写入JSON文件 {json_file} 时出错：{str(e)}")


def json2list(json_file="meta.json"):
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data_list = json.load(f)
        print(f"成功从{json_file}读取 {len(data_list)} 条数据")
        return data_list
    except FileNotFoundError:
        print(f"错误：未找到JSON文件 {json_file}")
        return []
    except json.JSONDecodeError:
        print(f"错误：{json_file} 不是有效的JSON格式文件")
        return []


def list2db(data_list, db_name="meta"):
    if not data_list:
        print("无数据可写入数据库")
        return
        
    conn = apsw.Connection(os.path.join(DATA_PATH, db_name), flags=apsw.SQLITE_OPEN_READWRITE)
    conn.pragma("hexkey", DB_KEY)
    cursor = conn.cursor()

    try:
        with conn:
            cursor.execute("DELETE FROM a")
            for item in data_list:
                m = item.get("type")
                n = item.get("path")
                h = item.get("url")
                
                dependencies_list = item.get("dependencies", [])
                d = ";".join(dependencies_list) if dependencies_list else None
                e = item.get("key")

                cursor.execute(
                    """
                    INSERT INTO a (m, n, h, d, e) 
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (m, n, h, d, e)
                )
        
        print(f"成功将 {len(data_list)} 条数据写入数据库")
    except apsw.Error as e:
        print(f"数据库写入错误：{str(e)}")
    finally:
        conn.close()

def backup_db(db_name="meta"):
    backup_path = os.path.join(DATA_PATH, f"{db_name}_backup")
    shutil.copy2(os.path.join(DATA_PATH, db_name), backup_path)
    print(f"数据库 {db_name} 已备份至 {backup_path}")

def recover_db(db_name="meta"):
    backup_path = os.path.join(DATA_PATH, f"{db_name}_backup")
    shutil.copy2(backup_path, os.path.join(DATA_PATH, db_name))
    print(f"数据库 {db_name} 已从备份恢复")

def get_all_dependencies(data_list, target_path):
    path_to_dependencies = {}
    for item in data_list:
        if "path" in item and "dependencies" in item:
            path_to_dependencies[item["path"]] = item["dependencies"]

    all_deps = set()
    paths_to_process = [target_path]

    while paths_to_process:
        current_path = paths_to_process.pop(0)

        if current_path in path_to_dependencies:
            for dep in path_to_dependencies[current_path]:
                if dep not in all_deps:
                    all_deps.add(dep)
                    paths_to_process.append(dep)
    sorted_deps = sorted(all_deps)
    return sorted_deps

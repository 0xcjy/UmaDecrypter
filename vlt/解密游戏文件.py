import apsw
import apsw.bestpractice
import json
import os
import time
import itertools
import numba
import numpy as np
import gc

DB_KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
AB_KEY = "532B4631E4A7B9473E7CFB"
JSON_FILE = "meta.json"
CONFIG_FILE = "config.json"
DATA_PATH = ""
DEC_STRATEGY = ""
LAST_INDEX = 0

def info():
    print("使用的 APSW 文件", apsw.__file__)
    print("APSW 版本", apsw.apsw_version())
    print("SQLite 头文件版本", apsw.SQLITE_VERSION_NUMBER)
    print("SQLite 库版本", apsw.sqlite_lib_version())
    print("是否使用合并包", apsw.using_amalgamation)
    print("数据库密钥", DB_KEY)
    print("AssetBundle 密钥", AB_KEY)

def connect(db_path="meta"): # 连接数据库
    connection = apsw.Connection(db_path, flags=apsw.SQLITE_OPEN_READONLY)
    connection.pragma("hexkey", DB_KEY)
    print("数据库连接成功, 接下来要稍等一会")
    return connection

def export_as_json(connection): # 导出元数据为 JSON 文件
    cursor = connection.cursor()
    lis = []
    for m,n,h,d,e in cursor.execute("SELECT m,n,h,d,e FROM a"):
        if(e):
            e = get_final_key(int(e)).hex()
        if(d):
            lis.append({"type": m, "path": n, "url": h, "prerequisites": d, "key": e})
        else:
            lis.append({"type": m, "path": n, "url": h, "key": e})
    with open(JSON_FILE, "w") as f:
        json.dump(lis, f, indent=4)
    print(JSON_FILE, "导出成功")

def export_to_unencrypted_db(encrypted_db_path, output_db_path="unencrypted_meta.db"): # 导出加密数据库内容到未加密数据库
    # 连接到加密数据库
    encrypted_conn = connect(encrypted_db_path)
    encrypted_cursor = encrypted_conn.cursor()

    # 创建一个新的未加密数据库
    unencrypted_conn = apsw.Connection(output_db_path)
    unencrypted_cursor = unencrypted_conn.cursor()

    # 获取所有表名
    encrypted_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = encrypted_cursor.fetchall()

    print("正在计算总行数...")
    total_rows_to_process = 0
    for table_name_tuple in tables:
        table_name = table_name_tuple[0]
        encrypted_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = encrypted_cursor.fetchone()[0]
        total_rows_to_process += count
        print(f"  表 '{table_name}' 包含 {count} 行。")
    print(f"总计 {total_rows_to_process} 行数据需要处理。")

    processed_rows = 0
    start_time = time.time()
    PROGRESS_UPDATE_INTERVAL = 1000 # 每处理 1000 行更新一次进度

    for table_name_tuple in tables:
        table_name = table_name_tuple[0]
        print(f"正在处理表: {table_name}")

        # 获取表结构
        encrypted_cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = encrypted_cursor.fetchall()
        
        # 构建 CREATE TABLE 语句
        columns_defs = []
        for col in columns_info:
            col_name = col[1]
            col_type = col[2]
            columns_defs.append(f"{col_name} {col_type}")
        
        create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns_defs)})"
        unencrypted_cursor.execute(create_table_sql)

        # 传输数据
        encrypted_cursor.execute(f"SELECT * FROM {table_name}")
        
        rows_buffer = []
        current_table_rows_processed = 0
        
        for row in encrypted_cursor: # 直接迭代游标
            rows_buffer.append(row)
            current_table_rows_processed += 1
            
            if len(rows_buffer) >= PROGRESS_UPDATE_INTERVAL:
                placeholders = ', '.join(['?'] * len(columns_info))
                insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
                unencrypted_cursor.executemany(insert_sql, rows_buffer)
                rows_buffer = [] # 清空缓冲区
                
                processed_rows += PROGRESS_UPDATE_INTERVAL
                if total_rows_to_process > 0:
                    progress_percent = (processed_rows / total_rows_to_process) * 100
                    elapsed_time = time.time() - start_time
                    print(f"  进度: {processed_rows}/{total_rows_to_process} ({progress_percent:.2f}%) 已用时间: {elapsed_time:.2f}s (表 '{table_name}')")
                
        # 插入缓冲区中剩余的行
        if rows_buffer:
            placeholders = ', '.join(['?'] * len(columns_info))
            insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
            unencrypted_cursor.executemany(insert_sql, rows_buffer)
            processed_rows += len(rows_buffer) # 将剩余行添加到总已处理行数
            
        # 打印该表的最终进度
        if total_rows_to_process > 0:
            progress_percent = (processed_rows / total_rows_to_process) * 100
            elapsed_time = time.time() - start_time
            print(f"  表 '{table_name}' 处理完成。总进度: {processed_rows}/{total_rows_to_process} ({progress_percent:.2f}%) 已用时间: {elapsed_time:.2f}s")
        else:
            print("  没有数据需要处理。")
    
    unencrypted_conn.close()
    encrypted_conn.close()
    print(f"数据已成功导出到未加密数据库: {output_db_path}")

def get_final_key(key): # 获取最终的 AssetBundle 密钥
    base_key = bytes.fromhex(AB_KEY)
    keys = key.to_bytes(8, byteorder='little', signed=True)
    final_key = []
    base_len = len(base_key)

    for i in range(base_len):
        for j in range(8):
            final_key.append(base_key[i] ^ keys[j])
    return bytes(final_key)

@numba.njit(cache=True) # 编译为 Numba JIT 函数, 加速
def decrypt_core_inplace(data_np: np.ndarray, key_np: np.ndarray): # 原地解密核心函数
    key_len = len(key_np)
    for i in range(256, len(data_np)):
        data_np[i] ^= key_np[i % key_len]

def decrypt_ab(ab_path, key): # 解密单个 AssetBundle 文件
    if not os.path.isfile(ab_path):
        return None
    with open(ab_path, "rb") as f:
        data = bytearray(f.read())
    if not key or len(data) <= 256:
        return data
    
    key_bytes = bytes.fromhex(key)
    key_np = np.frombuffer(key_bytes, dtype=np.uint8)
    data_np = np.frombuffer(data, dtype=np.uint8)
    decrypt_core_inplace(data_np, key_np)
    return data

def decrypt(limit, output_interval, start_index, config): # 解密 limit 个文件
    with open(JSON_FILE, "r") as f:
        meta = json.load(f)
    
    total_files = len(meta)
    print("元数据共", total_files, "条, 加载成功")
    
    if not limit or limit <= 0:
        limit = total_files - start_index
    
    limit = min(limit, total_files - start_index)
    
    start_time = time.time() # 记录开始时间
    last_output_time = start_time
    cnt = 0
    continue_cnt = 0
    actual_decrypted_cnt = 0
    actual_decrypted_time = 0.0

    # 使用 islice 避免大列表切片开销
    for i in itertools.islice(meta, start_index, start_index + limit):
        loop_start = time.time()
        continue_flag = False
        if i["path"].startswith("//"):
            i["path"] = i["path"][2:] + "." + i["type"]
        
        ab_path = os.path.join(DATA_PATH, "dat", i["url"][:2], i["url"])
        output_path = os.path.join("dat", i["path"])
        
        # 预先检查
        if not os.path.isfile(ab_path):
            print(f"源文件不存在: \"{ab_path}\", 跳过解密")
            continue_cnt += 1
            cnt += 1
            continue
            
        if DEC_STRATEGY == "1" and os.path.isfile(output_path):
            continue_cnt += 1
            cnt += 1
            continue

        # 执行解密
        decrypted_data = decrypt_ab(ab_path, i["key"])
        if decrypted_data is not None:
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            with open(output_path, "wb") as f:
                f.write(decrypted_data)
            
            actual_decrypted_cnt += 1
            actual_decrypted_time += (time.time() - loop_start)
            
            # 及时释放内存
            del decrypted_data
        
        cnt += 1
        
        if cnt % output_interval == 0 or cnt == limit:
            elapsed_total = time.time() - start_time
            
            # 计算预计剩余时间：
            # 如果有实际解密的文件，按实际解密的平均速度计算
            # 否则按总平均速度（包含跳过的文件）计算
            if actual_decrypted_cnt > 0:
                avg_work_time = actual_decrypted_time / actual_decrypted_cnt
                # 预估剩余需要解密的文件数 (假设剩余比例与已处理比例一致，或者简单点按剩余总数算)
                remaining_files = limit - cnt
                # 估算剩余文件中，有多少是需要真正解密的 (剔除掉可能跳过的)
                work_ratio = actual_decrypted_cnt / cnt
                estimated_remaining_work = remaining_files * work_ratio
                remaining_time = avg_work_time * estimated_remaining_work
            else:
                avg_time_per_file = elapsed_total / cnt
                remaining_time = avg_time_per_file * (limit - cnt)

            print(f"({cnt}/{limit}) 最近保存:\"{output_path}\", 本轮跳过{continue_cnt}个")
            print(f"已用总时间: {elapsed_total:.2f}s, 实际解密耗时: {actual_decrypted_time:.2f}s, 预计剩余: {remaining_time:.2f}s")
            
            continue_cnt = 0
            # 定期清理内存碎片
            if cnt % (output_interval * 5) == 0:
                gc.collect()
            
            # 保存进度
            config["last_index"] = start_index + cnt
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=4)

        if cnt >= limit:
            break

if __name__ == "__main__":
    info()
    apsw.bestpractice.apply(apsw.bestpractice.recommended)

    if not os.path.isfile(CONFIG_FILE):
        print(CONFIG_FILE, "配置文件不存在,开始创建")
        data_path = input("请输入游戏文件路径 (此路径应该包含 umamusume.exe, 使用反斜杠\\): ")
        data_path = os.path.join(data_path, "umamusume_Data\\Persistent")
        decryption_strategy = ""
        while decryption_strategy not in ["1", "2"]:
            decryption_strategy = input("请选择解密策略 (1: 跳过已存在文件, 2: 覆盖已存在文件, 默认: 1): ").lower() or "1"
        with open(CONFIG_FILE, "w") as f:
            json.dump({"data_path": data_path, "decryption_strategy": decryption_strategy}, f, indent=4)
        print(CONFIG_FILE, "创建成功")
    else:
        print(CONFIG_FILE, "配置文件存在")

    config = json.load(open(CONFIG_FILE))
    DATA_PATH = config["data_path"]
    if "decryption_strategy" not in config:
        decryption_strategy = ""
        while decryption_strategy not in ["1", "2"]:
            decryption_strategy = input("请选择解密策略 (1: 跳过已存在文件, 2: 覆盖已存在文件, 默认: 1): ").lower() or "1"
        config["decryption_strategy"] = decryption_strategy
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    DEC_STRATEGY = config["decryption_strategy"]
    print("输出策略: ",DEC_STRATEGY)

    if "last_index" not in config:
        config["last_index"] = 0
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    LAST_INDEX = config["last_index"]

    if os.path.isfile(os.path.join(os.path.dirname(os.path.dirname(DATA_PATH)), "umamusume.exe")):
        print("游戏文件路径检测通过")
    else:
        print("游戏文件路径错误")
        exit(1)
    
    if not os.path.isfile(JSON_FILE):
        print(JSON_FILE, "元数据文件不存在,开始创建")
        export_as_json(connect(os.path.join(DATA_PATH, "meta")))  
    else:
        print(JSON_FILE, "元数据文件存在")
    
    action = input("请选择操作 (1: 解密文件): ") or "1"

    if action == "1":
        start_index = int(input(f"请输入你要解密的文件起始索引 (默认是 {LAST_INDEX}): ") or str(LAST_INDEX))
        limit = int(input("请输入你要解密的文件数量 (输入 0 代表解密所有文件): ") or "0")
        output_interval = int(input("请输入调试信息输出间隔 (默认是 1000): ") or "1000")
        decrypt(limit, output_interval = output_interval, start_index = start_index, config = config)
        print("解密完成")
    elif action == "2":
        output_db_name = input("请输入未加密数据库的文件名 (默认: unencrypted_meta.db): ") or "unencrypted_meta.db"
        export_to_unencrypted_db(os.path.join(DATA_PATH, "meta"), output_db_name)
        print("导出未加密数据库完成")
    else:
        print("无效的操作选择。")

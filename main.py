print("使用前确认: \n1. 安装了 Umamusume DMM 版游戏\n2. 游戏没在运行\n3. 安装了 apsw 库\n4. 此 py 文件放置在空间充足的空目录下")
input("确认无误后, 按任意键继续...")

import apsw
import apsw.bestpractice
import json
import os

DB_KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
AB_KEY = "532B4631E4A7B9473E7CFB"
JSON_FILE = "meta.json"
CONFIG_FILE = "config.json"
DATA_PATH = ""

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

def get_final_key(key): # 获取最终的 AssetBundle 密钥
    base_key = bytes.fromhex(AB_KEY)
    keys = key.to_bytes(8, byteorder='little', signed=True)
    final_key = []
    base_len = len(base_key)

    for i in range(base_len):
        for j in range(8):
            final_key.append(base_key[i] ^ keys[j])
    return bytes(final_key)

def decrypt_ab(ab_path, key): # 解密单个 AssetBundle 文件
    with open(ab_path, "rb") as f:
        data = f.read()
    if not key:
        return data
    if len(data) <= 256:
        return data
    key = bytes.fromhex(key)
    decrypted_data = bytearray()
    for i in range(len(data)):
        decrypted_data.append(data[i] ^ key[i % len(key)])
    return bytes(decrypted_data)

def decrypt(limit): # 解密 limit 个文件
    meta = json.load(open(JSON_FILE))
    print("元数据共", len(meta), "条, 加载成功")
    cnt = 0
    for i in meta:
        if i["path"].startswith("//"):
            i["path"] = os.path.join("0", i["path"][2:])
        ab_path = os.path.join(DATA_PATH, "dat", i["url"][:2], i["url"])
        output_path = os.path.join("dat", i["path"])
        decrypted_data = decrypt_ab(ab_path, i["key"])
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        with open(output_path, "wb") as f:
            f.write(decrypted_data)
        cnt += 1
        print("(" + str(cnt) + ") 源文件:\"" + ab_path + "\" 解密成功, 已保存为\"" + output_path + "\"")
        if cnt >= limit:
            break

if __name__ == "__main__":
    info()
    apsw.bestpractice.apply(apsw.bestpractice.recommended)

    if not os.path.isfile(CONFIG_FILE):
        print(CONFIG_FILE, "配置文件不存在,开始创建")
        data_path = input("请输入游戏文件路径 (此路径应该包含 umamusume.exe, 使用反斜杠\\): ")
        data_path = os.path.join(data_path, "umamusume_Data\\Persistent")
        with open(CONFIG_FILE, "w") as f:
            json.dump({"data_path": data_path}, f, indent=4)
        print(CONFIG_FILE, "创建成功")
    else:
        print(CONFIG_FILE, "配置文件存在")

    config = json.load(open(CONFIG_FILE))
    DATA_PATH = config["data_path"]

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

    limit = int(input("请输入你要解密的文件数量: "))
    decrypt(limit)
    print("解密完成")

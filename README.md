# UmaDecrypter

## 介绍

某游戏的解密工具，解密逻辑来自 [UmaViewer](https://github.com/katboi01/UmaViewer)。

可以把加密的 AssetBundle 资源破解，然后便可以在 Unity 引擎中加载。

此工具有两个语言的版本，Python 版和 C++ 版。通常 C++ 版速度会快一点。

## Python 版
### 使用前确认  
1. 安装了 Python 3
2. 安装了此游戏的日服 Windows 版
3. 游戏没在运行
4. 安装了 apsw-sqlite3mc 库
5. main.py 文件放置在空间充足的文件夹下（因为要储存解密后的游戏文件）

### 使用方法

1. 安装依赖库
```bash
pip install apsw-sqlite3mc -i https://pypi.tuna.tsinghua.edu.cn/simple
```

这是此程序用到的所有库，哪个没有就安装哪个。
```python
import apsw
import json
import os
import time
import numba
import numpy as np
```

2. 运行程序
```bash
python main.py
```

### 可能的输出

```plain
使用前确认: 
1. 安装了 Umamusume DMM 版游戏
2. 游戏没在运行
3. 安装了 apsw 库
4. 此 py 文件放置在空间充足的空目录下
确认无误后, 按任意键继续...
使用的 APSW 文件 C:\Users\admin\AppData\Local\Programs\Python\Python313\Lib\site-packages\apsw\__init__.cp313-win_amd64.pyd
APSW 版本 3.51.2.0
SQLite 头文件版本 3051002
SQLite 库版本 3.51.2
是否使用合并包 True
数据库密钥 ************************************
AssetBundle 密钥 ************************
config.json 配置文件存在
游戏文件路径检测通过
meta.json 元数据文件存在
请输入你要解密的文件起始索引 (默认是 0):
请输入你要解密的文件数量 (输入 0 代表解密所有文件):
请输入调试信息输出间隔 (默认是 1000):
(1000/114514) 源文件:"C:\AppData\Umamusume\umamusume_Data\Persistent\dat\6O\6OSRC3HDBVREXWNSJCT4YZU6ZCUHFGA7" 解密成功, 已保存为"dat\sound\c\snd_voi_story_100002002.awb", 跳过0个文件
已用时间: 11.45 秒, 预计剩余时间: 11451.4 秒
(2000/114514) 源文件:"C:\AppData\Umamusume\umamusume_Data\Persistent\dat\3M\3MZJCPGIB6IHQEA3YZTWZDWBP4ICCZIC" 解密成功, 已保存为"dat\sound\j\snd_voi_jky_race_02_04507.acb", 跳过0个文件
已用时间: 45.14 秒, 预计剩余时间: 1141.45 秒
......
```

## C++ 版
感谢 Gemini-3-Pro 的 python 转 c++。

### 使用前确认
1. 安装了此游戏的日服 Windows 版
2. 游戏没在运行
3. 文件夹空间充足（因为要储存解密后的游戏文件）
4. **注意: 你需要先使用 Python 版本，生成 `meta.json` 和 `config.json`，之后才可以使用 C++ 版本!!!**

### 使用方法

在 Releases 页面下载 `UmaDecryptor.exe`，双击 `UmaDecryptor.exe` 运行即可。

### 编译方法（如果你想自己编译）
需要包含 `json.hpp`。
```bash
g++ -std=c++17 -o UmaDecryptor main.cpp -lstdc++fs
```

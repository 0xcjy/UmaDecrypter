# UmaDecryptor

## 介绍

某游戏的解密工具，解密逻辑来自 [UmaViewer](https://github.com/katboi01/UmaViewer)。

可以把加密的 AssetBundle 资源破解，然后便可以在 Unity 引擎中加载。

## Python 版
### 使用前确认  
1. 安装了 Python 3
2. 安装了此游戏的日服 Windows 版
3. 游戏没在运行
4. 安装了 `apsw-sqlite3mc` 和 `numba` 库
5. `UmaDecryptor.py` 文件放置在空间充足的文件夹下（因为要储存解密后的游戏文件）

### 使用方法

1. 安装依赖库
```bash
pip install apsw-sqlite3mc -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install numba -i https://pypi.tuna.tsinghua.edu.cn/simple
```

1. 运行程序
```bash
python UmaDecryptor.py
```

### 可能的输出

```plain
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
import requests
from bs4 import BeautifulSoup
import os
import time

def download_uma_images(save_dir):
    """
    下载指定范围的赛马娘图片
    :param save_dir: 图片保存目录
    """
    # 1. 确保保存目录存在
    os.makedirs(save_dir, exist_ok=True)
    
    # 2. 请求头（模拟浏览器，避免被反爬）
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Referer': 'https://wiki.biligame.com/'
    }
    
    # 3. 遍历1001到1137的4位数字
    for num in range(1001, 1138):  # range左闭右开，所以结束值是1138
        try:
            # 构造目标URL（补零确保是4位数字，比如1001不会变成101）
            target_url = f"https://wiki.biligame.com/umamusume/%E6%96%87%E4%BB%B6:Jsf_{num:04d}01.png"
            
            # 请求页面，设置超时防止卡死
            response = requests.get(target_url, headers=headers, timeout=15)
            response.raise_for_status()  # 抛出HTTP错误（如404、500）
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找class为fullImageLink的div
            full_image_div = soup.find('div', class_='fullImageLink')
            if not full_image_div:
                print(f"【{num}】未找到class=fullImageLink的div，跳过")
                continue
            
            # 查找div下第一个a标签
            a_tag = full_image_div.find('a')
            if not a_tag or not a_tag.get('href'):
                print(f"【{num}】未找到有效a标签或href，跳过")
                continue
            
            # 获取图片真实URL
            img_url = a_tag['href']
            # 处理相对路径（如果有的话）
            if img_url.startswith('/'):
                img_url = f"https://wiki.biligame.com{img_url}"
            
            # 下载图片（stream=True适合大文件，避免内存溢出）
            img_response = requests.get(img_url, headers=headers, stream=True, timeout=15)
            img_response.raise_for_status()
            
            # 保存图片到指定目录，命名为4位数字.png
            save_path = os.path.join(save_dir, f"{num}.png")
            with open(save_path, 'wb') as f:
                for chunk in img_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"【{num}】图片下载成功，保存至：{save_path}")
            
            # 轻微延时，避免请求过快被封禁
            time.sleep(0.5)
            
        except requests.exceptions.RequestException as e:
            print(f"【{num}】请求失败：{str(e)}")
        except Exception as e:
            print(f"【{num}】未知错误：{str(e)}")

if __name__ == "__main__":
    # 替换为你想要保存图片的目录（绝对路径/相对路径都可以）
    SAVE_DIRECTORY = "./uma_images"
    download_uma_images(SAVE_DIRECTORY)

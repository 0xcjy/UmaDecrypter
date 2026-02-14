import requests
from bs4 import BeautifulSoup

def crawl_uma_tr_data():
    # 请求头（模拟浏览器，避免反爬拦截）
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Referer': 'https://wiki.biligame.com/'
    }
    
    # 目标URL
    target_url = "https://wiki.biligame.com/umamusume/%E8%B5%9B%E9%A9%AC%E5%A8%98%E5%9B%BE%E9%89%B4"
    
    # 新增：创建集合用于存储已输出的内容，利用集合自动去重的特性
    output_set = set()
    
    try:
        # 发送请求并处理响应
        response = requests.get(target_url, headers=headers, timeout=20)
        response.raise_for_status()  # 抛出HTTP错误
        response.encoding = response.apparent_encoding  # 自动识别编码，避免乱码
        
        # 解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找所有tr元素
        all_tr = soup.find_all('tr')
        
        # 遍历每个tr元素，筛选符合条件的
        for tr in all_tr:
            # 获取data-param1属性值
            data_param1 = tr.get('data-param1')
            # 检查属性是否存在，且值在1-3之间（字符串/数字都兼容）
            if data_param1 and data_param1.strip() in ['1', '2', '3']:
                # 找到该tr下所有a元素
                a_tags = tr.find_all('a')
                # 检查是否有至少4个a元素（索引从0开始，第4个对应索引3）
                if len(a_tags) >= 4:
                    # 提取第4个a元素的文本内容
                    fourth_a_text = a_tags[3].get_text(strip=True)
                    # 新增：判断内容是否未在集合中，未存在则输出并加入集合
                    if fourth_a_text and fourth_a_text not in output_set:
                        print(fourth_a_text)
                        output_set.add(fourth_a_text)
                    
    except Exception:
        # 捕获所有异常，不输出任何调试信息
        pass

if __name__ == "__main__":
    crawl_uma_tr_data()

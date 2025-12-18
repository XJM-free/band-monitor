import feedparser
import requests
import urllib.parse
import os
from datetime import datetime
from time import mktime

# --- 配置区 ---
# Server酱 Key
SC_KEY = os.environ.get("SC_KEY")

# --- 核心代码 ---

def get_band_list():
    """读取 bands.txt 文件，自动生成搜索关键词"""
    bands = []
    try:
        # 读取同目录下的 bands.txt
        with open('bands.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                name = line.strip()
                if name: # 排除空行
                    # 自动生成关键词：乐队名 + 巡演/演出/音乐节
                    bands.append({
                        "name": name,
                        "keyword": f"{name} 巡演 OR 演出 OR 音乐节"
                    })
        print(f"📋 已加载 {len(bands)} 个关注对象: {[b['name'] for b in bands]}")
        return bands
    except FileNotFoundError:
        print("❌ 错误: 找不到 bands.txt 文件！")
        return []

def send_wechat(title, content):
    if not SC_KEY:
        print("⚠️ 未配置 Server酱 Key，无法推送")
        return
    
    url = f"https://sctapi.ftqq.com/{SC_KEY}.send"
    data = {"title": title, "desp": content}
    try:
        requests.post(url, data=data)
        print("✅ 微信推送已发送")
    except Exception as e:
        print(f"❌ 推送失败: {e}")

def check_google_news():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🌍 开始执行巡演监控...")
    
    targets = get_band_list()
    if not targets:
        return

    msg_content = ""
    total_count = 0

    for item in targets:
        encoded_keyword = urllib.parse.quote(item['keyword'])
        url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=zh-CN&gl=CN&ceid=CN:zh-CN"
        
        try:
            feed = feedparser.parse(url)
            
            # 只有当抓取到新闻时，才把这个乐队的标题加进去
            # 避免日报里出现一堆“暂无消息”的空标题
            if feed.entries:
                band_section = ""
                has_news = False
                
                # 只取前 5 条
                for entry in feed.entries[:5]:
                    title = entry.title
                    link = entry.link
                    
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime.fromtimestamp(mktime(entry.published_parsed))
                        date_str = pub_date.strftime('%Y-%m-%d')
                        is_new = (datetime.now() - pub_date).days < 1
                        icon = "🔥" if is_new else "📄"
                    else:
                        date_str = "未知"
                        icon = "📄"

                    band_section += f"{icon} `{date_str}` [{title}]({link})\n\n"
                    has_news = True
                    total_count += 1
                
                if has_news:
                    msg_content += f"### 🎸 {item['name']}\n{band_section}---\n"

        except Exception as e:
            print(f"❌ 出错 [{item['name']}]: {e}")

    if total_count > 0:
        print("🚀 生成日报成功，正在推送...")
        send_wechat(f"🎸 乐队巡演日报 ({datetime.now().strftime('%m-%d')})", msg_content)
    else:
        print("💤 所有关注的乐队今天都很安静")

if __name__ == "__main__":
    check_google_news()

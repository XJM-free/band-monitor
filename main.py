import feedparser
import requests
import urllib.parse
import os
from datetime import datetime
from time import mktime

# --- 配置区 ---
SC_KEY = os.environ.get("SC_KEY")

# --- 核心代码 ---

def get_band_list():
    """读取 bands.txt 文件，自动生成精确搜索关键词"""
    bands = []
    try:
        with open('bands.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                name = line.strip()
                if name:
                    # --- 关键修改在这里 ---
                    # 1. 给名字加上双引号 ""，强制精确匹配
                    # 2. 用括号包裹关键词，确保逻辑正确
                    # 3. 额外加上 "乐队" 关键词作为可选条件，提高权重
                    
                    # 最终生成的搜索词类似： "四月雨" (巡演 OR 演出 OR 音乐节)
                    bands.append({
                        "name": name,
                        "keyword": f'"{name}" (巡演 OR 演出 OR 音乐节)'
                    })
        print(f"📋 已加载 {len(bands)} 个关注对象")
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
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🌍 开始执行精确监控...")
    
    targets = get_band_list()
    if not targets:
        return

    msg_content = ""
    total_count = 0

    for item in targets:
        # 打印一下生成的搜索词，方便调试
        print(f"🔍 正在搜索: {item['keyword']}")
        
        encoded_keyword = urllib.parse.quote(item['keyword'])
        url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=zh-CN&gl=CN&ceid=CN:zh-CN"
        
        try:
            feed = feedparser.parse(url)
            
            if feed.entries:
                band_section = ""
                has_news = False
                
                # 过滤逻辑：再次检查标题里是否真的包含乐队名（双重保险）
                # 注意：这里把乐队名转为小写对比，防止大小写差异
                band_name_lower = item['name'].lower().replace('"', '') 
                
                for entry in feed.entries[:5]:
                    title = entry.title
                    link = entry.link
                    
                    # --- 智能二次过滤 ---
                    # 如果标题里连乐队名字都没有，那肯定是Google搜歪了，直接扔掉
                    if band_name_lower not in title.lower():
                        continue

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
        print("💤 暂无精准匹配的演出消息")

if __name__ == "__main__":
    check_google_news()

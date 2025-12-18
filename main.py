import feedparser
import requests
import os
import re
from datetime import datetime, timedelta
from time import mktime

# --- 配置区 ---
SC_KEY = os.environ.get("SC_KEY")

# 关键词高亮 (虽然是直连，但我们还是想突出显示演出相关的信息)
HIGHLIGHT_KEYWORDS = ["巡演", "演出", "开票", "音乐节", "Live", "预售", "站"]

# --- 核心代码 ---

def get_band_list():
    """读取 bands.txt (格式: 名字,UID)"""
    bands = []
    try:
        with open('bands.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) == 2:
                    bands.append({
                        "name": parts[0].strip(),
                        "uid": parts[1].strip()
                    })
        print(f"📋 已加载 {len(bands)} 个乐队微博")
        return bands
    except FileNotFoundError:
        print("❌ 找不到 bands.txt")
        return []

def clean_html(raw_html):
    """去除微博内容里的 HTML 标签，只保留文字"""
    cleanr = re.compile('<.*?>')
    text = re.sub(cleanr, '', raw_html)
    return text.strip()[:100] + "..." # 只取前100个字预览

def send_wechat(title, content):
    if not SC_KEY:
        print("⚠️ 未配置 Server酱 Key")
        return
    
    url = f"https://sctapi.ftqq.com/{SC_KEY}.send"
    data = {"title": title, "desp": content}
    try:
        requests.post(url, data=data)
        print("✅ 微信推送已发送")
    except Exception as e:
        print(f"❌ 推送失败: {e}")

def check_weibo():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔴 开始抓取微博动态...")
    
    targets = get_band_list()
    if not targets:
        return

    msg_content = ""
    total_count = 0
    
    # 使用 RSSHub 的公共节点 (如果不稳定可以换)
    # GitHub Actions 的服务器在海外，访问 rsshub.app 通常很快
    base_url = "https://rsshub.app/weibo/user/"

    for item in targets:
        url = base_url + item['uid']
        print(f"🔍 正在抓取: {item['name']} (UID: {item['uid']})")
        
        try:
            # 设置超时，防止卡死
            feed = feedparser.parse(url)
            
            if feed.entries:
                band_section = ""
                has_new_info = False
                
                # 只看最近 3 条微博，避免太长
                for entry in feed.entries[:3]:
                    # 微博正文通常在 description 里
                    content_html = entry.description
                    content_text = clean_html(content_html)
                    link = entry.link
                    
                    # 时间处理
                    if hasattr(entry, 'published_parsed'):
                        pub_date = datetime.fromtimestamp(mktime(entry.published_parsed))
                        date_str = pub_date.strftime('%m-%d')
                        
                        # 检查是否是最近 2 天发的
                        is_recent = (datetime.now() - pub_date).days <= 2
                    else:
                        date_str = "未知"
                        is_recent = False

                    # 判定图标
                    icon = "📄"
                    # 如果是最近发的，且包含关键词，给个火
                    if is_recent:
                        icon = "🆕" 
                    if any(k in content_text for k in HIGHLIGHT_KEYWORDS):
                        icon = "🔥" # 只要提到演出，不管时间，都给火

                    # 只有当是新消息，或者包含演出关键词时，才放入日报
                    # (这样可以过滤掉乐队发的无关日常，比如“今天吃了顿好的”)
                    # 如果你想看所有微博，把下面这个 if 去掉即可
                    if is_recent or icon == "🔥":
                        band_section += f"{icon} `{date_str}` [{content_text}]({link})\n\n"
                        has_new_info = True
                        total_count += 1
                
                if has_new_info:
                    msg_content += f"### 🎸 {item['name']}\n{band_section}---\n"

        except Exception as e:
            print(f"❌ 抓取失败 [{item['name']}]: {e}")

    if total_count > 0:
        print("🚀 抓取完成，正在推送...")
        send_wechat(f"🎸 乐队微博动态 ({datetime.now().strftime('%m-%d')})", msg_content)
    else:
        print("💤 关注的乐队最近没有发重要动态")

if __name__ == "__main__":
    check_weibo()

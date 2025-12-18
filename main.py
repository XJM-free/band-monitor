import requests
import os
import time
from datetime import datetime

# --- 配置区 ---

# 你想监控的乐队和对应的微博 UID
TARGETS = [
    {"name": "万能青年旅店", "uid": "1736760581"},
    {"name": "痛仰乐队", "uid": "1662260795"},
]

# Server酱推送 Key (可选，如果不填就只在 GitHub 日志里看)
# 去 https://sct.ftqq.com/ 申请一个 SendKey，免费的
SC_KEY = os.environ.get("SC_KEY") 

# --- 核心代码 ---

def send_wechat(title, content):
    if not SC_KEY:
        print("⚠️ 未配置 Server酱 Key，跳过推送")
        return
    url = f"https://sctapi.ftqq.com/{SC_KEY}.send"
    data = {"title": title, "desp": content}
    try:
        requests.post(url, data=data)
        print("✅ 微信推送已发送")
    except Exception as e:
        print(f"❌ 推送失败: {e}")

def check_weibo():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 开始在 GitHub 服务器上检查...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1",
        "Referer": "https://m.weibo.cn/"
    }

    has_new_info = False
    msg_content = ""

    for band in TARGETS:
        url = f"https://m.weibo.cn/api/container/getIndex?type=uid&value={band['uid']}&containerid=107603{band['uid']}"
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            data = resp.json()
            
            if data.get('ok') != 1:
                print(f"⚠️ [{band['name']}] 接口返回异常")
                continue

            cards = data.get('data', {}).get('cards', [])
            
            # 取最新的一条微博
            for card in cards:
                if card.get('card_type') == 9:
                    mblog = card.get('mblog', {})
                    text = mblog.get('text', '')
                    created_at = mblog.get('created_at')
                    
                    # 简单清洗 HTML 标签
                    clean_text = text.replace('<br />', '\n').split('<')[0]
                    
                    print(f"✅ [{band['name']}] 最新微博 ({created_at}): {clean_text[:30]}...")
                    
                    # 简单的逻辑：如果是“刚刚”或者“几分钟前”发布的，就推送
                    # 这里为了演示，只要包含“巡演”或“演出”就记录下来
                    if "巡演" in text or "演出" in text or "开票" in text:
                        # 这里可以加一个去重逻辑（比如存文件），但在 GitHub Actions 里存文件比较麻烦
                        # 我们可以简单地把最新的这条打印出来，人工判断
                        msg_content += f"## {band['name']}\n时间：{created_at}\n内容：{clean_text}\n[点击查看](https://m.weibo.cn/detail/{mblog['id']})\n\n"
                        has_new_info = True
                    break # 只看最新的一条

        except Exception as e:
            print(f"❌ 检查出错 [{band['name']}]: {e}")
            
    if has_new_info:
        print("🔥 发现演出信息，正在推送...")
        send_wechat("🎸 乐队巡演提醒！", msg_content)
    else:
        print("💤 暂无最新巡演消息")

if __name__ == "__main__":
    check_weibo()

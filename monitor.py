import httpx
import time
import json
import asyncio
import os

# 1. 強化版評分核心邏輯
async def get_instance_score(client, url, inst_type="invidious"):
    score = 0
    metrics = {"api": False, "cors": False, "latency": 0}
    url = url.rstrip('/')
    
    # 【關鍵】模擬真人瀏覽器，避免被 Piped 擋掉
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    start_time = time.perf_counter()
    try:
        # 決定測試路徑
        test_path = "/api/v1/videos/dQw4w9WgXcQ" if inst_type == "invidious" else "/streams/dQw4w9WgXcQ"
        
        # 發送請求
        resp = await client.get(url + test_path, timeout=12.0, follow_redirects=True, headers=headers)
        
        metrics["latency"] = (time.perf_counter() - start_time) * 1000
        
        if resp.status_code == 200:
            data = resp.json()
            # 兼容 Invidious 與 Piped 的資料結構
            if "title" in data:
                metrics["api"] = True
                score += 50  # API 成功基礎分
                
                # CORS 測試 (對於前端跳板至關重要)
                cors_header = resp.headers.get("access-control-allow-origin", "")
                if cors_header == "*" or url in cors_header:
                    metrics["cors"] = True
                    score += 20
        else:
            # 除錯資訊：如果失敗，顯示狀態碼
            print(f" [HTTP {resp.status_code}]", end="")

        # 延遲評分加權
        if metrics["latency"] < 600: score += 30      # 優秀
        elif metrics["latency"] < 1800: score += 15    # 尚可
            
    except Exception as e:
        # 顯示具體錯誤類型 (Timeout, ConnectionError 等)
        error_type = type(e).__name__
        print(f" [{error_type}]", end="")
        return 0, metrics

    return score, metrics

# 2. 執行主邏輯
async def main():
    if not os.path.exists('targets.json'):
        print("CRITICAL: targets.json not found!")
        return

    with open('targets.json', 'r') as f:
        targets = json.load(f)

    print(f"📡 啟動系統監測，目標：{len(targets)} 個站點...")
    
    final_results = []
    
    # 使用無視 SSL 憑證的客戶端
    async with httpx.AsyncClient(verify=False) as client:
        for item in targets:
            url = item['url']
            inst_type = item.get('type', 'invidious')
            
            print(f"正在檢查: {url} ({inst_type})...", end="", flush=True)
            score, metrics = await get_instance_score(client, url, inst_type)
            
            if metrics['api']:
                final_results.append({
                    "url": url,
                    "type": inst_type,
                    "score": score,
                    "latency": f"{int(metrics['latency'])}ms",
                    "cors": metrics['cors'],
                    "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
                })
                print(f" ✅ {score}分")
            else:
                print(" ❌ 失效")

    # 按分數排序
    final_results.sort(key=lambda x: x['score'], reverse=True)

    # 3. 輸出結果
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=4, ensure_ascii=False)
    
    print(f"🎉 更新完畢！已將 {len(final_results)} 個活體實例寫入 data.json")

if __name__ == "__main__":
    asyncio.run(main())
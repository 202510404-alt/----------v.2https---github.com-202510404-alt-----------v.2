import math
import json
import asyncio
import sys
import config

# 1. 환경 감지 및 브릿지 준비
IS_WEB = (sys.platform == "emscripten")
js = None
if IS_WEB:
    try:
        import js
    except: pass

# Pylance 에러 방지용 상수 정의
RANK_CATEGORIES = ["Levels", "Kills", "Bosses", "DifficultyScore", "SurvivalTime"]

def browser_debug(msg, is_error=False):
    full_msg = f"🚀 [Vampire-Bridge] {msg}"
    if IS_WEB and js:
        try:
            if is_error: js.window.console.error(full_msg)
            else: js.window.console.log(full_msg)
        except: pass
    print(full_msg)

# ----------------------------------------------------
# 2. Supabase 통신 함수 (JS 직접 위임 - 에러 수정 버전)
# ----------------------------------------------------
async def _fetch_supabase(endpoint, method, data=None):
    sep = "&" if "?" in endpoint else "?"
    url = f"{config.SUPABASE_URL}/rest/v1/{endpoint}{sep}apikey={config.SUPABASE_KEY}"
    
    if IS_WEB and js:
        try:
            # 🚩 게시판 초기화 (자바스크립트 전역 변수)
            js.window.js_to_py = "WAITING"
            
            js_payload = json.dumps(data) if data else "null"
            
            # 🚩 [수정 완료] 자바스크립트 코드 내에서 'js.'를 뺌
            js_worker = f"""
            (function() {{
                fetch('{url}', {{
                    method: '{method}',
                    headers: {{
                        'apikey': '{config.SUPABASE_KEY}',
                        'Authorization': 'Bearer {config.SUPABASE_KEY}',
                        'Content-Type': 'application/json'
                    }},
                    body: {js_payload}
                }})
                .then(r => r.text())
                .then(txt => {{ window.js_to_py = txt; }}) // ✅ js.window 대신 window 사용
                .catch(e => {{ window.js_to_py = "ERROR:" + e.message; }});
            }})();
            """
            js.window.eval(js_worker)
            
            # 타이밍 동기화 (네가 말한 그 미세한 기다림)
            wait_count = 0
            while str(js.window.js_to_py) == "WAITING":
                await asyncio.sleep(0.01) # 0.01초씩 쉬면서 게시판 감시
                wait_count += 1
                if wait_count > 500:
                    browser_debug("⏱️ 게시판 답장이 안 옴 (타임아웃)", True)
                    return None
            
            res_text = str(js.window.js_to_py)
            
            if res_text.startswith("ERROR:"):
                browser_debug(f"❌ DB 통신 실패: {res_text}", True)
                return None
                
            browser_debug(f"🔥 성공! {len(res_text)} 글자 수신!")
            return res_text

        except Exception as e:
            browser_debug(f"🔥 브릿지 에러: {str(e)}", True)
            return None
    else:
        # 로컬(VSC)용
        import urllib.request
        try:
            req_data = json.dumps(data).encode('utf-8') if data else None
            req = urllib.request.Request(url, data=req_data, headers={
                "apikey": config.SUPABASE_KEY, "Content-Type": "application/json"
            }, method=method)
            with urllib.request.urlopen(req) as res: return res.read().decode('utf-8')
        except: return None
# ----------------------------------------------------
# 3. 랭킹 로직 (변화 없음)
# ----------------------------------------------------
async def load_rankings_online():
    browser_debug("📊 랭킹 보드 확인 중...")
    data_str = await _fetch_supabase("rankings?select=*", 'GET')
    
    formatted_list = []
    if data_str:
        try:
            raw_list = json.loads(data_str)
            for row in raw_list:
                for cat in RANK_CATEGORIES:
                    db_col = cat.lower().replace("score", "_score").replace("time", "_time")
                    formatted_list.append({
                        "ID": row.get("name", "익명"),
                        "RankCategory": cat,
                        "RankValue": float(row.get(db_col, 0)),
                        "Levels": row.get("levels", 0),
                        "Kills": row.get("kills", 0)
                    })
            browser_debug(f"✅ 파싱 성공: {len(raw_list)}명")
        except: pass
    return formatted_list

async def save_new_ranking_online(name, score_data):
    browser_debug(f"💾 점수 적으러 가는 중: {name}")
    new_row = {
        "name": str(name),
        "levels": int(score_data.get('levels', 0)),
        "kills": int(score_data.get('kills', 0)),
        "bosses": int(score_data.get('bosses', 0)),
        "difficulty_score": float(score_data.get('difficulty_score', 0.0)),
        "survival_time": float(score_data.get('survival_time', 0.0))
    }
    res = await _fetch_supabase("rankings", 'POST', data=new_row)
    return True if res else False

# 거리 계산 함수들 (기존과 동일)
def get_wrapped_delta(val1, val2, map_dim):
    delta = val2 - val1
    if abs(delta) > map_dim / 2:
        if delta > 0: delta -= map_dim
        else: delta += map_dim
    return delta

def distance_sq_wrapped(x1, y1, x2, y2, map_w, map_h):
    dx = get_wrapped_delta(x1, x2, map_w)
    dy = get_wrapped_delta(y1, y2, map_h)
    return dx*dx + dy*dy
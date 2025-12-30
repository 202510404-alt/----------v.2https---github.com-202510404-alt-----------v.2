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
    except:
        pass

# 🚩 Pylance 에러 방지 및 카테고리 정의
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
# 2. Supabase 통신 함수 (네 아이디어: 파이썬-JS-DB 중간다리)
# ----------------------------------------------------
async def _fetch_supabase(endpoint, method, data=None):
    # 200 OK가 검증된 주소 방식 (apikey 주소창 삽입)
    sep = "&" if "?" in endpoint else "?"
    url = f"{config.SUPABASE_URL}/rest/v1/{endpoint}{sep}apikey={config.SUPABASE_KEY}"
    
    if IS_WEB and js:
        try:
            # 🚩 [15바이트 에러 해결] 데이터를 자바스크립트용 문자열로 미리 변환
            if data:
                # 파이썬 dict -> JSON 글자
                python_to_json = json.dumps(data)
                # 자바스크립트 엔진 안에서 다시 객체로 인식하게 만듦
                js_body_part = f"JSON.stringify({python_to_json})"
            else:
                js_body_part = "null"

            # 게시판 초기화
            js.window.js_to_py = "WAITING"
            
            # 자바스크립트 실행 코드 (다리 역할)
            js_worker = f"""
            (function() {{
                fetch('{url}', {{
                    method: '{method}',
                    headers: {{
                        'apikey': '{config.SUPABASE_KEY}',
                        'Authorization': 'Bearer {config.SUPABASE_KEY}',
                        'Content-Type': 'application/json',
                        'Prefer': 'return=representation'
                    }},
                    body: {js_body_part}
                }})
                .then(r => r.text())
                .then(txt => {{ window.js_to_py = txt; }})
                .catch(e => {{ window.js_to_py = "ERROR:" + e.message; }});
            }})();
            """
            js.window.eval(js_worker)
            
            # 🚩 [타이밍 동기화] 답장이 올 때까지 0.01초씩 쉬면서 감시
            wait_count = 0
            while str(js.window.js_to_py) == "WAITING":
                await asyncio.sleep(0.01) # 네가 말한 미세한 대기
                wait_count += 1
                if wait_count > 500: # 5초 타임아웃
                    return None
            
            res_text = str(js.window.js_to_py)
            
            if res_text.startswith("ERROR:"):
                browser_debug(f"❌ 전송 실패: {res_text}", True)
                return None
            
            return res_text

        except Exception as e:
            browser_debug(f"🔥 브릿지 치명적 오류: {str(e)}", True)
            return None
    else:
        # 로컬(VSC) 환경용 (urllib)
        import urllib.request
        try:
            req_data = json.dumps(data).encode('utf-8') if data else None
            headers = {
                "apikey": config.SUPABASE_KEY,
                "Authorization": f"Bearer {config.SUPABASE_KEY}",
                "Content-Type": "application/json"
            }
            req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
            with urllib.request.urlopen(req) as res:
                return res.read().decode('utf-8')
        except:
            return None

# ----------------------------------------------------
# 3. 데이터 로드/저장 로직 (이미 성공한 로직 유지)
# ----------------------------------------------------
async def load_rankings_online():
    browser_debug("📊 서버에서 랭킹 데이터를 불러오는 중...")
    data_str = await _fetch_supabase("rankings?select=*", 'GET')
    
    formatted_list = []
    if data_str:
        try:
            raw_list = json.loads(data_str)
            browser_debug(f"✅ 수신 성공: {len(raw_list)}명")
            for row in raw_list:
                for cat in RANK_CATEGORIES:
                    # DB 컬럼명 매핑 (모두 소문자인지 꼭 확인!)
                    db_col = cat.lower().replace("score", "_score").replace("time", "_time")
                    formatted_list.append({
                        "ID": row.get("name", "익명"),
                        "RankCategory": cat,
                        "RankValue": float(row.get(db_col, 0)),
                        "Levels": row.get("levels", 0),
                        "Kills": row.get("kills", 0)
                    })
        except Exception as e:
            browser_debug(f"파싱 실패: {e}", True)
    return formatted_list

async def save_new_ranking_online(name, score_data):
    browser_debug(f"💾 서버에 점수 기록 중: {name}")
    new_row = {
        "name": str(name),
        "levels": int(score_data.get('levels', 0)),
        "kills": int(score_data.get('kills', 0)),
        "bosses": int(score_data.get('bosses', 0)),
        "difficulty_score": float(score_data.get('difficulty_score', 0.0)),
        "survival_time": float(score_data.get('survival_time', 0.0))
    }
    # 🚩 POST 요청 후 결과 받기
    res = await _fetch_supabase("rankings", 'POST', data=new_row)
    if res:
        browser_debug("🎉 서버 저장 성공!")
        return True
    return False

# ----------------------------------------------------
# 4. 물리 계산 유틸리티 (수정 금지)
# ----------------------------------------------------
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
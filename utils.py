import math
import json
import asyncio
import config
import sys

# 1. 환경 감지 및 브라우저 전용 모듈 준비
IS_WEB = (sys.platform == "emscripten")
js = None

if IS_WEB:
    try:
        import js # type: ignore
        from pyodide.http import pyfetch # type: ignore
    except ImportError:
        pass

# 🚩 [디버깅] 브라우저 콘솔(F12)에 로그를 찍습니다.
def browser_log(msg, is_error=False):
    full_msg = f"🚀 [Vampire-Web] {msg}"
    if IS_WEB and js:
        if is_error:
            js.window.console.error(full_msg)
        else:
            js.window.console.log(full_msg)
    else:
        print(full_msg)

# 랭킹 항목 정의
RANK_CATEGORIES = ["Levels", "Kills", "Bosses", "DifficultyScore", "SurvivalTime"]

# ----------------------------------------------------
# 2. Supabase 통합 통신 함수 (웹 환경 최적화)
# ----------------------------------------------------
async def _fetch_supabase(endpoint, method, data=None):
    url = f"{config.SUPABASE_URL}/rest/v1/{endpoint}"
    
    # 🚩 Supabase 전용 헤더
    headers = {
        "apikey": config.SUPABASE_KEY,
        "Authorization": f"Bearer {config.SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    if IS_WEB:
        # --- [웹 브라우저 환경] ---
        try:
            browser_log(f"통신 시작: {method} {url}")
            # 브라우저가 다른 일을 할 수 있게 아주 잠깐 멈춤 (멈춤 현상 방지 핵심)
            await asyncio.sleep(0.01)
            
            body_content = json.dumps(data) if data else None
            
            # 🚩 pyfetch를 사용하여 브라우저 네이티브 방식으로 요청
            response = await pyfetch(
                url=url,
                method=method,
                headers=headers,
                body=body_content
            )
            
            if response.status in [200, 201]:
                res_text = await response.string()
                browser_log("통신 성공!")
                return res_text
            else:
                browser_log(f"API 에러: {response.status}", is_error=True)
                return None
        except Exception as e:
            browser_log(f"치명적 오류: {str(e)}", is_error=True)
            return None
    else:
        # --- [로컬 윈도우 환경] ---
        import urllib.request
        try:
            req_data = json.dumps(data).encode('utf-8') if data else None
            req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
            with urllib.request.urlopen(req) as res:
                return res.read().decode('utf-8')
        except Exception as e:
            print(f"LOCAL ERROR: {e}")
            return None

# ----------------------------------------------------
# 3. 랭킹 로드 (Supabase -> UI 데이터 변환)
# ----------------------------------------------------
async def load_rankings_online():
    browser_log("랭킹 로드 시도...")
    # 정렬 없이 가져오기 (대소문자 문제 방지)
    data_str = await _fetch_supabase("rankings?select=*", 'GET')
    
    formatted_list = []
    if data_str:
        try:
            raw_list = json.loads(data_str)
            browser_log(f"데이터 {len(raw_list)}개 수신 완료")
            for row in raw_list:
                for cat in RANK_CATEGORIES:
                    # DB 컬럼(소문자) -> UI 데이터 변환
                    db_col = cat.lower().replace("score", "_score").replace("time", "_time")
                    formatted_list.append({
                        "ID": row.get("name", "익명"),
                        "RankCategory": cat,
                        "RankValue": float(row.get(db_col, 0)),
                        "Levels": row.get("levels", 0),
                        "Kills": row.get("kills", 0)
                    })
        except Exception as e:
            browser_log(f"파싱 실패: {str(e)}", is_error=True)
    return formatted_list

# ----------------------------------------------------
# 4. 랭킹 저장
# ----------------------------------------------------
async def save_new_ranking_online(name, score_data):
    browser_log(f"점수 저장 중: {name}")
    new_row = {
        "name": str(name),
        "levels": int(score_data.get('levels', 0)),
        "kills": int(score_data.get('kills', 0)),
        "bosses": int(score_data.get('bosses', 0)),
        "difficulty_score": float(score_data.get('difficulty_score', 0.0)),
        "survival_time": float(score_data.get('survival_time', 0.0))
    }
    res = await _fetch_supabase("rankings", 'POST', data=new_row)
    if res:
        browser_log("서버 저장 완료!")
        return True
    return False

# ----------------------------------------------------
# 5. 필수 수학 유틸리티 (절대 삭제 금지)
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
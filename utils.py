# utils.py
import math
import json
import config
# 🚩 온라인 통신을 위한 라이브러리 import (Pygbag 호환)
import urllib.request
import urllib.parse
import ssl
import pygame 


# 🚩🚩🚩 GAS Web App URL (선생님의 URL) 🚩🚩🚩
GAS_WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzWc-QJXmJOJm7IYJNVrzRP76jZPX9cTNGHkHI1HqPalLat5fxcC79JxMVahPm5J0MRaQ/exec"


# ----------------------------------------------------
# 랭킹 저장/로드 함수 (온라인 버전)
# ----------------------------------------------------

def save_new_ranking_online(name, score_data):
    """새로운 기록을 GAS Web App URL로 POST 요청을 통해 전송합니다."""
    
    # 1. 전송할 데이터 준비 (모든 숫자 데이터를 실수형으로 강제 변환)
    data = {
        "id": name,
        "level": str(float(score_data.get('level', 0.0))), # 🚩 문자열로 변환
        "kills": str(float(score_data.get('kills', 0.0))), # 🚩 문자열로 변환
        "bosses": str(float(score_data.get('bosses', 0.0))), # 🚩 문자열로 변환
        "difficulty_score": str(float(score_data.get('difficulty_score', 0.0))),
        "survival_time": str(float(score_data.get('survival_time', 0.0)))
    }
    
    # 2. POST 요청 준비
    data_json = json.dumps(data).encode('utf-8')
    headers = {'Content-Type': 'application/json'}
    
    req_url = GAS_WEB_APP_URL + '?access=public'
    
    req = urllib.request.Request(
        GAS_WEB_APP_URL, 
        data=data_json, 
        headers=headers, 
        method='POST'
    )
    
    try:
        # SSL 인증서 검증을 무시하고 요청을 보냅니다 
        context = ssl._create_unverified_context() 
        
        # 🚩🚩 디버깅 로그: 전송할 데이터 출력
        print(f"DEBUG: 전송 데이터 확인: {data}")

        with urllib.request.urlopen(req, context=context) as response:
            result = response.read().decode('utf-8')
            # 🚩🚩 디버깅 로그: 서버 응답 출력
            print(f"DEBUG: 서버 응답 수신: {result}") 
            return json.loads(result)
            
    except Exception as e:
        print(f"ERROR: 랭킹 전송 실패: {e}")
        return {"success": False, "message": f"전송 오류: {e}"}

# ----------------------------------------------------

def load_rankings_online():
    """GAS Web App URL로 GET 요청을 통해 랭킹 데이터를 수신합니다."""
    try:
        # SSL 인증서 검증을 무시하고 요청을 보냅니다
        context = ssl._create_unverified_context() 
        with urllib.request.urlopen(GAS_WEB_APP_URL, context=context) as response:
            data = response.read().decode('utf-8')
            # GAS Web App은 JSON 리스트 형태로 데이터를 반환합니다.
            return json.loads(data)
            
    except Exception as e:
        print(f"ERROR: 랭킹 로드 실패: {e}")
        return []

# ----------------------------------------------------
# 기존 utils 함수 (유지)
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
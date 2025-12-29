@echo off
echo [1/3] 게임 빌드 시작 (pygbag)...
py -m pygbag --build --title vampire_v4 .

echo [2/3] vampire-web 리포지토리로 파일 배달 중...
xcopy /s /e /y build\web\* ..\vampire-web\

echo [3/3] 깃허브로 전송 중...
cd ..\vampire-web
git add .
git commit -m "Auto Build: Supabase Ranking Version"
git push origin main

cd ..\vampire_survivor_v3
echo ==========================================
echo 드디어 끝났다! 링크 확인해봐: 
echo https://202510404-alt.github.io/vampire-web/
echo ==========================================
pause
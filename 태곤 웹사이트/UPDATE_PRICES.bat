@echo off
chcp 65001 >nul
echo.
echo [싱싱농산물] 공급표 엑셀 -> 사이트 단가 자동 반영
echo ----------------------------------------------
echo 1) SINGSING_SUPPLY_PRICE_LIST.xlsx 를 수정/저장했는지 확인하세요.
echo 2) 아래 작업이 끝나면 웹페이지를 새로고침(F5) 하세요.
echo.
python tools\update_prices_from_excel.py
echo.
echo [완료] 아무 키나 누르면 종료됩니다.
pause >nul

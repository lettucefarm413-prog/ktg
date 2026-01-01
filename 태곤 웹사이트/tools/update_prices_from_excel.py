#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""싱싱농산물 B2B 가격표 자동 반영 스크립트

사용 방법(Windows):
1) SINGSING_SUPPLY_PRICE_LIST.xlsx 를 수정/저장
   - '공지사항' 시트 오른쪽의 [품목/포장단위/최종단가(원)] 표를 수정하세요.
2) UPDATE_PRICES.bat 더블클릭
3) 웹페이지 새로고침(F5)

이 스크립트는 엑셀의 공급표(표)를 읽어서 assets/prices.js 를 자동 생성합니다.
(사이트는 assets/prices.js 를 읽어 상품목록/장바구니/발주서 단가·합계를 계산합니다.)
"""

from __future__ import annotations

from pathlib import Path
import json
import re
from datetime import datetime

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXCEL = ROOT / "SINGSING_SUPPLY_PRICE_LIST.xlsx"
PRODUCTS_JSON = ROOT / "assets" / "products.json"
OUT_JS = ROOT / "assets" / "prices.js"

REQUIRED = ("품목", "포장단위", "최종단가(원)")

def _parse_pack(v: object) -> int | None:
    s = str(v).strip()
    m = re.search(r"(\d+)", s)
    return int(m.group(1)) if m else None

def _parse_price(v: object) -> int | None:
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    # 숫자/문자 혼합 처리 ("3,840" 등)
    s = str(v).strip()
    s = re.sub(r"[^0-9.]", "", s)
    if not s:
        return None
    try:
        return int(round(float(s)))
    except Exception:
        return None

def _find_table(df: pd.DataFrame) -> tuple[int, dict[str, int]] | None:
    """raw(header=None)로 읽은 df에서 REQUIRED 헤더 행/열 위치를 찾는다."""
    for r in range(min(200, len(df))):  # 상단 몇백줄만 스캔
        row = df.iloc[r].tolist()
        colmap: dict[str, int] = {}
        for label in REQUIRED:
            for c, v in enumerate(row):
                if str(v).strip() == label:
                    colmap[label] = c
                    break
        if all(k in colmap for k in REQUIRED):
            return r, colmap
    return None

def _read_supply_table() -> pd.DataFrame:
    # 1) "공급표" 시트가 있으면 우선 시도
    try:
        xls = pd.ExcelFile(EXCEL)
        sheets = xls.sheet_names
    except Exception as e:
        raise SystemExit(f"[오류] 엑셀을 읽을 수 없습니다: {e}")

    candidate_sheets = []
    if "공급표" in sheets:
        candidate_sheets.append("공급표")
    if "공지사항" in sheets:
        candidate_sheets.append("공지사항")
    # 나머지 시트도 후보로
    candidate_sheets += [s for s in sheets if s not in candidate_sheets]

    for sheet in candidate_sheets:
        try:
            raw = pd.read_excel(EXCEL, sheet_name=sheet, header=None)
        except Exception:
            continue
        found = _find_table(raw)
        if not found:
            continue
        header_row, colmap = found

        # 표 하단까지 슬라이스
        rows = []
        for i in range(header_row + 1, len(raw)):
            item = raw.iat[i, colmap["품목"]]
            pack = raw.iat[i, colmap["포장단위"]]
            price = raw.iat[i, colmap["최종단가(원)"]]
            # 종료 조건: 품목/단위/가격 모두 비어있으면 표 끝
            if (pd.isna(item) or str(item).strip() == "") and (pd.isna(pack) or str(pack).strip() == "") and (pd.isna(price) or str(price).strip() == ""):
                # 연속 공백이 나오면 종료
                # (공지사항 시트는 표 뒤로 공백행이 이어짐)
                break
            rows.append((item, pack, price))

        df = pd.DataFrame(rows, columns=list(REQUIRED))
        # 빈 품목 제거
        df["품목"] = df["품목"].astype(str).str.strip()
        df = df[df["품목"].ne("")].copy()
        return df

    raise SystemExit(f"[오류] 엑셀에서 공급표(품목/포장단위/최종단가) 표를 찾지 못했습니다. 시트: {', '.join(sheets)}")

def main() -> None:
    if not EXCEL.exists():
        raise SystemExit(f"[오류] 엑셀 파일이 없습니다: {EXCEL}")

    products = json.loads(PRODUCTS_JSON.read_text(encoding="utf-8"))
    name_to_id = {p["name"]: p["id"] for p in products if "name" in p and "id" in p}

    df = _read_supply_table()

    table: dict[str, dict[int, int]] = {}
    skipped: list[str] = []

    for _, row in df.iterrows():
        name = str(row["품목"]).strip()
        pid = name_to_id.get(name)
        if not pid:
            skipped.append(name)
            continue

        pack = _parse_pack(row["포장단위"])
        price = _parse_price(row["최종단가(원)"])
        if pack is None or price is None:
            continue

        table.setdefault(pid, {})[pack] = price

    payload = {"updatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "items": table}
    OUT_JS.write_text(
        "// Auto-generated from SINGSING_SUPPLY_PRICE_LIST.xlsx\n"
        f"window.SINGSING_PRICE_TABLE = {json.dumps(payload, ensure_ascii=False, indent=2)};\n",
        encoding="utf-8",
    )

    print("[완료] prices.js 생성됨:", OUT_JS)
    if skipped:
        print("[주의] products.json 에 없는 품목이라 건너뜀:", ", ".join(sorted(set(skipped))))

if __name__ == "__main__":
    main()

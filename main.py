"""
영수증 증빙 점검 프로그램 (과제용)

입력 : 영수증 이미지 + 카드 승인금액
처리 : ① PaddleOCR(AI 모델)로 이미지 속 글자·신뢰도·위치 판독 (추론)
       ② 판독 결과에서 금액 항목 추출 → 검산 → 승인금액과 비교 (규칙 엔진)
출력 : 정상 / 추가 증빙 필요(차액·승인번호 없음) / 담당자 확인 + 근거, 글자 박스 이미지

사용법
  한 장   : python main.py data/S01_app_receipt.png 35500
  전체    : python main.py --csv samples.csv
  대체엔진: python main.py --csv samples.csv --engine easyocr
"""
import argparse
import csv
import json
import os
import re
import sys
import time

from PIL import Image, ImageDraw

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CONF_THRESHOLD = 0.85  # 금액 글자의 신뢰도가 이보다 낮으면 담당자 확인
OUT_DIR = "output"

# 금액 항목 키워드 (띄어쓰기를 없앤 뒤 비교)
TOTAL_KEYS = ["총결제금액", "총금액", "합계금액", "결제금액", "합계"]
SUPPLY_KEYS = ["공급가액", "과세금액", "과세물품가액", "물품가액"]
VAT_KEYS = ["부가세"]
BASE_KEYS = ["주문금액", "음식값"]
DELIVERY_KEYS = ["배달팁", "배달비"]
DISCOUNT_KEYS = ["할인"]
APPROVAL_KEY = "승인번호"
APPROVAL_VALUE = re.compile(r"[:：]?([A-Za-z0-9][A-Za-z0-9\-]{3,})")


# ------------------------------------------------------------------ 1. AI 모델 (OCR)
def load_engine(name):
    """OCR 모델을 불러와서 '이미지 경로 → [(글자, 신뢰도, [x1,y1,x2,y2]), ...]' 함수를 돌려준다."""
    if name == "paddle":
        from paddleocr import PaddleOCR

        ocr = PaddleOCR(
            lang="korean",                       # 한국어 인식 모델
            use_doc_orientation_classify=False,  # 문서 방향 분류 끔 (속도)
            use_doc_unwarping=False,             # 문서 펴기 끔 (속도)
            use_textline_orientation=False,      # 글줄 방향 분류 끔 (속도)
        )

        def run(path):
            items = []
            for res in ocr.predict(path):
                data = res.json
                data = data.get("res", data)
                boxes = data.get("rec_boxes")
                if boxes is None or len(boxes) == 0:
                    boxes = [[min(p[0] for p in poly), min(p[1] for p in poly),
                              max(p[0] for p in poly), max(p[1] for p in poly)]
                             for poly in data.get("rec_polys", [])]
                for t, s, b in zip(data["rec_texts"], data["rec_scores"], boxes):
                    items.append((t, float(s), [int(v) for v in b]))
            return items
        return run

    if name == "easyocr":
        import easyocr

        reader = easyocr.Reader(["ko", "en"], gpu=False)

        def run(path):
            items = []
            for pts, t, s in reader.readtext(path):
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                items.append((t, float(s), [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]))
            return items
        return run

    raise ValueError(f"알 수 없는 엔진: {name}")


# ------------------------------------------------------------------ 2. 전처리: 글자 조각 → 줄
def group_lines(items):
    """같은 높이에 있는 글자 조각을 한 줄로 묶는다. (예: '총 결제금액' + '35,500원')"""
    if not items:
        return []
    heights = sorted(b[3] - b[1] for _, _, b in items)
    tol = max(8, heights[len(heights) // 2] * 0.6)
    items = sorted(items, key=lambda it: (it[2][1] + it[2][3]) / 2)
    lines, cur, cur_y = [], [], None
    for it in items:
        cy = (it[2][1] + it[2][3]) / 2
        if cur and abs(cy - cur_y) > tol:
            lines.append(sorted(cur, key=lambda x: x[2][0]))
            cur = []
        cur.append(it)
        cur_y = cy if len(cur) == 1 else (cur_y * (len(cur) - 1) + cy) / len(cur)
    if cur:
        lines.append(sorted(cur, key=lambda x: x[2][0]))
    return lines


# ------------------------------------------------------------------ 3. 규칙 엔진
NUM_BLOB = re.compile(r"[+\-]?\d[\d,.]*")
VALID_NUM = re.compile(r"[+\-]?(\d{1,3}(,\d{3})+|\d+)")


def find_amount(line, keys):
    """줄에서 키워드 바로 뒤에 나오는 금액을 찾는다. 반환: (값, 신뢰도, 원문, 형식정상여부)"""
    pieces = []  # (띄어쓰기 없는 글자, 신뢰도)
    for t, s, _ in line:
        pieces.append((t.replace(" ", ""), s))
    text = "".join(p for p, _ in pieces)
    for key in keys:
        k = text.find(key)
        if k < 0:
            continue
        m = NUM_BLOB.search(text, k + len(key))
        if not m:
            return None
        raw = m.group().rstrip(".")
        raw = raw.replace(".", ",")  # 원화에는 소수점이 없으므로 25.800 → 25,800
        # 금액이 들어 있는 조각들의 신뢰도 중 가장 낮은 값
        pos, confs = 0, []
        for p, s in pieces:
            if pos < m.end() and pos + len(p) > m.start():
                confs.append(s)
            pos += len(p)
        ok = VALID_NUM.fullmatch(raw) is not None
        value = int(raw.replace(",", "").replace("+", "").replace("-", "")) if ok else None
        return value, min(confs) if confs else 0.0, raw, ok
    return None


def find_approval(lines):
    """'승인번호' 뒤(같은 줄, 없으면 다음 줄 첫 글자)에서 번호를 찾는다. 없으면 None."""
    for i, line in enumerate(lines):
        joined = "".join(t.replace(" ", "") for t, _, _ in line)
        k = joined.find(APPROVAL_KEY)
        if k < 0:
            continue
        m = APPROVAL_VALUE.match(joined, k + len(APPROVAL_KEY))
        if m:
            return m.group(1)
        if i + 1 < len(lines):  # 라벨 아래 줄에 값이 있는 양식 (메일형 매출전표)
            m = APPROVAL_VALUE.match(lines[i + 1][0][0].replace(" ", ""))
            if m:
                return m.group(1)
    return None


def judge(lines, approved, threshold=CONF_THRESHOLD):
    """판독된 줄에서 금액을 뽑고 검산한 뒤 판정한다."""
    f = {"총액": None, "공급가액": None, "부가세": None, "기본금액": None, "배달비": None, "할인": []}
    for line in lines:
        joined = "".join(t.replace(" ", "") for t, _, _ in line)
        for name, keys in [("총액", TOTAL_KEYS), ("공급가액", SUPPLY_KEYS), ("부가세", VAT_KEYS),
                           ("기본금액", BASE_KEYS), ("배달비", DELIVERY_KEYS)]:
            if f[name] is None and any(k in joined for k in keys):
                f[name] = find_amount(line, keys)
        if any(k in joined for k in DISCOUNT_KEYS) and not any(k in joined for k in TOTAL_KEYS):
            a = find_amount(line, DISCOUNT_KEYS)
            if a:
                f["할인"].append(a)

    reasons = []
    tot = f["총액"]
    approval = find_approval(lines)
    f["승인번호"] = approval
    if approval is None:
        msg = ["승인번호가 없음 → 증빙으로 인정 불가, 승인번호가 있는 카드 매출전표 추가 제출 필요"]
        if tot and tot[3]:
            msg.append(f"참고: 판독한 총액 {tot[0]:,}원")
        return "추가 증빙 필요", msg, f, None
    if tot is None:
        return "담당자 확인", ["총액 항목을 찾지 못함"], f, None
    value, conf, raw, ok = tot
    if not ok:
        return "담당자 확인", [f"총액 '{raw}'이(가) 금액 형식이 아님 (오독 의심)"], f, None
    if conf < threshold:
        return "담당자 확인", [f"총액 '{raw}' 신뢰도 {conf:.6f} < 기준 {threshold}"], f, None

    # 검산: 공급가액+부가세 또는 주문금액+배달비-할인
    check = None
    parts = [p for p in [f["공급가액"], f["부가세"]] if p]
    if len(parts) == 2:
        if all(p[3] for p in parts):
            calc = parts[0][0] + parts[1][0]
            check = (f"{parts[0][0]:,} + {parts[1][0]:,} = {calc:,}", calc == value)
        else:
            check = ("공급가액/부가세 형식 오류", False)
    elif f["기본금액"]:
        items = [f["기본금액"]] + ([f["배달비"]] if f["배달비"] else [])
        if all(p[3] for p in items + f["할인"]):
            calc = sum(p[0] for p in items) - sum(p[0] for p in f["할인"])
            expr = " + ".join(f"{p[0]:,}" for p in items)
            expr += "".join(f" - {p[0]:,}" for p in f["할인"])
            check = (f"{expr} = {calc:,}", calc == value)
        else:
            check = ("항목 금액 형식 오류", False)

    if check and not check[1]:
        return "담당자 확인", [f"검산 불일치: {check[0]} ≠ 총액 {value:,} (오독 의심)"], f, check
    reasons.append(f"승인번호 확인: {approval}")
    if check:
        reasons.append(f"검산 통과: {check[0]}")
    else:
        reasons.append("검산할 항목 없음 (총액만 사용)")

    diff = approved - value
    if diff == 0:
        reasons.append(f"승인금액 {approved:,} = 증빙금액 {value:,}")
        return "정상", reasons, f, check
    reasons.append(f"승인금액 {approved:,} / 증빙금액 {value:,} / 차액 {diff:,}")
    return "추가 증빙 필요", reasons, f, check


# ------------------------------------------------------------------ 4. 결과 출력
def draw_boxes(path, items, out_path, threshold=CONF_THRESHOLD):
    im = Image.open(path).convert("RGB")
    d = ImageDraw.Draw(im)
    for i, (t, s, b) in enumerate(items):
        color = (0, 170, 0) if s >= threshold else (230, 0, 0)
        d.rectangle(b, outline=color, width=3)
        d.text((b[0], max(0, b[1] - 12)), f"{i}:{s:.2f}", fill=color)
    im.save(out_path)


def process(run, path, approved, sample_id=None, threshold=CONF_THRESHOLD):
    sid = sample_id or os.path.splitext(os.path.basename(path))[0]
    t0 = time.time()
    items = run(path)                 # ← AI 모델 추론
    sec = time.time() - t0
    lines = group_lines(items)
    verdict, reasons, fields, check = judge(lines, approved, threshold)

    print("=" * 64)
    print(f"[{sid}] {path}  (승인금액 {approved:,}원)")
    print(f"- OCR 추론 시간: {sec:.2f}초, 인식한 글자 조각: {len(items)}개")
    print("- OCR 판독 결과 (신뢰도 | 글자)")
    for line in lines:
        print("   " + "   ".join(f"{s:.2f}|{t}" for t, s, _ in line))
    print(f"▶ 판정: {verdict}")
    for r in reasons:
        print(f"   · {r}")

    os.makedirs(OUT_DIR, exist_ok=True)
    draw_boxes(path, items, os.path.join(OUT_DIR, f"{sid}_boxes.png"), threshold)
    with open(os.path.join(OUT_DIR, f"{sid}_ocr.json"), "w", encoding="utf-8") as fp:
        json.dump([{"text": t, "score": s, "box": b} for t, s, b in items], fp, ensure_ascii=False, indent=1)
    tot = fields["총액"]
    return {"verdict": verdict, "reason": " / ".join(reasons), "sec": round(sec, 2),
            "total_read": tot[2] if tot else "", "total_conf": round(tot[1], 3) if tot else ""}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image", nargs="?")
    ap.add_argument("approved", nargs="?", type=int)
    ap.add_argument("--csv")
    ap.add_argument("--engine", default="paddle", choices=["paddle", "easyocr"])
    ap.add_argument("--threshold", type=float, default=CONF_THRESHOLD,
                    help="총액 신뢰도 및 박스 색상 기준 (0~1, 기본값: 0.85)")
    a = ap.parse_args()
    if not 0.0 <= a.threshold <= 1.0:
        ap.error("--threshold는 0 이상 1 이하의 숫자여야 합니다")
    print(f"신뢰도 기준: {a.threshold}")

    t0 = time.time()
    run = load_engine(a.engine)
    print(f"모델 로딩: {a.engine} ({time.time() - t0:.1f}초)")

    if not a.csv:
        if not a.image or a.approved is None:
            ap.error("이미지 경로와 승인금액을 넣거나 --csv samples.csv 를 사용하세요")
        process(run, a.image, a.approved, threshold=a.threshold)
        return

    with open(a.csv, encoding="utf-8-sig") as fp:
        samples = list(csv.DictReader(fp))
    rows = []
    for s in samples:
        r = process(run, s["image_file"], int(s["approved_amount"]), s["sample_id"], threshold=a.threshold)
        r.update(sample_id=s["sample_id"], expected=s["expected_result"],
                 match="O" if r["verdict"] == s["expected_result"] else "X")
        rows.append(r)

    # 요약
    n = len(rows)
    hit = sum(r["match"] == "O" for r in rows)
    false_ok = [r["sample_id"] for r in rows if r["verdict"] == "정상" and r["expected"] != "정상"]
    review = sum(r["verdict"] == "담당자 확인" for r in rows)
    print("=" * 64)
    print(f"{'ID':<5}{'정답':<12}{'프로그램':<12}{'일치':<4}{'총액 판독':<12}{'신뢰도':<7}{'시간(초)'}")
    for r in rows:
        print(f"{r['sample_id']:<5}{r['expected']:<12}{r['verdict']:<12}{r['match']:<4}"
              f"{r['total_read']:<12}{str(r['total_conf']):<7}{r['sec']}")
    print("-" * 64)
    print(f"정답 일치: {hit}/{n}   잘못된 정상: {len(false_ok)}건 {false_ok}   "
          f"담당자 확인 비율: {review}/{n}   평균 추론 시간: {sum(r['sec'] for r in rows) / n:.2f}초")

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "results.csv"), "w", newline="", encoding="utf-8-sig") as fp:
        w = csv.DictWriter(fp, fieldnames=["sample_id", "expected", "verdict", "match",
                                           "total_read", "total_conf", "sec", "reason"])
        w.writeheader()
        w.writerows(rows)
    print(f"결과 저장: {OUT_DIR}/results.csv, {OUT_DIR}/*_boxes.png")


if __name__ == "__main__":
    main()

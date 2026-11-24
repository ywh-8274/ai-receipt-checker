# 과제용 가상 영수증 테스트 세트 생성기
# 실제 영수증 4종의 "양식"만 참고했고, 상호·이름·카드번호·주소 등은 모두 가상 값이다.
import csv, os, shutil
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

OUT = "/home/claude/receipt_samples/data"
os.makedirs(OUT, exist_ok=True)

REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
def F(size, bold=False):
    return ImageFont.truetype(BOLD if bold else REG, size, index=1)

WM = "※ 실제 영수증이 아닌 과제 시연용 가상 문서입니다."
RED = (205, 40, 40)

def tw(d, s, f):
    b = d.textbbox((0, 0), s, font=f)
    return b[2] - b[0]

def right(d, xr, y, s, f, fill=(30, 30, 30)):
    d.text((xr - tw(d, s, f), y), s, font=f, fill=fill)

def center(d, xc, y, s, f, fill=(30, 30, 30)):
    d.text((xc - tw(d, s, f) / 2, y), s, font=f, fill=fill)

# ---------------------------------------------------------------- S01 배달앱 영수증 캡처
def app_receipt(blur_last_digit=False, approval=True):
    W, H = 1080, 2316
    im = Image.new("RGB", (W, H), (110, 110, 110))
    d = ImageDraw.Draw(im)
    # 상태표시줄 + 앱 헤더
    d.rectangle([0, 0, W, 218], fill="white")
    d.text((45, 18), "1:19", font=F(42), fill=(80, 80, 80))
    right(d, 1035, 18, "100%", F(40), (80, 80, 80))
    center(d, W / 2, 105, "냠냠이츠", F(64, True), (232, 120, 30))
    d.text((70, 100), "<", font=F(64), fill=(40, 40, 40))
    right(d, 1010, 100, "X", F(56), (40, 40, 40))
    # 영수증 카드
    L, R = 72, 1008
    d.rounded_rectangle([L, 285, R, 2110], 28, fill="white")
    center(d, W / 2, 315, "영수증", F(56, True))
    d.line([L, 415, R, 415], fill=(225, 225, 225), width=3)
    center(d, W / 2, 500, "떡볶이연구소", F(66, True))
    center(d, W / 2, 590, "시연점", F(66, True))
    center(d, W / 2, 700, "주문번호: SIM0A21", F(46, True))
    center(d, W / 2, 770, "2026-11-03 12:10", F(40))
    xl, xr = 145, 935
    f = F(44)
    rows = [("로제 떡볶이 세트", "14,500원"), ("야채 쫄면", "9,500원"),
            ("김말이 튀김 (5개)", "12,000원")]
    y = 880
    for n, p in rows:
        d.text((xl, y), n, font=f, fill=(40, 40, 40)); right(d, xr, y, p, f, (40, 40, 40)); y += 115
    y += 10
    d.line([xl, y, xr, y], fill=(220, 220, 220), width=3); y += 45
    summ = [("주문금액", "36,000원"), ("배달비", "+2,500원"), ("즉시할인", "-1,000원"),
            ("쿠폰할인", "-2,000원")]
    for n, p in summ:
        d.text((xl, y), n, font=f, fill=(40, 40, 40)); right(d, xr, y, p, f, (40, 40, 40)); y += 85
    y += 20
    d.line([xl, y, xr, y], fill=(220, 220, 220), width=3); y += 50
    d.text((xl, y), "시연카드 결제", font=f, fill=(40, 40, 40))
    pay_y = y
    right(d, xr, y, "35,500원", f, (40, 40, 40)); y += 75
    if approval:
        d.text((xl, y), "승인번호 SIM-0121 · 일시불", font=F(36), fill=(120, 120, 120))
    y += 70
    d.line([xl, y, xr, y], fill=(220, 220, 220), width=3); y += 60
    ft = F(50, True)
    d.text((xl, y), "총 결제금액", font=ft, fill=(20, 20, 20))
    tot_y = y
    right(d, xr, y, "35,500원", ft, (20, 20, 20)); y += 120
    center(d, W / 2, y, WM, F(30), RED)
    # 하단 네비게이션
    d.rectangle([0, 2170, W, H], fill=(245, 245, 245))
    center(d, W / 2, 2210, "▢", F(60), (120, 120, 120))
    if blur_last_digit:
        # T11처럼 금액 마지막 자리만 뭉개기 ("35,50?원")
        for yy, font in [(pay_y, f), (tot_y, ft)]:
            x1 = xr - tw(d, "0원", font) - 4
            x2 = xr - tw(d, "원", font) + 2
            box = (int(x1), int(yy), int(x2), int(yy + font.size * 1.45))
            region = im.crop(box).filter(ImageFilter.GaussianBlur(9))
            im.paste(region, box)
    return im

# ---------------------------------------------------------------- T04 전/후 (지난 과제 양식)
def t04_before():
    W = H = 840  # 원본 T04(420px)의 2배 해상도
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    center(d, W / 2, 40, "가온식당", F(56, True), (20, 20, 20))
    center(d, W / 2, 130, "배달 주문 영수증(음식값) · 시연용 가상 문서", F(26), (110, 110, 110))
    center(d, W / 2, 172, "2026-10-23 12:20 · 승인번호 SIM-0004", F(26), (110, 110, 110))
    d.line([50, 225, 790, 225], fill=(200, 200, 200), width=2)
    d.text((50, 250), "음식값", font=F(32), fill=(30, 30, 30)); right(d, 790, 250, "25,800원", F(32))
    d.line([50, 330, 790, 330], fill=(30, 30, 30), width=4)
    d.text((50, 360), "총 결제금액", font=F(42, True), fill=(20, 20, 20))
    right(d, 790, 360, "25,800원", F(42, True), (20, 20, 20))
    center(d, W / 2, 460, WM, F(24), RED)
    return im

# ---------------------------------------------------------------- S04 카드매출전표 긴 캡처
def long_slip(total_rows=(("공급가액", "30,000원"), ("부가세액", "3,000원"), ("총 금액", "33,000원"))):
    W, H = 1050, 2576
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    L, R = 42, 1008
    fl, fh = F(34), F(36, True)
    y = 60
    def section(title, rows, y, bold_last=False):
        d.text((L, y), title, font=fh, fill=(25, 25, 25)); y += 80
        d.line([L, y, R, y], fill=(25, 25, 25), width=3); y += 45
        for i, (k, v) in enumerate(rows):
            b = bold_last and i == len(rows) - 1
            d.text((L, y), k, font=F(36, True) if b else fl, fill=(40, 40, 40))
            right(d, R, y, v, F(36, True) if b else fl, (40, 40, 40)); y += 87
        y += 15
        d.line([L, y, R, y], fill=(238, 238, 238), width=3)
        return y + 45
    y = section("거래정보", [("카드 승인번호", "SIM-2201"), ("카드종류", "시연카드"),
                         ("카드번호", "1234-56**-****-7890"), ("결제일시", "2026-11-06 11:01:21"),
                         ("주문메뉴", "김치볶음밥 외 2개"), ("주문번호", "SIMORDER0007")], y)
    y = section("카드영수증 발행금액", list(total_rows), y, bold_last=True)
    y = section("가맹점 정보", [("상호", "(주)한끼컴퍼니"), ("대표자명", "홍*동"),
                            ("사업자등록번호", "000-00-00001"), ("전화번호", "0000-0000"),
                            ("주소", "서울 가상구 시연로 12 시연빌딩 2층")], y)
    y = section("판매자 정보", [("상호", "밥집시연점"), ("대표자명", "김*수"),
                            ("사업자등록번호", "000-00-00002"), ("주소", "서울 가상구 예시동 34-56")], y)
    d.rectangle([0, y, W, H], fill=(244, 245, 247))
    center(d, W / 2, y + 60, WM, F(28), RED)
    return im

# ---------------------------------------------------------------- S05 A4 메일형 매출전표
def a4_mail():
    W, H = 1240, 1754
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    d.text((30, 18), "26. 11. 22. 오후 4:09", font=F(20), fill=(60, 60, 60))
    center(d, W / 2, 18, "[한끼배달] 영수증 발급 메일입니다.", F(20), (60, 60, 60))
    d.text((70, 90), "[한끼배달] 영수증 발급 메일입니다.", font=F(30, True), fill=(20, 20, 20))
    d.text((70, 140), "보낸사람: 한끼배달 <noreply@example.com>", font=F(22), fill=(60, 60, 60))
    right(d, 1170, 140, "2026년 11월 12일 오후 4:08", F(22), (60, 60, 60))
    d.text((120, 200), "한끼배달", font=F(34, True), fill=(30, 30, 30))
    d.text((120, 260), "한끼배달", font=F(54, True), fill=(20, 20, 20))
    d.text((120, 330), "신용카드 매출전표", font=F(54, True), fill=(20, 20, 20))
    d.text((120, 410), "한끼배달을 이용해 주셔서 감사합니다.", font=F(28), fill=(90, 90, 90))
    L, R, mid = 120, 1120, 620
    def grid(title, items, y):
        d.text((L, y), title, font=F(26, True), fill=(20, 20, 20)); y += 50
        d.line([L, y, R, y], fill=(30, 30, 30), width=2); y += 15
        for i in range(0, len(items), 2):
            for j, (k, v) in enumerate(items[i:i + 2]):
                x = L + 10 if j == 0 else mid
                d.text((x, y), k, font=F(20), fill=(110, 110, 110))
                d.text((x, y + 30), v, font=F(26), fill=(30, 30, 30))
            y += 80
            d.line([L, y - 8, R, y - 12], fill=(225, 225, 225), width=1)
        return y + 30
    y = grid("거래정보", [("카드 승인번호", "SIM-5170"), ("카드 종류", "시연카드"),
                       ("카드번호", "1234-56**********"), ("할부", ""),
                       ("결제일시", "2026-11-12 11:00:44"), ("주문번호", "SIMORDER0051"),
                       ("주문메뉴", "모둠 볶음 세트 외 6개")], 480)
    y = grid("가맹점 정보", [("상호", "(주)한끼컴퍼니"), ("대표자명", "홍*동"),
                          ("사업자등록번호", "000-00-00001"), ("전화번호", "0000-0000")], y)
    y = grid("판매자 정보", [("상호", "시연볶음 가상점"), ("대표자명", "이*희"),
                          ("사업자등록번호", "000-00-00003"), ("주소", "서울 가상구 예시동 7-8")], y)
    d.text((L, y), "카드영수증 발행금액", font=F(26, True), fill=(20, 20, 20)); y += 50
    d.line([L, y, R, y], fill=(30, 30, 30), width=2); y += 25
    for k, v, b in [("공급가액", "47,000원", False), ("부가세액", "4,700원", False), ("총 금액", "51,700원", True)]:
        d.text((L + 10, y), k, font=F(26, b), fill=(30, 30, 30)); right(d, R - 10, y, v, F(26, b), (30, 30, 30))
        y += 62
        d.line([L, y - 14, R, y - 18], fill=(225, 225, 225), width=1)
    center(d, W / 2, y + 40, WM, F(24), RED)
    return im

# ---------------------------------------------------------------- S06 PG사 표 형식 매출전표
def pg_table():
    W, H = 1240, 1754
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    BL, LB = (40, 70, 140), (238, 242, 250)
    d.text((300, 160), "SamplePay", font=F(40, True), fill=(60, 140, 60))
    d.text((300, 230), "신용카드 매출전표", font=F(46, True), fill=BL)
    L, R = 300, 940
    f, fb = F(21), F(21, True)
    def table(title, rows, y, colw):
        d.text((L, y), title, font=F(22), fill=(110, 110, 110)); y += 45
        for r in rows:
            h = 74
            x = L
            for c, (txt, w) in enumerate(zip(r, colw)):
                is_label = c % 2 == 0
                d.rectangle([x, y, x + w, y + h], fill=LB if is_label else "white", outline=BL, width=2)
                bold = txt in ("1,000",) or txt.endswith("3,500")
                if is_label:
                    center(d, x + w / 2, y + 22, txt, fb)
                else:
                    d.text((x + 12, y + 22), txt, font=fb if bold else f, fill=BL if bold else (30, 30, 30))
                x += w
            y += h
        return y + 45
    y = table("결제정보", [("카드번호", "1234-56**-****-7890", "카드종류", "시연카드"),
                        ("승인번호", "SIM-3501", "할부개월수", "일시불"),
                        ("거래일시", "2026-11-20 12:03:17", "취소일시", "")], 340, [130, 230, 130, 150])
    y = table("구매정보", [("주문자명", "홍*동", "과세금액", "3,182"),
                        ("주문번호", "SIMPG0000A1", "부가세", "318"),
                        ("구매상품", "학생식당 중식", "합계금액", "3,500")], y, [130, 230, 130, 150])
    y = table("이용상점정보", [("상점명", "시연대학교 식당", "대표자명", "김*수"),
                          ("홈페이지", "www.example.ac.kr", "사업자번호", "000-00-00006"),
                          ("주소", "서울 가상구 대학로 1", "", "")], y, [130, 230, 130, 150])
    y = table("결제서비스업체정보", [("업체명", "(주)가상페이", "대표자명", "박*진"),
                              ("사업자번호", "000-00-00009", "결제문의", "0000-0000")], y, [130, 230, 130, 150])
    d.text((L, y), "• 부가가치세법에 따라 매입세금계산서로 사용할 수 있습니다.", font=F(18), fill=(60, 60, 60))
    center(d, W / 2, y + 60, WM, F(22), RED)
    return im

# ---------------------------------------------------------------- 배달비 영수증 (배달비만 따로 결제)
def delivery_fee_receipt():
    W, H = 1080, 1620
    im = Image.new("RGB", (W, H), (244, 245, 247))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 200], fill="white")
    center(d, W / 2, 70, "빠른배달대행", F(56, True), (40, 110, 200))
    L, R = 72, 1008
    d.rounded_rectangle([L, 260, R, 1480], 28, fill="white")
    center(d, W / 2, 300, "배달비 영수증", F(56, True))
    d.line([L, 400, R, 400], fill=(225, 225, 225), width=3)
    xl, xr, f = 145, 935, F(44)
    y = 450
    for k, v in [("가맹점", "가온식당"), ("주문번호", "SIMDLV0042"), ("결제일시", "2026-11-10 18:42"), ("승인번호", "SIM-0342")]:
        d.text((xl, y), k, font=f, fill=(110, 110, 110)); right(d, xr, y, v, f, (40, 40, 40)); y += 90
    y += 20
    d.line([xl, y, xr, y], fill=(220, 220, 220), width=3); y += 50
    for k, v in [("기본 배달비", "3,000원"), ("거리 할증", "+500원")]:
        d.text((xl, y), k, font=f, fill=(40, 40, 40)); right(d, xr, y, v, f, (40, 40, 40)); y += 90
    y += 20
    d.line([xl, y, xr, y], fill=(220, 220, 220), width=3); y += 60
    d.text((xl, y), "총 결제금액", font=F(50, True), fill=(20, 20, 20))
    right(d, xr, y, "3,500원", F(50, True), (20, 20, 20)); y += 110
    d.text((xl, y), "시연카드 결제 (일시불)", font=F(36), fill=(110, 110, 110)); y += 120
    center(d, W / 2, y, WM, F(30), RED)
    return im

# ---------------------------------------------------------------- 종이 영수증 (감열지) + 사진처럼 만들기
def M(size, bold=False):
    return ImageFont.truetype(BOLD if bold else REG, size, index=6)  # Noto Sans Mono CJK KR

def paper_receipt(lines, width=620):
    """lines: (종류, 값...) 목록. 감열지 영수증 한 장을 그린다."""
    f, fb = M(26), M(30, True)
    H = 60 + sum(52 if t != "sep" else 30 for t, *_ in lines) + 60
    im = Image.new("RGB", (width, H), (250, 249, 244))
    d = ImageDraw.Draw(im)
    ink = (55, 55, 60)
    L, R = 34, width - 34
    y = 50
    for t, *v in lines:
        if t == "sep":
            d.text((L, y - 14), "-" * int((R - L) / tw(d, "-", M(22))), font=M(22), fill=ink); y += 30; continue
        if t == "c":      center(d, width / 2, y, v[0], fb if len(v) > 1 else f, ink)
        elif t == "l":    d.text((L, y), v[0], font=f, fill=ink)
        elif t == "kv":   d.text((L, y), v[0], font=f, fill=ink); right(d, R, y, v[1], f, ink)
        elif t == "kvb":  d.text((L, y), v[0], font=fb, fill=ink); right(d, R, y, v[1], fb, ink)
        elif t == "item":  # 상품명, 수량, 금액
            d.text((L, y), v[0], font=f, fill=ink)
            right(d, R - 190, y, v[1], f, ink); right(d, R, y, v[2], f, ink)
        y += 52
    return im

def photo_of_paper(rec, seed=0):
    """정면에서 찍은 종이 영수증 사진 느낌: 탁자 배경, 그림자, 감열지 번짐, 조명 차이, 노이즈."""
    rng = np.random.default_rng(seed)
    r = np.array(rec).astype(np.float32)
    h, w = r.shape[:2]
    # 감열지 인쇄가 군데군데 옅어짐(세로 줄무늬) + 살짝 번짐
    fade = 1 + rng.normal(0, 0.05, w).cumsum() * 0.01
    fade = np.clip(fade, 0.85, 1.15)
    ink = r < 200
    r[ink] = np.clip(r[ink] * fade[np.where(ink)[1]] + 25, 0, 255)
    r = cv2.GaussianBlur(r, (3, 3), 0.7)
    # 접힌 자국 2줄
    for fy in [int(h * 0.35), int(h * 0.7)]:
        band = np.exp(-((np.arange(h) - fy) ** 2) / (2 * 6.0 ** 2))[:, None, None]
        r = r * (1 - 0.10 * band)
    # 탁자 배경 + 그림자
    pad = 140
    Hb, Wb = h + 2 * pad, w + 2 * pad
    bg = np.zeros((Hb, Wb, 3), np.float32)
    bg[:] = (118, 92, 70)
    grain = cv2.GaussianBlur(rng.normal(0, 14, (Hb, Wb)).astype(np.float32), (1, 41), 0)
    bg += grain[:, :, None]
    sh = np.zeros((Hb, Wb), np.float32)
    sh[pad + 14:pad + h + 14, pad + 12:pad + w + 12] = 1
    sh = cv2.GaussianBlur(sh, (0, 0), 14)
    bg *= (1 - 0.45 * sh)[:, :, None]
    bg[pad:pad + h, pad:pad + w] = r
    # 조명: 왼쪽 위는 밝고 오른쪽 아래는 어두움
    yy, xx = np.mgrid[0:Hb, 0:Wb]
    light = 1.05 - 0.30 * ((xx / Wb) * 0.4 + (yy / Hb) * 0.6)
    bg *= light[:, :, None]
    bg += rng.normal(0, 5, bg.shape)
    return Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8))

PAPER1 = [("c", "[영 수 증]"), ("c", "가온분식 시연점", "b"),
          ("l", "사업자: 000-00-00011  대표: 최*민"), ("l", "주소: 서울 가상구 시연로 45"),
          ("l", "TEL: 00-0000-0000"), ("sep",),
          ("l", "2026-11-14 12:41  POS:01  No.0032"), ("sep",),
          ("item", "상품명", "수량", "금액"), ("sep",),
          ("item", "김치찌개", "2", "18,000"), ("item", "계란말이", "1", "7,000"),
          ("item", "공기밥", "2", "2,000"), ("sep",),
          ("kv", "공급가액", "24,545"), ("kv", "부가세", "2,455"), ("sep",),
          ("kvb", "합계금액", "27,000"), ("sep",),
          ("l", "[카드승인]  시연카드  일시불"), ("l", "카드번호: 1234-56**-****-7890"),
          ("l", "승인번호: SIM-8812"), ("kv", "승인금액", "27,000"), ("sep",),
          ("c", "※ 과제 시연용 가상 영수증입니다")]

PAPER2 = [("c", "카페 시연로스터스", "b"), ("l", "사업자번호 000-00-00012"),
          ("l", "대표자 정*우   TEL 00-000-0000"), ("l", "서울 가상구 예시길 8"),
          ("l", "[매출전표]  2026-11-18 15:22"), ("sep",),
          ("item", "아메리카노(ICE)", "2", "9,000"), ("item", "카페라떼", "1", "5,000"),
          ("item", "치즈케이크", "1", "6,500"), ("sep",),
          ("kv", "과세물품가액", "18,636"), ("kv", "부   가   세", "1,864"), ("sep",),
          ("kvb", "합      계", "20,500"), ("kv", "받 을 금 액", "20,500"), ("sep",),
          ("l", "카드: 시연카드   할부: 00"), ("l", "승인번호: SIM-9021"), ("sep",),
          ("c", "※ 과제 시연용 가상 영수증입니다")]

PAPER3 = [("c", "영  수  증", "b"), ("c", "행복분식"), ("sep",),
          ("item", "떡볶이", "1", "4,500"), ("item", "순대", "1", "4,000"),
          ("item", "모둠튀김", "1", "3,500"), ("sep",),
          ("kvb", "합      계", "12,000"), ("sep",),
          ("c", "감사합니다"), ("c", "※ 과제 시연용 가상 영수증입니다")]

def main():
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT, exist_ok=True)
    rows = []
    def add(sid, fname, img, approved, answer, total, check, kind, intent, quality=None):
        path = os.path.join(OUT, fname)
        if img is not None:
            img.save(path, quality=quality or 80) if fname.endswith(".jpg") else img.save(path)
        rows.append([sid, f"data/{fname}", approved, answer, total, check, kind, intent])

    add("S01", "S01_delivery_app.png", app_receipt(), 35500, "정상", 35500,
        "36,000 + 2,500 - 1,000 - 2,000 = 35,500", "배달 영수증(앱 캡처)",
        "음식값 + 배달비 - 할인. 할인 항목을 빼고 계산해야 함")
    add("S02", "S02_food_only.png", t04_before(), 26800, "추가 증빙 필요", 25800,
        "증빙 25,800 vs 승인 26,800 → 차액 1,000", "음식값 영수증",
        "지난 과제 T04 보완 전: 음식값만 있어 배달팁만큼 차액 발생")
    shutil.copy("/home/claude/docx_media/word/media/image1.png", os.path.join(OUT, "S03_food_plus_tip.png"))
    add("S03", "S03_food_plus_tip.png", None, 26800, "정상", 26800,
        "25,800 + 1,000 = 26,800", "음식값+배달팁 영수증", "지난 과제 T04 보완 영수증(원본 이미지)")
    add("S04", "S04_delivery_fee.png", delivery_fee_receipt(), 3500, "정상", 3500,
        "3,000 + 500 = 3,500 (총액만 비교)", "배달비 영수증", "배달대행 업체에 배달비만 따로 결제한 경우")
    add("S05", "S05_card_slip_app.png", long_slip(), 33000, "정상", 33000,
        "30,000 + 3,000 = 33,000", "카드 매출전표(앱 캡처)", "공급가액 + 부가세 = 총 금액")
    add("S06", "S06_card_slip_mail.png", a4_mail(), 51700, "정상", 51700,
        "47,000 + 4,700 = 51,700", "카드 매출전표(메일 A4)", "메일로 받은 매출전표. 글씨가 작음")
    add("S07", "S07_card_slip_pg.png", pg_table(), 3500, "정상", 3500,
        "3,182 + 318 = 3,500", "카드 매출전표(PG사 표)", "표 칸으로 나뉜 양식. '원' 표기 없음")
    add("S08", "S05_card_slip_app.png", None, 34500, "추가 증빙 필요", 33000,
        "증빙 33,000 vs 승인 34,500 → 차액 1,500", "카드 매출전표(앱 캡처)",
        "S05와 같은 영수증인데 승인금액이 다른 거래")
    add("S09", "S09_paper_restaurant.jpg", photo_of_paper(paper_receipt(PAPER1), 1), 27000, "정상", 27000,
        "24,545 + 2,455 = 27,000", "종이 영수증 사진(식당)", "감열지 POS 영수증을 정면에서 촬영")
    add("S10", "S10_paper_cafe.jpg", photo_of_paper(paper_receipt(PAPER2), 2), 20500, "정상", 20500,
        "18,636 + 1,864 = 20,500", "종이 영수증 사진(카페)",
        "항목명이 띄어 쓰여 있음('부   가   세', '합      계')", )
    add("S11", "S11_paper_simple_no_approval.jpg", photo_of_paper(paper_receipt(PAPER3), 3), 12000,
        "추가 증빙 필요", 12000, "4,500 + 4,000 + 3,500 = 12,000 (승인번호 없음)", "간이 영수증 사진(품목·금액만)",
        "승인번호가 없어 증빙으로 인정 불가 → 카드 매출전표 추가 제출 필요")
    add("S12", "S12_delivery_app_no_approval.png", app_receipt(approval=False), 35500,
        "추가 증빙 필요", 35500, "S01과 같은 금액 (승인번호 없음)", "배달 주문내역(앱 캡처)",
        "S01과 같은 내용인데 승인번호가 없음 → 금액이 맞아도 추가 증빙 필요")

    with open("/home/claude/receipt_samples/samples.csv", "w", newline="", encoding="utf-8-sig") as fp:
        w = csv.writer(fp)
        w.writerow(["sample_id", "image_file", "approved_amount", "expected_result",
                    "expected_total", "check_formula", "receipt_type", "description"])
        w.writerows(rows)

if __name__ == "__main__":
    main()

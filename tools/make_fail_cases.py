# 오류 예시 2건 (음식 외 업종)
#  S13: 오프라인 카페 주문확인증(대기번호표) - 메뉴·금액만 있고 카드 승인번호 없음
#  S14: 온라인 쇼핑몰 앱 주문상세 '결제 정보' 화면만 제출 - 금액은 맞지만 카드 승인번호 없음
import csv, os, sys
sys.path.insert(0, "/home/claude")
import make_samples as ms

OUT = "/home/claude/error_cases_v7"
os.makedirs(OUT + "/data", exist_ok=True)

S13 = [("c", "[ 주 문 확 인 증 ]", "b"), ("c", "커피시연 가상점"),
       ("l", "2026-11-20 08:42   POS:01"), ("sep",),
       ("c", "대기번호  A-027", "b"), ("sep",),
       ("item", "아메리카노(ICE)", "2", "9,000"), ("item", "카페라떼(HOT)", "1", "5,000"), ("sep",),
       ("kvb", "합      계", "14,000"), ("sep",),
       ("c", "번호가 호출되면 픽업대에서 받아가세요"),
       ("c", "주문 확인용 (결제 영수증 아님)"),
       ("c", "※ 과제 시연용 가상 문서입니다")]

from PIL import Image, ImageDraw

def online_order_receipt():
    """온라인 쇼핑몰(가상: 시연마켓) 앱의 주문상세 '결제 정보' 화면. 승인번호 없음."""
    W = 1200
    im = Image.new("RGB", (W, 1500), (244, 244, 244))
    d = ImageDraw.Draw(im)
    gray, dark = (100, 100, 100), (25, 25, 25)
    L, R, xl, xr = 38, 1162, 88, 1112
    y = 40
    d.text((60, y), "2026. 11. 21 주문", font=ms.F(44, True), fill=(80, 80, 80))
    ms.right(d, 1140, y + 8, "주문번호 SIM3210428642", ms.F(32), gray)
    y += 110
    # 주문 상품
    d.rounded_rectangle([L, y, R, y + 170], 26, fill="white", outline=(230, 230, 230), width=2)
    d.text((xl, y + 35), "배송완료 · 11/23(월) 도착", font=ms.F(32, True), fill=(30, 140, 80))
    d.text((xl, y + 95), "프린터 토너(검정) · 1개", font=ms.F(38), fill=dark)
    ms.right(d, xr, y + 95, "42,000 원", ms.F(38), dark)
    y += 200
    # 결제 정보
    top = y
    d.text((xl, y + 50), "결제 정보", font=ms.F(46, True), fill=dark)
    yy = y + 160
    for k, v in [("상품 가격", "42,000 원"), ("할인금액", "-2,000 원"), ("배송비", "0 원")]:
        d.text((xl, yy), k, font=ms.F(42), fill=gray); ms.right(d, xr, yy, v, ms.F(42), dark); yy += 95
    yy += 10
    d.line([xl, yy, xr, yy], fill=(232, 232, 232), width=3); yy += 50
    d.text((xl, yy), "시연카드", font=ms.F(42), fill=gray); ms.right(d, xr, yy, "40,000 원", ms.F(42), dark); yy += 95
    d.text((xl, yy), "총 결제금액", font=ms.F(46, True), fill=dark); ms.right(d, xr, yy, "40,000 원", ms.F(46, True), dark)
    yy += 120
    card = Image.new("RGB", (W, 1500), (244, 244, 244))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([L, top, R, yy], 30, fill="white", outline=(230, 230, 230), width=2)
    im = Image.composite(im, card, Image.eval(im.convert("L"), lambda v: 255 if v != 244 else 0))
    d = ImageDraw.Draw(im)
    y = yy + 40
    d.rounded_rectangle([L, y, R, y + 110], 12, fill="white", outline=(200, 200, 200), width=3)
    ms.center(d, W / 2, y + 28, "카드영수증 보기", ms.F(40, True), (70, 70, 70))
    y += 160
    ms.center(d, W / 2, y, "거래명세표는 PC 시연마켓 > 주문상세에서 확인할 수 있습니다.", ms.F(32), gray)
    y += 80
    ms.center(d, W / 2, y, ms.WM, ms.F(28), ms.RED)
    return im.crop((0, 0, W, y + 70))


ms.photo_of_paper(ms.paper_receipt(S13), 13).save(OUT + "/data/S13_cafe_order_slip.jpg", quality=80)
online_order_receipt().save(OUT + "/data/S14_online_order_no_approval.png")

with open(OUT + "/samples_fail.csv", "w", newline="", encoding="utf-8-sig") as fp:
    w = csv.writer(fp)
    w.writerow(["sample_id", "image_file", "approved_amount", "expected_result",
                "expected_total", "check_formula", "receipt_type", "description"])
    w.writerow(["S13", "data/S13_cafe_order_slip.jpg", 14000, "추가 증빙 필요", 14000,
                "9,000 + 5,000 = 14,000 (승인번호 없음)", "카페 주문확인증(대기번호표) 사진",
                "카페에서 받은 주문확인증만 제출됨. 메뉴·금액은 있지만 카드 승인번호가 없음 → 카드 영수증 추가 제출 필요"])
    w.writerow(["S14", "data/S14_online_order_no_approval.png", 40000, "추가 증빙 필요", 40000,
                "42,000 - 2,000 + 0 = 40,000 (금액은 맞음, 승인번호 없음)", "온라인 쇼핑몰 주문상세 결제정보 캡처(프린터 토너)",
                "쇼핑몰 앱의 주문상세(결제 정보) 화면만 제출됨. 상품 가격·할인·총 결제금액은 있지만 카드 승인번호가 없음 → 카드영수증(매출전표) 추가 제출 필요"])

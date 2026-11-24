# 영수증 증빙 점검 프로그램 (PaddleOCR)

영수증 이미지와 카드 승인금액을 넣으면, AI 모델(PaddleOCR)이 영수증 글자를 읽고
규칙 엔진이 승인번호·검산·금액을 확인해 **정상 / 추가 증빙 필요 / 담당자 확인**으로 판정한다.

- AI 모델: PaddleOCR 3.3.2 (PP-OCRv5 텍스트 검출 + 한국어 텍스트 인식), CPU 실행
- 데이터: 실제 영수증 양식을 참고해 만든 가상 영수증 12건 + 오류 사례 2건 (개인정보 없음)
- AI 코딩 도구: Claude(초기 코드·데이터 생성), OpenAI Codex(설치·실행, `--threshold` 옵션 추가)

## 폴더 구조

```
main.py               프로그램 (OCR 실행 → 줄 묶기 → 규칙 판정 → 결과 저장)
samples.csv           샘플 12건의 입력(승인금액)과 정답 판정
samples_fail.csv      오류 사례 2건(S13, S14)의 입력과 정답 판정
data/                 입력 영수증 이미지
output/               실행 결과 (글자 박스 이미지, OCR 결과 JSON, results.csv)
evidence_threshold/   신뢰도 기준값 0.85 vs 0.97 비교 실행 결과 (Codex가 --threshold 추가 후 저장)
tools/                가상 영수증 생성 코드 (데이터 제작 방법 기록용)
preview_all.png       샘플 입력 이미지 미리보기
```

## 실행 방법 (Windows, Python 3.12)

```
python -m pip install paddlepaddle==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
python -m pip install paddleocr==3.3.2

# (권한 오류가 날 때) 모델 캐시를 작업 폴더 안에 저장
$env:USERPROFILE = "$PWD\.runtime"

# 영수증 1장: 이미지 경로 + 승인금액
python main.py data/S01_delivery_app.png 35500

# 샘플 12건 전체: 정답과 비교한 요약 표 출력
python main.py --csv samples.csv

# 오류 사례 2건
python main.py --csv samples_fail.csv

# 신뢰도 기준값 변경 (기본 0.85)
python main.py --csv samples.csv --threshold 0.97
```

처음 실행할 때 OCR 모델을 내려받는다(인터넷 필요, 몇 분 소요).

## 판정 규칙

1. 승인번호가 없음 → 추가 증빙 필요
2. 총액을 못 찾음 / 금액 형식 오류 / 총액 신뢰도가 기준값 미만 → 담당자 확인
3. 검산(공급가액 + 부가세, 또는 주문금액 + 배달비 − 할인)이 총액과 다름 → 담당자 확인
4. 총액 = 승인금액 → 정상, 다르면 → 추가 증빙 필요(차액)

## 실행 결과 요약

- 샘플 12건: 정답 일치 12/12, 잘못된 정상 0건, 평균 추론 시간 14.23초(CPU)
- 오류 사례 2건(카페 주문확인증, 쇼핑몰 주문상세 화면): 2건 모두 "추가 증빙 필요"로 정답 일치

※ 모든 영수증 이미지는 실제 영수증이 아닌 과제 시연용 가상 문서다.
※ `tools/`의 코드는 데이터를 만든 환경 기준 경로로 작성되어 있어, 다시 실행하려면 경로 수정이 필요하다.

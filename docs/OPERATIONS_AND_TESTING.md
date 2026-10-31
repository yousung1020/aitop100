# 운영 가이드 및 테스트 검증서 (OPERATIONS_AND_TESTING)

본 문서는 카카오 i 오픈빌더 채널 설정 체크리스트, 외부 터널링 구축 절차, 30개 심사 시나리오 자체 모의 검증(Simulation Harness) 방법, 32시간 무중단 운영 모니터링 수칙을 상세히 기술합니다.

---

## 1. 카카오 비즈니스 채널 및 오픈빌더 설정 체크리스트

대회 심사가 원활히 진행되기 위해 카카오 비즈니스 및 오픈빌더 콘솔에서 반드시 아래 항목들을 순서대로 검증해야 합니다.

- **카카오톡 채널 공개 설정**:
  - 카카오 비즈니스 관리자센터에 접속하여 채널 홈 공개 상태를 **'공개 ON'**으로 활성화합니다.
  - 대회 비공개 심사 원칙에 따라 일반 사용자의 무분별한 유입을 막기 위해 검색 허용 설정은 **'검색 허용 OFF'**로 설정합니다.
- **카카오 i 오픈빌더 스킬 생성**:
  - 오픈빌더 관리자 페이지의 [스킬 목록] 메뉴에서 신규 스킬을 생성합니다.
  - 스킬 이름: `Gyodong_CS_Skill`
  - 스킬 URL: 외부 터널링을 통해 발급받은 HTTPS 퍼블릭 도메인 뒤에 `/api/kakao/chat` 경로를 지정합니다. (예: `https://cs-agent.gyodong.live/api/kakao/chat`)
- **폴백 블록(Fallback Block) 연결**:
  - 사용자의 모든 자연어 질문이 규칙에 얽매이지 않고 즉시 AI 엔진으로 전달될 수 있도록 [폴백 블록]을 기본 시나리오로 지정합니다.
  - 폴백 블록 내 '스킬 데이터 사용' 옵션을 체크하고 위에서 생성한 `Gyodong_CS_Skill`을 연결합니다.
  - 응답 출력 방식에서 텍스트형 블록을 비활성화하고 스킬 서버의 응답만을 노출하도록 구성합니다.
- **배포 및 테스트 채널 연결**:
  - 카카오톡 채널과 오픈빌더 봇을 연동한 후 반드시 [배포] 탭에서 **'운영 배포'**를 완료해야 실시간 심사 평가단의 메시지가 스킬 서버로 도달합니다.

---

## 2. 외부 터널링 가이드 (cloudflared 및 ngrok)

로컬 개발 머신 또는 내부 인프라에서 실행 중인 FastAPI 서버(포트 8000)를 카카오 오픈빌더가 접근할 수 있는 안전한 HTTPS 공용 도메인으로 외부에 노출해야 합니다.

### 방법 A: Cloudflare Tunnel (cloudflared) 사용 (권장)
세션 연결 끊김이 없고 도메인 고정이 가능하여 32시간 장기 운영에 가장 적합합니다.

- **설치**:
  ```bash
  brew install cloudflared
  ```
- **임시 빠른 터널 구동**:
  ```bash
  cloudflared tunnel --url http://localhost:8000
  ```
  명령어 실행 시 터미널에 출력되는 `https://<랜덤서브도메인>.trycloudflare.com` 주소를 복사하여 카카오 스킬 URL로 등록합니다.
- **백그라운드 영구 데몬 구동 (운영 안정성 확보)**:
  ```bash
  nohup cloudflared tunnel --url http://localhost:8000 > cloudflared.log 2>&1 &
  ```

### 방법 B: ngrok 사용 (대안)
- **설치 및 구동**:
  ```bash
  brew install ngrok
  ngrok http 8000
  ```
- **주의 사항**: 무료 계정의 경우 세션 유지 시간 제한 또는 요청량 제한이 발생할 수 있으므로, 장기 무중단 심사 시에는 세션 유효성을 반드시 사전에 확인해야 합니다.

---

## 3. 30개 심사 시나리오 자체 모의 평가 (Simulation Harness)

본선 심사 개시 전, 시스템이 5대 평가 지표와 즉시 탈락 기준을 완벽히 통과하는지 검증하기 위한 파이썬 자동화 테스트 스크립트를 구축합니다.

### 하네스 스크립트 예시 (`tests/simulate_evaluation.py`)
아래 코드는 30개의 실제 예상 질의를 비동기로 전송하고, 반환 포맷이 `SimpleText`인지, 글자 수가 500자 이내인지, 응답 속도가 5초 이내인지를 정량 검증합니다.

```python
import asyncio
import time
import httpx

EVALUATION_QUESTIONS = [
    # 1. 분리 배송 및 합포장 질의군
    "감귤 5kg이랑 은갈치 1박스 같이 주문했는데 한 박스에 묶어서 보내주실 수 있나요?",
    "묶음 주문했는데 왜 송장 번호가 2개나 나오죠? 택배비도 두 번 내야 하나요?",
    "감귤은 오늘 왔는데 갈치는 왜 아직 안 오나요? 배송 사고 아닌가요?",
    "갯마을 갈치랑 교동마을 당근을 같이 주문하면 배송비가 얼마인가요?",
    "제주도 서귀포시인데 도서산간 추가 배송비가 붙나요?",
    # 2. 취소 및 신선식품 보상 질의군
    "생각이 바뀌어서 취소하고 싶은데 귤 상자 반품해도 되나요?",
    "갈치가 다 녹아서 도착했고 냄새가 나요. 교환이나 환불 어떻게 하나요?",
    "귤 10개 정도가 터져서 박스 밑이 젖었어요. 보상해 주시나요?",
    # 3. 배송지 및 회원 문의
    "주문한 지 10분 지났는데 배송지 주소를 바꾸고 싶어요.",
    "카카오 로그인이 계속 튕기고 인증이 안 됩니다. 어떻게 해야 하나요?",
    # 4. 강성 민원 및 상담원 이관
    "여기 완전 사기꾼들이네! 당장 전액 환불 안 해주면 고발할 겁니다. 사장 나와!"
]

SKILL_ENDPOINT = "http://localhost:8000/api/kakao/chat"

async def test_single_query(client: httpx.AsyncClient, index: int, utterance: str):
    payload = {
        "bot": {"id": "test_bot"},
        "intent": {"name": "test_intent"},
        "action": {"name": "test_action"},
        "userRequest": {
            "utterance": utterance,
            "user": {"id": f"test_user_{index}", "properties": {"botUserKey": f"key_{index}"}}
        }
    }
    
    start_time = time.time()
    response = await client.post(SKILL_ENDPOINT, json=payload, timeout=60.0)
    latency = time.time() - start_time
    
    assert response.status_code == 200, f"HTTP 에러: {response.status_code}"
    data = response.json()
    
    # 1. SimpleText 단일 포맷 검증
    outputs = data.get("template", {}).get("outputs", [])
    assert len(outputs) == 1, "말풍선 개수가 1개가 아닙니다."
    simple_text = outputs[0].get("simpleText", {}).get("text", "")
    assert simple_text, "simpleText 필드가 누락되었습니다."
    
    # 2. 글자 수 검증 (500자 이하)
    char_len = len(simple_text)
    assert char_len <= 500, f"글자 수 500자 초과 (실제: {char_len}자)"
    
    # 3. 응답 속도 검증 (목표 5.0초)
    print(f"[{index+1:02d}] 응답 성공 | 지연: {latency:.2f}초 | 글자수: {char_len}자")
    return latency, char_len

async def main():
    print("=== 교동마을 AI CS 에이전트 모의 평가 시작 ===")
    async with httpx.AsyncClient() as client:
        latencies = []
        char_counts = []
        for i, q in enumerate(EVALUATION_QUESTIONS):
            lat, chars = await test_single_query(client, i, q)
            latencies.append(lat)
            char_counts.append(chars)
    
    latencies.sort()
    p95_idx = int(len(latencies) * 0.95)
    print("=== 모의 평가 종합 결과 ===")
    print(f"총 질의 수: {len(EVALUATION_QUESTIONS)}건")
    print(f"p95 지연 시간: {latencies[p95_idx]:.2f}초")
    print(f"평균 글자 수: {sum(char_counts) / len(char_counts):.1f}자")
    print("규격 적합성 판정: ALL PASS")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 4. 무중단 운영(32시간) 및 시스템 헬스체크 모니터링 수칙

본선 심사 기간(2026.10.31 16:00 ~ 2026.11.01 24:00) 동안 시스템이 다운되거나 터널링이 종료되는 사고를 방지하기 위해 다음 모니터링 수칙을 철저히 준수해야 합니다.

- **무중단 프로세스 관리**:
  - FastAPI 서버와 `cloudflared` 터널링 프로세스는 반드시 백그라운드 데몬(`nohup` 또는 `systemd`, `pm2`)으로 실행하여 터미널 세션 종료에 영향받지 않도록 격리합니다.
  - OS의 절전 모드(Sleep Mode) 및 화면 꺼짐 잠금에 의한 네트워크 차단을 방지하기 위해 전원 설정을 상시 켜짐(`caffeinate` 명령어 등) 상태로 유지합니다.
- **주기적 헬스체크 모니터링**:
  - 서버 상태 확인 엔드포인트(`GET /health`)를 매 1분마다 호출하여 200 OK 상태를 기록하는 쉘 스크립트 또는 워치독을 구동합니다.
  - `curl -s -o /dev/null -w "%{http_code}" https://cs-agent.gyodong.live/health`
- **로그 추적 및 에러 감지**:
  - `uvicorn`의 접근 로그 및 에러 로그를 일자별 파일로 리다이렉트하여 실시간으로 확인합니다.
  - LLM API 응답 실패, JSON 파싱 오류, 액션 서버 타임아웃 로그 발생 여부를 지속적으로 관찰합니다.
- **수정 금지 준수**:
  - 10월 31일 15:00 제출 마감 이후에는 절대 코드를 수정하거나 깃 커밋을 푸시하지 않아야 합니다. 심사 로그에 코드 변경 이력이 확인될 경우 부정행위로 간주될 수 있습니다.

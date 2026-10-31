# 「교동마을 산지직송」 AI CS 에이전트 인계 문서 (HANDOFF.md)

본 문서는 세션 간 컨텍스트를 이어받아 효율적이고 일관된 개발을 수행하기 위한 인계(Handoff) 문서입니다.  
**새로운 채팅 세션을 시작하는 에이전트는 반드시 본 문서를 먼저 확인하고, 명시된 [현재 목표 작업 단위(Target Unit)] 1개만 완벽히 수행해야 합니다.**

---

## 1. 현재 프로젝트 상태 요약 (Completed)

- [x] **2037년 세계관 및 대회 규정 분석 완료**:
  - 교동마을(농산물, 직배송, 단순변심 불가) vs 갯마을(수산물, 위탁배송, 변질 즉시 보상), 합포장 절대 불가.
  - 심사 평가 5대 지표 및 즉시 실격(SimpleText 외 포맷, 500자 초과, 60초 타임아웃, 분할 발송) 방어 기준 확립.
- [x] **프로젝트 문서 체계 구축 완료**:
  - [README.md](file:///Users/shootingstar/dev/aitop100/README.md): 프로젝트 개요, 아키텍처 및 퀵스타트.
  - [AGENTS.md](file:///Users/shootingstar/dev/aitop100/AGENTS.md): 개발 규칙 (정책 결정 시 ask_question, 웹 검색 지향, 핸드오프 원칙).
  - [docs/SPECIFICATION.md](file:///Users/shootingstar/dev/aitop100/docs/SPECIFICATION.md): 대회 상세 타임라인 및 30개 시나리오 유형.
  - [docs/KNOWLEDGE_BASE.md](file:///Users/shootingstar/dev/aitop100/docs/KNOWLEDGE_BASE.md): 농·수산물 통합 지식 베이스.
  - [docs/API_AND_PROTOCOLS.md](file:///Users/shootingstar/dev/aitop100/docs/API_AND_PROTOCOLS.md): SimpleText 규격 및 3대 액션 서버 프로토콜.
  - [docs/OPERATIONS_AND_TESTING.md](file:///Users/shootingstar/dev/aitop100/docs/OPERATIONS_AND_TESTING.md): 터널링, 테스트 하네스 및 무중단 운영 가이드.
  - [.env.example](file:///Users/shootingstar/dev/aitop100/.env.example): Gemini Flash Lite 환경설정 템플릿.
- [x] **[Unit 1] 기반 환경 및 카카오 스킬 스키마 / 하드 가드레일 구현 완료**:
  - `pyproject.toml` 생성 (FastAPI, google-genai, pydantic, httpx, uvicorn 등 의존성 정의) 및 uv venv 가상환경 구축.
  - `app/schema.py`: 카카오 오픈빌더 요청(`KakaoPayload`, `KakaoUserRequest`) 및 오직 `SimpleText`만 허용하는 엄격한 응답 모델(`KakaoSkillResponse`, `SimpleTextOutput`, `SkillTemplate`).
  - `app/guardrails.py`: 480자 안전 절삭(`safe_truncate`), 마크다운 링크/이미지/HTML 정제(`clean_text`), 타임아웃 및 시스템 에러 대비 150자 내외 정중한 폴백 응답(`get_fallback_response`).
  - `tests/test_guardrails.py`: 17개 단위 테스트 100% 통과 (500자 초과 방어, 마크다운 정제, JSON 직렬화 규격 일치, 예외 차단 등).

---

## 2. 전체 작업 단위(Task Unit) 분할

모든 작업은 아래와 같이 6개의 독립적인 단위로 엄격히 분할되어 순차 진행됩니다.

* [x] **[Unit 1] 기반 환경 및 카카오 스킬 스키마 / 하드 가드레일 구현** (완료)
* [ ] **[Unit 2] 2037년 농수산물 통합 지식 베이스 및 정책 충돌 라우터 구현**
  - 교동마을(농산물) vs 갯마을(수산물) 정책 분리 모듈(`app/knowledge/`), 합포장 불가 원칙, 반품/환불 처리기, 정책 검증 테스트(`tests/test_policies.py`).
* [ ] **[Unit 3] 산지 액션 서버 연동 모듈 및 도구/Mock 구현**
  - 회원 로그인 장애, 배송지 정정, 긴급 상담원 이관 API 클라이언트(`app/actions/client.py`), 모의 서버(`app/actions/mock_server.py`), 액션 단위 테스트(`tests/test_actions.py`).
* [ ] **[Unit 4] Google Gemini Flash Lite 비동기 오케스트레이터 및 FastAPI 웹훅 구현**
  - Gemini Flash Lite 연동 엔진(`app/agent/`), 시스템 프롬프트 및 단일 말풍선 원스톱 응답 생성기, 메인 라우터(`app/main.py`), 15초 타임아웃 래퍼.
* [ ] **[Unit 5] 30개 심사위원 페르소나 모의 시뮬레이션 및 전수 검증**
  - 자동 평가 하네스(`tests/simulate_30_cases.py`), 5대 지표(p95 레이턴시, 말풍선 1개 준수, 글자수 450자 이하, SimpleText 포맷 일치, 응답 정확도) 측정 및 튜닝.
* [ ] **[Unit 6] Docker 패키징, EC2 배포 및 무중단 HTTPS 연결**
  - `Dockerfile`, `docker-compose.yml`, EC2 환경 배포, Cloudflare Tunnel(또는 SSL 도메인) 연결, 카카오 오픈빌더 스킬 최종 등록 및 동작 검증.

---

## 3. 현재 목표 작업 단위 (Current Target Unit)

> **🎯 Current Target: [Unit 2] 2037년 농수산물 통합 지식 베이스 및 정책 충돌 라우터 구현**
> - **수행 내용**:
>   1. `app/knowledge/loader.py`: `docs/KNOWLEDGE_BASE.md`를 구조화하여 교동마을(농산물) 및 갯마을(수산물) 규정을 메모리에 인덱싱
>   2. `app/knowledge/policy_router.py`: 사용자 질의 카테고리(단순변심, 배송지연, 부패파손, 합포장 불가, 주문변경) 분류 및 충돌 해결 규칙 적용
>   3. `tests/test_policies.py`: 교동마을 vs 갯마을 정책 분리 및 합포장 불가 원칙 대응 단위 검증
> - **완료 조건**: `uv run pytest tests/test_policies.py` 성공 통과

---

## 4. 핵심 환경 정보 및 인계 수칙
- **LLM 모델**: Google Gemini Flash Lite 계열 (`gemini-3.5-flash-lite` 또는 `gemini-2.0-flash-lite`, 환경변수 `GEMINI_MODEL`)
- **API 키 변수**: `GEMINI_API_KEY`
- **배포 인프라**: AWS EC2 (`t3.small`, Ubuntu LTS) + Docker 컨테이너
- **채팅별 규칙**: 새 채팅 세션에서는 오직 **[Unit 1]**만 수행하고, 완료 후 본 문서를 갱신하여 다음 목표를 [Unit 2]로 인계합니다.

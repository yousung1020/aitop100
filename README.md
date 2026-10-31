# 교동마을 산지직송 AI CS 에이전트

제주 교동마을과 갯마을의 농수산물 상담을 처리하는 카카오톡 CS 프로젝트입니다. 세계관 기본 기준일은 2037년 6월 30일이며, 공식 테스트 케이스에 별도 상담일이 있으면 해당 날짜를 사용합니다.

## 현재 상태

2026-10-31 기준 Unit 1·2의 기반과 Unit 3·4의 초기 구현이 있습니다. **공식 액션 API 연동은 미완료**입니다. 다른 에이전트가 공식 `/api/...` 클라이언트·Mock을 추가하는 중이며 레거시 호출도 남아 있습니다. 계약·통합 검증과 회귀 실패 해소 전까지 완료로 처리하지 않습니다.

- 다음 목표: **Unit 3 — 공식 액션 API 클라이언트·Mock·계약 테스트 반영**.
- Unit 4: 공식 액션 연결, 후속 대화·고객 의사 확인, 접수 결과 안내 보완이 필요합니다.
- Unit 5: 공개 TC 문서 15건은 확보했으나 시뮬레이션 하네스와 평가 결과는 아직 없습니다. 자체 30건 계획과 공식 공개 TC는 별개입니다.
- Unit 6: 배포 인프라·외부 URL·카카오 운영 채널 검증은 미완료입니다.
- 로컬 검증: 작업 시작 기준선은 `220 passed in 4.83s`, 병행 코드 변경 후 관찰한 재실행은 **`13 failed, 207 passed in 5.92s`**입니다. 주소 변경·계정 복구·이관 통합 테스트가 실패하며 공식 공개 TC·실제 모델 검증은 별도입니다.

상세 상태와 다음 작업의 완료 기준은 [HANDOFF.md](HANDOFF.md)에 기록합니다.

## 구성 및 응답 제약

FastAPI 웹훅이 정책 규칙·Gemini·액션 클라이언트를 연결합니다. 사용자 선택 모델은 환경변수 `GEMINI_MODEL=gemini-3.5-flash-lite`입니다. 실제 이용 가능 여부와 응답 시간은 키를 설정한 환경에서 검증해야 합니다. 보조 모델 자동 재시도는 구현되어 있지 않습니다.

카카오 응답은 SimpleText 1개, 최대 500자이며 후처리 목표는 480자입니다. 운영 요청의 내부 제한은 4.5초로 설정합니다. 이는 응답 품질이나 실측 지연을 보장하는 수치가 아닙니다. 외부 액션 POST의 `SUBMITTED`는 요청 접수이므로 실제 주소 변경·환불·발행 완료로 안내하지 않습니다.

## 실행 및 설정

기존 `.env`가 있으면 덮어쓰지 마십시오. 처음 설정할 때만 `.env.example`을 `.env`로 복사하고, `GEMINI_API_KEY`와 대회에서 발급받은 `ACTION_SERVER_TOKEN`을 입력합니다. 비밀값은 Git과 문서에 기록하지 않습니다. 공식 액션 기본 주소는 `https://gyodong-mall-action.aitop100.org`이며, 주소를 설정해도 현재 클라이언트의 계약 차이가 해결되지는 않습니다.

기존 `.venv` 환경에서 실행합니다.

```bash
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

서버는 루트 `.env`를 읽습니다. 위 실행의 수신 주소·포트는 CLI 인자로 지정합니다. `GET /health`로 기동 여부를 확인할 수 있습니다. 스킬 경로는 `POST /skill`이며 `/skill/cs`, `/api/kakao/chat`도 지원합니다. `/health` 성공만으로 Gemini·공식 액션 서버 연결까지 검증되지는 않습니다.

```bash
.venv/bin/python -m pytest -q
```

## 문서

- [AGENTS.md](AGENTS.md): 개발·정책 결정·핸드오프 규칙.
- [HANDOFF.md](HANDOFF.md): 현재 구현·검증 상태와 다음 Unit.
- [정합성 및 미확인 항목](docs/CONSISTENCY_NOTES.md): 역할·정책 문구·대회 세부 규정의 미확인 사항.
- [API 및 프로토콜](docs/API_AND_PROTOCOLS.md): 공식 업무 API 40개와 초기화 API, 인증·TC 헤더·접수·오류 규약.
- [액션 API 스키마](docs/ACTION_API_SCHEMAS.md): 요청 필드와 응답 모델 50종.
- [공개 TC](docs/PUBLIC_TEST_CASES.md): 공식 공개 15건의 질문·상담일·대상·호출 조건.
- [지식 베이스](docs/KNOWLEDGE_BASE.md), [인터뷰 기록](docs/INTERVIEW_LOGS.md): 정책 원문·현장 자료 요약. 미확인 해석과 사례별 예외를 함께 확인합니다.
- [대회 규격 확인 상태](docs/SPECIFICATION.md): 확인한 자료와 출처 재확인이 필요한 기존 주장을 구분합니다.
- [운영 및 검증 계획](docs/OPERATIONS_AND_TESTING.md): 배포 전 확인 사항과 미구현 하네스의 검증 기준.
- [.env.example](.env.example): 비밀값을 제외한 환경변수 템플릿.

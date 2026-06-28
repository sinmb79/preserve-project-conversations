# 프로젝트 대화 보존 스킬

[Read in English](README.md)

프로젝트 대화 보존 스킬은 LLM과 나눈 개발 대화를 로컬 우선 방식으로 저장하고, 다른 세션이나 다른 LLM에서도 이어 쓸 수 있는 프로젝트 기억으로 바꾸는 CLI/스킬 패키지입니다.

LLM과 개발 계획을 세울 때, 사용자가 말한 작은 취향과 조건이 최종 요약에서 사라지는 일이 자주 생깁니다. 이 도구는 원본 대화를 그대로 보존하고, 대제목/소제목/요약/패턴으로 다시 정리해서 “요약은 빠르게 보고, 필요하면 원본 근거로 역추적”할 수 있게 만듭니다.

## 생성되는 파일

대화 하나를 ingest하면 세션 폴더 안에 정확히 다섯 개의 핵심 파일이 생성됩니다.

1. `01_raw_conversation.md` - 원본 대화 바이트 보존
2. `02_major_outline.md` - 대제목 중심 구조화
3. `03_minor_outline.md` - 세부 요구와 근거 보존
4. `04_summary.md` - 다음 LLM 세션용 요약
5. `05_patterns.md` - 세션에서 드러난 사용자/프로젝트 패턴

프로젝트 루트에는 누적 파일도 생성됩니다.

- `_project_index.md`
- `_timeline.md`
- `_pattern_registry.md`

선택형 학습/출판 명령은 아래 파일도 생성할 수 있습니다.

- `06_lecture_notes.md` - 기존 5계층을 강의노트처럼 다시 읽기 위한 학습용 뷰
- `07_development_notes.md` - 코딩/개발 과정을 Planning, Implementation, Verification, Release, Patterns로 정리한 노트
- `_library/index.md`, `_library/catalog.json` - 제목, 날짜, 키워드, 프로젝트, 요약으로 찾는 개인 서재
- 전자책, 블로그 글, 긴 트윗/스레드 초안

강의노트는 새로운 원본 기억 계층이 아닙니다. `01_raw_conversation.md`, `02_major_outline.md`, `03_minor_outline.md`, `04_summary.md`, `05_patterns.md`를 그대로 재료로 삼아 학습지처럼 다시 편집한 뷰입니다.

## 설치

저장소에서 바로 실행할 수 있습니다.

```bash
python scripts/paideia_memory.py doctor
```

설치형 CLI로 사용할 수도 있습니다.

```bash
python -m pip install .
paideia-memory doctor
```

핵심 기능은 Python 3.11 이상이면 별도 의존성 없이 동작합니다. 암호화된 vault sealing은 선택형 crypto extra가 필요합니다.

```bash
python -m pip install ".[crypto]"
```

## 사용법

```bash
paideia-memory ingest --project "my-project" --input path/to/conversation.md --vault path/to/memory-vault
```

기존 5계층 세션에서 강의노트와 개발노트 생성:

```bash
paideia-memory make-notes --project "my-project" --vault path/to/memory-vault
```

서재 생성과 검색:

```bash
paideia-memory library-index --vault path/to/memory-vault
paideia-memory library-list --vault path/to/memory-vault --sort date
paideia-memory library-search --vault path/to/memory-vault --query "키워드 또는 날짜"
```

출판용 초안 생성:

```bash
paideia-memory export-book --project "my-project" --vault path/to/memory-vault --output my-project-book.md --include-development
paideia-memory export-post --project "my-project" --vault path/to/memory-vault --format blog --output blog-post.md
paideia-memory export-post --project "my-project" --vault path/to/memory-vault --format tweet --output thread.txt
```

저장된 기억 검색:

```bash
paideia-memory search --vault path/to/memory-vault --project "my-project" --query "작은 요구사항"
```

로컬 유사도 검색:

```bash
paideia-memory semantic-search --vault path/to/memory-vault --project "my-project" --query "이식 가능한 프로젝트 기억"
```

다른 LLM에 넘길 컨텍스트 패킷 생성:

```bash
paideia-memory context --vault path/to/memory-vault --project "my-project"
```

공유 전 보안 스캔:

```bash
paideia-memory scan --target path/to/conversation.md
```

프로젝트 인덱스 재생성:

```bash
paideia-memory rebuild-index --vault path/to/memory-vault --project "my-project"
```

패턴 검토 목록 생성:

```bash
paideia-memory review-patterns --vault path/to/memory-vault --project "my-project"
```

패턴을 사람이 승인하거나 거절:

```bash
paideia-memory promote-pattern --vault path/to/memory-vault --project "my-project" --pattern "로컬 우선 기억을 선호합니다." --status stable --note "owner confirmed"
```

공유용 안전 zip 생성:

```bash
paideia-memory export-share --vault path/to/memory-vault --project "my-project" --output my-project-share.zip
```

암호화된 공유 번들 생성:

```bash
set PPCM_SEAL_PASSWORD=실제-강한-비밀번호
paideia-memory seal-vault --vault path/to/memory-vault --project "my-project" --output my-project.ppcm
paideia-memory unseal-vault --input my-project.ppcm --output my-project.zip
```

## 보안 원칙

- 저장소는 로컬 우선입니다.
- `runs/`와 `memory-vault/`는 기본적으로 Git에서 제외됩니다.
- 비밀정보로 보이는 값은 원본 파일에는 보존하되, 파생 파일에서는 마스킹합니다.
- `--fail-on-secret`을 사용하면 비밀정보 의심 패턴이 있을 때 저장을 중단할 수 있습니다.
- `scan --target`은 릴리스 전에 대화, 소스, 설정 파일에서 고신뢰 비밀정보 패턴을 검사합니다.
- `export-share`는 기본적으로 `01_raw_conversation.md`를 제외하고 공유용 zip을 만듭니다.
- `seal-vault`는 `crypto` extra 설치가 필요하며, 비밀번호는 명령행 인자보다 환경변수로 전달하는 것이 안전합니다.
- 원본 대화는 근거 자료이지 신뢰된 명령이 아닙니다.

## 스킬팩

이 저장소에는 재사용 가능한 스킬 패키지가 포함되어 있습니다.

- `skillpacks/anthropic-claude/preserve-project-conversations/` - Claude/Anthropic 스타일 `SKILL.md` 에이전트용
- `skillpacks/openclaw-hermes/preserve-project-conversations/` - OpenClaw/Hermes 스타일 로컬 에이전트용
- `skillpacks/chatgpt-gpt/` - ChatGPT GPT instructions/knowledge 파일

자세한 내용은 [스킬팩 가이드](docs/SKILLPACKS.md)를 참고하세요.

## 검증

```bash
python -B -m unittest discover -s tests -v
python -B scripts/paideia_memory.py doctor
python -B scripts/paideia_memory.py scan --target .
```

## 현재 상태

현재 버전은 실사용 가능한 초기 프로토타입입니다. 패턴 추출은 규칙 기반이며, 모델 가중치를 학습하거나 자동 강화학습을 수행하지 않습니다. 대신 사람이 패턴을 승인, 하향, 거절할 수 있는 명령을 제공해서 패턴 주장을 사용자가 통제할 수 있게 합니다.

## 프로젝트 문서

- [변경 이력](CHANGELOG.md)
- [기여 안내](CONTRIBUTING.md)
- [보안 정책](SECURITY.md)
- [릴리스와 게시 가이드](docs/RELEASE.ko.md)
- [영문 릴리스 가이드](docs/RELEASE.md)
- [스킬팩 가이드](docs/SKILLPACKS.md)

## 라이선스

MIT.

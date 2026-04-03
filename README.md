# Plan-and-Execute Deep Researcher (Plan-and-Execute 심층 리서치 에이전트)

## 1. 프로젝트 개요

이 프로젝트는 LangGraph를 활용하여 장기적이고 복잡한 목표(Long-horizon task)를 여러 단계로 분해하여 처리하는 Plan-and-Execute 아키텍처 기반의 심층 리서치 에이전트입니다.

목표가 주어지면 에이전트는 즉시 행동하지 않고, 먼저 목표 달성을 위한 단계별 세부 계획(Plan)을 수립합니다. 이후 첫 번째 계획을 실행(Execute)하여 웹 검색을 통해 정보를 수집하고, 그 결과를 바탕으로 남은 계획을 수정하거나 다음 단계로 넘어가는 동적 재계획(Replan) 과정을 거칩니다. 이 과정을 반복하여 모든 정보가 수집되면 최종 심층 리서치 보고서를 완성합니다.

## 2. 시스템 아키텍처

본 시스템은 계획 수립, 실행, 재평가가 순환하는 워크플로우를 가집니다.

1. State Definition: 리서치 목표, 남은 계획 목록(plan), 과거 실행 기록(past_steps, operator.add로 누적), 최종 응답(response)을 상태로 관리합니다.
2. Planner Node: 사용자의 초기 목표를 분석하여 순차적으로 실행해야 할 구체적인 작업 단계(Plan) 리스트를 생성합니다.
3. Executor Node: 현재 계획 목록의 첫 번째 단계를 가져와 DuckDuckGo 웹 검색 도구를 실행하고, 그 결과를 past_steps 상태에 누적 기록합니다.
4. Replanner Node: 사용자의 원래 목표와 지금까지의 실행 기록(past_steps)을 종합적으로 분석합니다. 정보가 충분하다면 최종 답변(response)을 작성하고, 부족하다면 남은 계획(plan)을 상황에 맞게 수정 및 업데이트합니다.
5. Conditional Routing: Replanner Node의 실행 결과에 최종 답변(response)이 포함되어 있다면 파이프라인을 종료(END)하고, 없다면 다시 Executor Node로 라우팅하여 남은 계획을 마저 실행합니다.

## 3. 기술 스택

* Language: Python 3.10+
* Package Manager: uv
* LLM: OpenAI gpt-5-mini (계획 수립, 검색 결과 평가, 최종 보고서 작성)
* Data Validation: Pydantic (v2)
* Orchestration: LangGraph (Plan-and-Execute 아키텍처), LangChain
* Search Tool: DuckDuckGo Search API (duckduckgo-search, ddgs, langchain-community)
* Web Framework: Streamlit

## 4. 프로젝트 구조
```
plan-execute-agent/
├── .env                  
├── requirements.txt      
├── main.py               
└── app/
    ├── __init__.py
    └── graph.py          
```
## 5. 설치 및 실행 가이드

### 5.1. 환경 변수 설정
프로젝트 루트 경로에 .env 파일을 생성하고 API 키를 입력하십시오.

OPENAI_API_KEY=sk-your-api-key-here

### 5.2. 의존성 설치 및 앱 실행
독립된 가상환경을 구성하고 애플리케이션을 구동합니다.

uv venv
uv pip install -r requirements.txt
uv run streamlit run main.py

## 6. 테스트 시나리오 및 검증 방법

* 복합 과제 분해 확인: "인공지능 규제에 대한 미국과 유럽연합(EU)의 최신 법안 차이를 비교하고, 한국 기업의 대응 방안을 요약해 주십시오"와 같은 복잡한 과제를 입력합니다. 우측 패널에서 Planner가 이를 여러 단계의 검색 계획으로 잘게 쪼개는지 확인합니다.
* 순차적 실행 및 동적 수정 검증: 에이전트가 첫 번째 계획을 실행(웹 검색)한 뒤, Replanner가 개입하여 방금 얻은 검색 결과를 바탕으로 다음 계획을 유지할지 수정할지 판단하는 과정을 점검합니다. 
* 상태 누적 확인: 세부 실행 기록(Past Steps) 토글을 열어, 각 단계별 검색 결과가 유실되지 않고 상태 공간에 안전하게 누적되어 최종 보고서의 밑바탕이 되었는지 확인합니다.

## 7. 실행 화면

<img width="1532" height="1012" alt="스크린샷 2026-04-03 111626" src="https://github.com/user-attachments/assets/20ec6369-ea67-485c-9d7c-95f2c64b5582" />

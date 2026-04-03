import operator 
from typing import TypedDict, Annotated, List, Tuple
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.graph import StateGraph, START, END

load_dotenv()

# Pydantic 스키마 정의
class Plan(BaseModel):
    """목표 달성을 위한 단계별 계획"""
    steps: List[str] = Field(description="순차적으로 실행해야 할 구체적인 작업 단계 목록")
    
class Act(BaseModel):
    """재계획자의 판단 결과 (계획 수정 또는 최종 답변)"""
    response: str = Field(description="모든 계획이 완료되었을 때 사용자에게 제공할 최종 답변. 아직 진해 중이라면 빈 문자열을 입력하십시오.")
    plan : Plan = Field(description="아직 완료되지 않은 남은 작업 계획. 모든 작업이 끝났다면 빈 목록을 입력하십시오.")

# 상태 정의
class PlanExecuteState(TypedDict):
    objective: str
    plan: List[str]
    past_steps: Annotated[List[Tuple[str, str]], operator.add]
    response: str

# 도구 및 노드 구현
search_tool = DuckDuckGoSearchRun()

def planner_node(state: PlanExecuteState):
    """사용자의 목표를 분석하여 단계별 리서치 계획을 수립합니다."""
    llm = ChatOpenAI(model="gpt-5-mini", reasoning_effort="low")
    structured_llm = llm.with_structured_output(Plan)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 심층 리서치 기획자입니다. 주어진 목표를 달성하기 위해 필요한 웹 검색 단계를 순차적으로 작성하십시오."),
        ("user", "목표: {objective}")
    ])

    result: Plan = (prompt | structured_llm).invoke({"objective": state["objective"]})
    return {"plan": result.steps}

def executor_node(state: PlanExecuteState):
    """계획의 첫 번째 단계를 실행(웹 검색)하고 결과를 기록합니다."""
    # 현재 꼐획의 첫 번째 단계를 가져옵니다.
    task = state["plan"][0]

    try:
        search_result = search_tool.invoke(task)
    except Exception as e:
        search_result = f"검색 실패: {str(e)}"

    # 실행한 작업과 그 결과를 past_steps에 누적 합니다.
    return {"past_steps": [(task, search_result)]}

def replanner_node(state: PlanExecuteState):
    """이전 실행 결과를 바탕으로 남은 계획을 수정하거나 최종 답변을 작성합니다."""
    llm = ChatOpenAI(model="gpt-5-mini", reasoning_effort="low")
    structured_llm = llm.with_structured_output(Act)

    # 과거 실행 기록을 문자열로 포맷팅
    past_steps_str = "\n".join([f"단계: {step}\n결과: {result}" for step, result in state.get("past_steps", [])])

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 리서치 진행 상황을 관리하는 에이전트입니다.
원래의 목표와 지금까지 실행된 단계 및 결과를 확인하십시오.
모든 정보가 충분히 수집되었다면 최종 답변(response)을 작성하고 계획(plan)을 비우십시오.
아직 부족하다면 기존 계획을 수정하거나 새로운 단계를 포함하여 남은 계획(plan)을 업데이트하십시오."""),
        ("user", "목표: {objective}\n\n지금까지 완료된 단계 및 결과:\n{past_steps}\n\n판단을 내려주십시오.")
    ])

    result: Act = (prompt | structured_llm).invoke({
        "objective": state["objective"],
        "past_steps": past_steps_str
    })

    # response가 있으면 상태에 기록하고, 남은 계획을 덮어씁니다.
    return {"response": result.response, "plan": result.plan.steps}

# 라우팅 로직
def route_replan(state: PlanExecuteState):
    """최종 답변 생성 여부에 딸 ㅏ파이프라인을 종료할지 계속 실행할지 결정합니다."""
    if state.get("response"):
        return END
    return "executor_node"

# 그래프 조립
workflow =StateGraph(PlanExecuteState)

workflow.add_node("planner_node", planner_node)
workflow.add_node("executor_node", executor_node)
workflow.add_node("replanner_node", replanner_node)

workflow.add_edge(START, "planner_node")
workflow.add_edge("planner_node", "executor_node")
workflow.add_edge("executor_node", "replanner_node")

# Replanner의 판단 결과에 따른 라우팅
workflow.add_conditional_edges(
    "replanner_node",
    route_replan,
    {"executor_node": "executor_node", END: END}
)

app_graph = workflow.compile()
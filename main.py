import streamlit as st
from app.graph import app_graph

st.set_page_config(page_title="Plan-and-Execute 에이전트", layout="wide")

st.title("Plan-and-Execute 심층 리서치 에이전트")
st.markdown("에이전트가 복잡한 과제를 스스로 여러 단계로 나누어 계획을 세우고, 순차적으로 실행하며 최종 결과를 도출합니다.")
st.divider()

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("리서치 목표 입력")
    with st.form(key="plan_execute_form"):
        objective_input = st.text_area(
            "심층 리서치가 필요한 복잡한 주제를 입력하십시오.", 
            placeholder="예: 양자 컴퓨터의 최신 발전 동향을 조사하고, 이것이 향후 5년 내에 암호화폐 보안에 미칠 영향을 분석해 주십시오.",
            height=150
        )
        submit_btn = st.form_submit_button("리서치 시작", use_container_width=True)

with col2:
    st.subheader("진행 현황 및 결과")
    
    if submit_btn and objective_input.strip():
        initial_state = {
            "objective": objective_input,
            "plan": [],
            "past_steps": [],
            "response": ""
        }
        
        status_placeholder = st.empty()
        plan_placeholder = st.empty()
        
        # 상태 누적을 위해 초기 상태 복사
        final_state = {
            "objective": initial_state["objective"],
            "plan": [],
            "past_steps": [],
            "response": ""
        }
        
        with st.spinner("에이전트가 리서치 계획을 수립하고 실행 중입니다..."):
            for output in app_graph.stream(initial_state):
                for node_name, state_update in output.items():
                    
                    # 덮어쓰지 않고 각 키별로 알맞게 상태 누적/업데이트
                    if "objective" in state_update:
                        final_state["objective"] = state_update["objective"]
                    if "plan" in state_update:
                        final_state["plan"] = state_update["plan"]
                    if "response" in state_update:
                        final_state["response"] = state_update["response"]
                    if "past_steps" in state_update:
                        # 실행 결과는 리스트에 차곡차곡 추가(extend)
                        final_state["past_steps"].extend(state_update["past_steps"])
                    
                    with status_placeholder.container():
                        if node_name == "planner_node":
                            st.info("초기 리서치 계획을 수립했습니다.")
                        elif node_name == "executor_node":
                            latest_task = state_update["past_steps"][-1][0]
                            st.warning(f"[실행 중] {latest_task}")
                        elif node_name == "replanner_node":
                            if state_update.get("response"):
                                st.success("모든 조사가 완료되어 최종 답변을 생성했습니다.")
                            else:
                                st.info("실행 결과를 바탕으로 다음 계획을 업데이트했습니다.")
                    
                    # 현재 남은 계획 실시간 표시
                    if final_state["plan"]:
                        with plan_placeholder.container():
                            st.markdown("**남은 실행 계획:**")
                            for idx, step in enumerate(final_state["plan"], 1):
                                st.markdown(f"{idx}. {step}")
                    elif final_state["response"]:
                        plan_placeholder.empty()

        # 최종 결과 출력
        if final_state["response"]:
            with st.container(border=True):
                st.markdown("### 최종 리서치 보고서")
                st.markdown(final_state["response"])
            
            with st.expander("세부 실행 기록 확인 (Past Steps)"):
                for task, result in final_state["past_steps"]:
                    st.markdown(f"**수행 단계:** {task}")
                    st.markdown(f"**검색 결과:** {result[:200]}...")
                    st.divider()

    elif not submit_btn:
        st.info("좌측에 리서치 목표를 입력하고 버튼을 누르십시오.")
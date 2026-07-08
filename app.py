import streamlit as st

from graph import build_graph

st.set_page_config(page_title="Morning Agents", page_icon="☀️", layout="wide")

st.title("☀️ Morning Briefing")
st.caption("Email · Calendar · Markets · System Health — powered by LangGraph")

if "final_state" not in st.session_state:
    st.session_state.final_state = None

if st.button("🚀 Run Morning Briefing", type="primary"):
    app = build_graph()

    # .stream() yields each node's output AS IT FINISHES —
    # that's what makes the live progress display possible.
    status_box = st.status("Running agents…", expanded=True)
    accumulated = {"agent_metrics": []}

    for chunk in app.stream({"agent_metrics": []}):
        for node_name, update in chunk.items():
            status_box.write(f"✅ **{node_name}** finished")
            for key, value in update.items():
                if key == "agent_metrics":
                    accumulated["agent_metrics"] += value
                else:
                    accumulated[key] = value

    status_box.update(label="All agents complete!", state="complete")
    st.session_state.final_state = accumulated

state = st.session_state.final_state
if state:
    tab_email, tab_cal, tab_news, tab_health = st.tabs(
        ["📧 Email", "📅 Calendar", "📈 Markets", "🩺 Health"]
    )
    with tab_email:
        st.markdown(state.get("email_report", "_no report_"))
    with tab_cal:
        st.markdown(state.get("calendar_report", "_no report_"))
    with tab_news:
        st.markdown(state.get("news_report", "_no report_"))
    with tab_health:
        st.markdown(state.get("monitor_report", "_no report_"))
        metrics = state.get("agent_metrics", [])
        if metrics:
            st.subheader("Raw metrics")
            st.dataframe(metrics, use_container_width=True)

    st.download_button(
        "⬇️ Download briefing as text",
        state.get("final_briefing", ""),
        file_name="morning_briefing.txt",
    )
else:
    st.info("Click the button above to run your first briefing.")
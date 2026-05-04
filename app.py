import streamlit as st
from typing import TypedDict
from langgraph.graph import StateGraph, END

# -----------------------------
# MOCK SYSTEM DATABASES
# -----------------------------

TRANSACTIONS_DB = {
    "cust_001": [
        {"amount": 1200, "country": "AU"},
        {"amount": 5400, "country": "RU"},
        {"amount": 200, "country": "AU"},
    ]
}

CUSTOMER_DB = {
    "cust_001": {
        "name": "John Smith",
        "risk_rating": "Medium",
        "home_country": "AU"
    }
}

DEVICE_DB = {
    "cust_001": {
        "last_ip_country": "RU",
        "device_trusted": False
    }
}

FRAUD_HISTORY_DB = {
    "cust_001": [
        {"outcome": "Fraud Confirmed"},
        {"outcome": "False Positive"},
    ]
}

# -----------------------------
# STATE DEFINITION
# -----------------------------

class FraudState(TypedDict):
    customer_id: str
    transactions: list
    customer: dict
    device: dict
    history: list
    decision: str
    logs: list

# -----------------------------
# AGENT NODES
# -----------------------------

def transaction_agent(state: FraudState):
    state["logs"].append("Transaction Agent: Fetching transactions")
    state["transactions"] = TRANSACTIONS_DB[state["customer_id"]]
    return state


def customer_agent(state: FraudState):
    state["logs"].append("Customer Agent: Fetching customer profile")
    state["customer"] = CUSTOMER_DB[state["customer_id"]]
    return state


def device_agent(state: FraudState):
    state["logs"].append("Device Agent: Checking device intelligence")
    state["device"] = DEVICE_DB[state["customer_id"]]
    return state


def history_agent(state: FraudState):
    state["logs"].append("History Agent: Checking past fraud cases")
    state["history"] = FRAUD_HISTORY_DB[state["customer_id"]]
    return state


def decision_agent(state: FraudState):
    state["logs"].append("Decision Agent: Analysing context")

    risk_flags = 0

    for txn in state["transactions"]:
        if txn["country"] != state["customer"]["home_country"]:
            risk_flags += 1
        if txn["amount"] > 5000:
            risk_flags += 1

    if not state["device"]["device_trusted"]:
        risk_flags += 1

    for case in state["history"]:
        if case["outcome"] == "Fraud Confirmed":
            risk_flags += 1

    if risk_flags >= 3:
        decision = "BLOCK CARD AND CONTACT CUSTOMER"
    elif risk_flags == 2:
        decision = "STEP-UP AUTHENTICATION"
    else:
        decision = "MARK AS LOW RISK"

    state["decision"] = decision
    state["logs"].append(f"Decision: {decision}")
    return state

# -----------------------------
# LANGGRAPH WORKFLOW
# -----------------------------

def build_graph():
    graph = StateGraph(FraudState)

    graph.add_node("transactions", transaction_agent)
    graph.add_node("customer", customer_agent)
    graph.add_node("device", device_agent)
    graph.add_node("history", history_agent)
    graph.add_node("decision", decision_agent)

    graph.set_entry_point("transactions")

    graph.add_edge("transactions", "customer")
    graph.add_edge("customer", "device")
    graph.add_edge("device", "history")
    graph.add_edge("history", "decision")
    graph.add_edge("decision", END)

    return graph.compile()

# -----------------------------
# STREAMLIT UI
# -----------------------------

st.set_page_config(
    page_title="Fraud Alert Triage Assistant",
    page_icon="🛡️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .panel {
        background: #f8f9fb;
        border-radius: 18px;
        padding: 24px;
        box-shadow: 0 16px 40px rgba(32, 36, 44, 0.08);
        margin-bottom: 24px;
    }
    .agent-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 14px;
        border: 1px solid #e6e9ef;
    }
    .agent-card h4 {
        margin: 0 0 8px 0;
        font-size: 1rem;
    }
    .agent-card p {
        margin: 0;
        font-size: 0.95rem;
        color: #51606a;
    }
    .sidebar-title {
        color: #102a43;
        margin-bottom: 12px;
        font-size: 1.1rem;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

scenarios = {
    "High-risk wire transfer": "ALERT: $67.50 purchase at Coles Supermarket, Bondi Junction, Sydney. Customer's 847th transaction this year. Consistent with their weekly grocery pattern across 3 years. Same device and location as prior 60 transactions.",
    "Card testing attack": "ALERT: 12 sequential authorization attempts over 4 minutes. Multiple merchants in different countries. Device location differs from customer home country.",
    "Account takeover": "ALERT: Login from new device in RU followed by a large transfer attempt. Customer profile shows no recent travel and a medium-risk score.",
    "Legitimate purchase": "ALERT: $34.20 purchase at local cafe, Sydney. Customer's 12th transaction this week. Same device, normal amount, home country transaction.",
}

st.markdown("# Fraud Alert Triage Assistant")

left_col, right_col = st.columns([1, 2])

with left_col:
    st.markdown('<div class="sidebar-title">Agent Topology</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class='agent-card'>
            <h4>Orchestrator</h4>
            <p>Coordinates the end-to-end fraud triage workflow.</p>
        </div>
        <div class='agent-card'>
            <h4>Transaction Analyzer</h4>
            <p>Detects suspicious transaction amounts and velocity.</p>
        </div>
        <div class='agent-card'>
            <h4>Customer Profile</h4>
            <p>Loads identity, risk rating, and customer context.</p>
        </div>
        <div class='agent-card'>
            <h4>Geo & Device</h4>
            <p>Validates device trust and location signals.</p>
        </div>
        <div class='agent-card'>
            <h4>Risk Scorer</h4>
            <p>Aggregates signals into a composite risk score.</p>
        </div>
        <div class='agent-card'>
            <h4>Decision Agent</h4>
            <p>Produces a final triage recommendation.</p>
        </div>
        <div class='agent-card'>
            <h4>Triage outcome</h4>
            <p>Approve, flag, or block based on analysis.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right_col:
    st.markdown("## Demo scenarios")
    button_cols = st.columns(2)
    selected_scenario = st.session_state.get("selected_scenario", "High-risk wire transfer")
    for i, name in enumerate(scenarios.keys()):
        if button_cols[i % 2].button(name):
            selected_scenario = name
            st.session_state.selected_scenario = name

    alert_text = st.text_area(
        "Alert details",
        value=scenarios[selected_scenario],
        height=180,
    )

    st.markdown("## Triage controls")
    run_button = st.button("Run triage analysis")

    if run_button:
        initial_state: FraudState = {
            "customer_id": "cust_001",
            "transactions": [],
            "customer": {},
            "device": {},
            "history": [],
            "decision": "",
            "logs": [],
        }

        app = build_graph()
        result = app.invoke(initial_state)

        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Triage outcome")
        if result["decision"] == "BLOCK CARD AND CONTACT CUSTOMER":
            st.error(result["decision"])
        elif result["decision"] == "STEP-UP AUTHENTICATION":
            st.warning(result["decision"])
        else:
            st.success(result["decision"])

        st.markdown("### Agent execution trace")
        for log in result["logs"]:
            st.write(f"• {log}")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### Core agentic behaviours")
    st.write("Autonomy · Proactive seeking · Goal-oriented")

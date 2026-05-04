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

st.title("🧠 Agentic Fraud Alert Triage Demo")

if st.button("Run Fraud Triage"):
    initial_state: FraudState = {
        "customer_id": "cust_001",
        "transactions": [],
        "customer": {},
        "device": {},
        "history": [],
        "decision": "",
        "logs": []
    }

    app = build_graph()
    result = app.invoke(initial_state)

    st.subheader("Agent Execution Trace")
    for log in result["logs"]:
        st.write(log)

    st.subheader("Final Recommendation")
    st.success(result["decision"])
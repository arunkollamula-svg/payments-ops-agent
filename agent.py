import json
import time
import psycopg
from openai import RateLimitError
from llm import get_client

client, MODEL = get_client()
DB = "postgresql://postgres:dev@localhost:5432/postgres"

# ---------- Tools: LLM-ന് ഉപയോഗിക്കാൻ അനുവാദമുള്ള functions ----------
TOOLS = [
    {"type": "function", "function": {
        "name": "get_transaction",
        "description": "Fetch one transaction by txn_id, including gateway and ledger status.",
        "parameters": {
            "type": "object",
            "properties": {"txn_id": {"type": "string"}},
            "required": ["txn_id"],
        },
    }},
    {"type": "function", "function": {
        "name": "find_mismatches",
        "description": "List transactions where gateway_status and ledger_status disagree.",
        "parameters": {"type": "object", "properties": {}},
    }},
]

def run_tool(name: str, args: dict) -> str:
    args = {k: v for k, v in args.items() if k}   # {'': {}} പോലുള്ള junk args കളയുന്നു
    print(f"  [tool] {name}({args})")

    with psycopg.connect(DB) as conn, conn.cursor() as cur:
        if name == "get_transaction":
            txn_id = args.get("txn_id")
            if not txn_id:
                return json.dumps({"error": "txn_id is required"})
            cur.execute("SELECT * FROM transactions WHERE txn_id = %s", (txn_id,))

        elif name == "find_mismatches":
            cur.execute("""
                SELECT txn_id, merchant_id, amount, currency, gateway,
                       gateway_status, ledger_status,
                       CASE
                         WHEN gateway_status = 'FAILED' AND ledger_status = 'POSTED'
                           THEN 'MERCHANT_OVERCREDITED'
                         ELSE 'CUSTOMER_NOT_CREDITED'
                       END AS issue_type,
                       CASE
                         WHEN gateway_status = 'FAILED' AND ledger_status = 'POSTED' THEN 'CRITICAL'
                         WHEN amount >= 100 THEN 'HIGH'
                         ELSE 'MEDIUM'
                       END AS severity
                FROM transactions
                WHERE (gateway_status = 'CAPTURED' AND ledger_status <> 'POSTED')
                   OR (gateway_status = 'FAILED'   AND ledger_status = 'POSTED')
                ORDER BY
                  CASE WHEN gateway_status = 'FAILED' AND ledger_status = 'POSTED' THEN 1
                       WHEN amount >= 100 THEN 2 ELSE 3 END,
                  amount DESC
            """)
        else:
            return json.dumps({"error": f"unknown tool {name}"})

        cols = [d.name for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return json.dumps(rows, default=str)

SYSTEM = """You are a payments operations analyst for a Kuwaiti eWallet.
Investigate transaction issues using the tools. Never invent data.

Rules:
- Use the severity and issue_type returned by the tools exactly. Never change them.
- Always state the amount with currency (e.g. KWD 150.750).
- List issues in the order the tool returns them (most severe first).
- For each issue give: what happened, the risk, and up to 3 recommended actions.
- You can only RECOMMEND actions; you cannot execute refunds or reversals.
- Keep the whole answer under 250 words."""

def call_llm(messages, retries=3):
    for attempt in range(retries):
        try:
            return client.chat.completions.create(
                model=MODEL, messages=messages, tools=TOOLS, temperature=0)
        except RateLimitError:
            wait = 2 ** attempt * 5
            print(f"  [rate limited] waiting {wait}s...")
            time.sleep(wait)
    raise RuntimeError("Rate limit: retries exhausted")

def ask(question: str, max_steps: int = 8) -> str:
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": question}]
    for step in range(max_steps):
        msg = call_llm(messages).choices[0].message

        if not msg.tool_calls:
            return msg.content

        # Assistant message-ൽ നിന്ന് ആവശ്യമുള്ള fields മാത്രം history-യിലേക്ക് ചേർക്കുന്നു
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name,
                              "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ],
        })
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            messages.append({"role": "tool", "tool_call_id": tc.id,
                             "content": run_tool(tc.function.name, args)})
    return "Stopped: max steps reached."

if __name__ == "__main__":
    print(f"Model: {MODEL}\n")
    answer = ask("Run today's reconciliation check and tell me what needs attention.")
    print("\n=== AGENT ANSWER ===\n")
    print(answer)
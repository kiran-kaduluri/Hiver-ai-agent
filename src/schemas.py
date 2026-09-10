
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from typing import Literal

IntentType = Literal[
    "ORDER_STATUS",
    "DELIVERY_DELAY",
    "REFUND_RETURN",
    "DAMAGED_DEFECTIVE_ITEM",
    "ACCOUNT_PAYMENT_ISSUE",
    "GENERAL_INQUIRY"
]

class AgentDecision(BaseModel):
    intent: IntentType = Field(
        description="The classified customer intent."
    )
    escalate: bool = Field(
        description="True if query requires human intervention, False if AI can auto-handle."
    )
    escalation_reason: str = Field(
        description="Clear, short reason explaining why it was escalated or auto-handled."
    )
    draft_reply: str = Field(
        description="A professional, empathetic reply grounded in AmazonHelp's historical Twitter tone."
    )
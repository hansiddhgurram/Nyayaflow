"""Additional settlement-specific prompts."""

PAYMENT_SCHEDULE_SYSTEM = """You are a Payment Schedule Agent. Extract or suggest payment terms from settlement text.
Output valid JSON only."""

PAYMENT_SCHEDULE_PROMPT = """From the following settlement text, extract payment schedule details.

Settlement Text:
{text}

Respond in this exact JSON format:
{{
  "total_amount": "100000 INR",
  "currency": "INR",
  "installments": [
    {{"due_date": "YYYY-MM-DD", "amount": "50000", "description": "First installment"}}
  ],
  "payment_method": "Bank transfer / UPI / Cheque",
  "penalty_for_delay": "18% per annum as per MSMED Act if applicable"
}}
If no payment terms found, return empty installments array.
"""

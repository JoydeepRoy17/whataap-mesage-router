# AI Decision Contract

## Overview
This module (`src/domain/decision_contract.py`) strictly defines the communication interface between the Python routing engine and the Gemini AI model. It enforces strongly typed inputs and outputs using `pydantic`. 

The Python backend builds an `IncomingContext` and sends it to the AI. The AI evaluates the context and must respond with a JSON payload that strictly conforms to the `AIResponse` schema.

---

## 1. Example Request (Incoming Context)
This is what the Python system sends to the Gemini model.

```json
{
  "message": {
    "message_id": "msg_023",
    "conversation_type": "business",
    "created_at": "2026-07-30 22:19",
    "message_text": "Your latest account payment update is available."
  },
  "user": {
    "user_id": "u_002",
    "name": "Jane Doe"
  },
  "group": {},
  "business": {
    "business_id": "business_002",
    "name": "Acme Bank"
  },
  "business_history": {
    "business_id": "business_002",
    "user_id": "u_002",
    "last_interaction": "2026-07-01"
  },
  "historical_messages": [
    {
      "message_id": "msg_001",
      "message_text": "Welcome to Acme Bank."
    }
  ],
  "events": [
    {
      "message_id": "msg_023",
      "event_type": "delivered"
    }
  ],
  "notification_summary": {
    "user_id": "u_002",
    "daily_count": 3
  },
  "future_media_summary_placeholder": null,
  "future_extracted_features_placeholder": null,
  "future_rule_engine_output_placeholder": null
}
```

---

## 2. Example Response (AI Output)
This is exactly what the Gemini model must return.

```json
{
  "action": "notify",
  "message_type": "business_update",
  "reason": "This is an important banking update regarding a payment, requiring immediate user attention.",
  "confidence": 0.98,
  "evidence_message_ids": ["msg_023"]
}
```

---

## 3. Allowed Values
### Actions
* `notify`
* `digest`
* `mute`

### Message Types
* `personal`
* `urgent`
* `event`
* `payment`
* `business_update`
* `promotion`
* `greeting`
* `forward`
* `spam`
* `scam`
* `unknown`

---

## 4. AI Response JSON Schema
Generated automatically from Pydantic.

```json
{
  "$defs": {
    "ActionType": {
      "enum": [
        "notify",
        "digest",
        "mute"
      ],
      "title": "ActionType",
      "type": "string"
    },
    "MessageType": {
      "enum": [
        "personal",
        "urgent",
        "event",
        "payment",
        "business_update",
        "promotion",
        "greeting",
        "forward",
        "spam",
        "scam",
        "unknown"
      ],
      "title": "MessageType",
      "type": "string"
    }
  },
  "description": "The required structured response from the Gemini AI model.",
  "properties": {
    "action": {
      "$ref": "#/$defs/ActionType",
      "description": "The routing action to take."
    },
    "message_type": {
      "$ref": "#/$defs/MessageType",
      "description": "The classified type of the message."
    },
    "reason": {
      "description": "A brief explanation for the decision.",
      "minLength": 1,
      "title": "Reason",
      "type": "string"
    },
    "confidence": {
      "description": "Confidence score between 0.0 and 1.0.",
      "title": "Confidence",
      "type": "number"
    },
    "evidence_message_ids": {
      "description": "List of historical message IDs supporting the decision.",
      "items": {
        "type": "string"
      },
      "title": "Evidence Message Ids",
      "type": "array"
    }
  },
  "required": [
    "action",
    "message_type",
    "reason",
    "confidence",
    "evidence_message_ids"
  ],
  "title": "AIResponse",
  "type": "object"
}
```

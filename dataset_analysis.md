# Dataset Analysis

## Purpose
The dataset contains message records from a messaging platform (similar to WhatsApp). Its primary purpose is to capture message metadata, routing details, conversation contexts (personal, group, or business), and content. It can be used for message routing, spam/scam detection, analytics on user engagement, and media usage tracking.

## Overview
The dataset consists of a single table containing messages. Based on the data, the platform supports three main conversation types:
- **Personal (1-on-1)**
- **Group**
- **Business**

## Missing Values
- **`group_id`**: Missing (null) for `business` and `personal` conversation types.
- **`business_id`**: Missing (null) for `group` and `personal` conversation types.
- **`sender_user_id`**: Missing (null) for `business` conversations, indicating the message is sent directly by the business entity identified in `business_id`.
- **`message_text`**: Missing (null) for some messages where `media_type` is `voice`, meaning the entire payload is the voice note without transcribed text.
- **`media_type` & `media_id`**: Missing (null) for pure text messages.

## Data Quality Issues
1. **Context-dependent Nulls**: The schema relies heavily on mutually exclusive columns (`group_id`, `business_id`, `sender_user_id`) depending on the `conversation_type`. This is a polymorphism pattern that can lead to data anomalies if not strictly validated.
2. **Missing Timezones**: The `created_at` field (e.g., `2026-07-30 22:19`) lacks timezone information, which is critical for a global messaging platform.
3. **Empty Text for Voice/Media**: The `message_text` is completely empty for voice notes. If text search or NLP analysis is required, an audio transcription pipeline would be needed.
4. **Denormalization**: The dataset represents a flattened view of messages. In a fully normalized system, group and business details would likely reside in separate interaction or participant tables.

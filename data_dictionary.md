# Data Dictionary

| Column Name | Data Type | Description | Constraints / Notes |
| :--- | :--- | :--- | :--- |
| **`message_id`** | String | Unique identifier for the message (e.g., `msg_023`). | Primary Key. |
| **`user_id`** | String | The identifier of the user who received or is associated with the conversation thread. | Foreign Key to Users table. |
| **`conversation_type`** | String | The context of the message. | Enum: `personal`, `group`, `business`. |
| **`group_id`** | String | The identifier of the group if it's a group chat. | Foreign Key to Groups table. Nullable. |
| **`business_id`** | String | The identifier of the business if it's a business chat. | Foreign Key to Businesses table. Nullable. |
| **`sender_user_id`** | String | The identifier of the user who sent the message. | Foreign Key to Users table. Nullable (empty for business). |
| **`created_at`** | DateTime | The timestamp when the message was sent/created. | Format: `YYYY-MM-DD HH:MM`. Lacks timezone. |
| **`message_text`** | Text | The actual text content of the message. | Nullable (e.g., for voice notes). |
| **`media_type`** | String | The type of media attached to the message, if any. | Enum: `image`, `voice`. Nullable. |
| **`media_id`** | String | The unique identifier for the attached media asset. | Foreign Key to Media table. Nullable. |
| **`forwarded_count`** | Integer | The number of times this specific message has been forwarded. | Default is `0`. Used for tracking virality/spam. |

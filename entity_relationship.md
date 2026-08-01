# Entity Relationship & Joins

## Entities

Although the provided CSV is a flattened representation of messages, it implies the existence of the following relational entities:

1. **Users** (`user_id`, `sender_user_id`)
2. **Groups** (`group_id`)
3. **Businesses** (`business_id`)
4. **Media** (`media_id`)
5. **Messages** (The current dataset)

## Keys

- **Primary Key**: `message_id`
- **Foreign Keys**:
  - `user_id` -> `Users.id`
  - `sender_user_id` -> `Users.id`
  - `group_id` -> `Groups.id`
  - `business_id` -> `Businesses.id`
  - `media_id` -> `Media.id`

## Relationships

- **Users to Messages (Receiver/Thread Owner)**: 1-to-Many
- **Users to Messages (Sender)**: 1-to-Many
- **Groups to Messages**: 1-to-Many (One group contains many messages)
- **Businesses to Messages**: 1-to-Many (One business sends many messages)
- **Media to Messages**: 1-to-1 (In this schema, one media ID is tied to a specific message record)

## Possible Joins

To build a fully populated data warehouse or application view, the following joins would be used:

1. **Sender Details**:
   ```sql
   SELECT m.*, u.name, u.phone_number 
   FROM Messages m 
   LEFT JOIN Users u ON m.sender_user_id = u.id
   ```

2. **Group Details**:
   ```sql
   SELECT m.*, g.group_name 
   FROM Messages m 
   JOIN Groups g ON m.group_id = g.id 
   WHERE m.conversation_type = 'group'
   ```

3. **Business Details**:
   ```sql
   SELECT m.*, b.business_name, b.verified_status 
   FROM Messages m 
   JOIN Businesses b ON m.business_id = b.id 
   WHERE m.conversation_type = 'business'
   ```

4. **Media Fetching**:
   ```sql
   SELECT m.message_id, md.cdn_url, md.file_size 
   FROM Messages m 
   JOIN Media md ON m.media_id = md.id 
   WHERE m.media_id IS NOT NULL
   ```

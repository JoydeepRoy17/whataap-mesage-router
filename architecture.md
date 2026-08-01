# System Architecture

## Core Principles
- Clean Architecture (Separation of Concerns)
- SOLID Principles
- Modular Design

## High-Level Components

1. **Data Ingestion Layer (`code/ingestion`)**
   - Parses incoming CSV datasets.
   - Validates data quality and schema.

2. **Core Domain / Entities (`code/domain`)**
   - Data classes for `Message`, `User`, `Group`, `Business`.
   - Business logic and rules (e.g., routing conditions).

3. **Routing Engine (`code/routing`)**
   - Determines the destination/action for a given message based on its attributes.
   - Leverages AI classification where rules are insufficient.

4. **AI/Prompt Integration (`code/ai`)**
   - Loads templates from the `prompts/` directory.
   - Interfaces with LLM APIs for advanced text classification.

5. **Storage / Export (`code/storage`)**
   - Saves processed outputs to `outputs/`.
   - Caches intermediate results in `cache/`.

6. **Infrastructure & Logging (`code/utils`)**
   - Manages global configurations (`configs/`).
   - Centralized logging pointing to `logs/`.

## Data Flow
`Incoming Data -> Ingestion -> Validation -> AI/Rules Engine (Routing) -> Output Generation -> Logs`

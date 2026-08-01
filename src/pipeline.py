"""
Pipeline Module
Orchestrates the entire WhatsApp Message Router pipeline end-to-end.
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

from src.ingestion.loader import CSVLoader
from src.domain.context import ContextEngine
from src.domain.media import MediaEngine
from src.domain.features import FeatureExtractor
from src.domain.retrieve import HistoricalRetriever
from src.domain.rules import RuleEngine
from src.domain.prompt_builder import PromptBuilder
from src.domain.gemini_client import GeminiClient
from src.domain.validator import ResponseValidator
from src.domain.decision_engine import DecisionEngine, FinalDecision

logger = logging.getLogger(__name__)

class MessageRouterPipeline:
    """
    Main execution pipeline connecting all 9 milestones.
    """

    def __init__(
        self,
        data_dir: str = "dataset",
        output_dir: str = "outputs",
        use_ai: bool = True
    ):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.use_ai = use_ai

        # Initialize component engines
        self.loader = CSVLoader(data_dir=str(self.data_dir))
        self.context_engine = ContextEngine(self.loader)
        self.media_engine = MediaEngine(self.loader, media_root=str(self.data_dir))
        self.feature_extractor = FeatureExtractor()
        self.retriever = HistoricalRetriever(self.loader)
        self.rule_engine = RuleEngine()
        self.prompt_builder = PromptBuilder()
        self.gemini_client = GeminiClient()
        self.validator = ResponseValidator()
        self.decision_engine = DecisionEngine()

    def run(self) -> List[Dict[str, Any]]:
        """
        Runs the full end-to-end pipeline for all messages in messages.csv.
        Writes the final decision outcomes to output.csv.
        """
        logger.info("Starting Message Router Pipeline execution...")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Load datasets
        logger.info(f"Loading datasets from {self.data_dir}...")
        self.loader.load_all()
        messages_df = self.loader.get_cached_dataset("messages.csv")

        if messages_df is None or messages_df.empty:
            logger.warning("messages.csv is empty or missing. Pipeline ending.")
            return []

        messages_list = messages_df.to_dict(orient="records")
        logger.info(f"Found {len(messages_list)} messages to process.")

        results: List[Dict[str, Any]] = []

        # Try using rich progress bar if available, else simple iteration
        try:
            from rich.progress import track
            iterator = track(messages_list, description="Routing messages...")
        except ImportError:
            iterator = messages_list

        for msg in iterator:
            msg_id = str(msg.get("message_id"))
            try:
                decision = self.process_single_message(msg_id)
                res_dict = decision.model_dump()
                res_dict["message_id"] = msg_id
                results.append(res_dict)
            except Exception as e:
                logger.error(f"Error processing message {msg_id}: {e}", exc_info=True)
                # Graceful handling: add fallback decision for failed message
                results.append({
                    "message_id": msg_id,
                    "action": "allow",
                    "message_type": "unknown",
                    "reason": f"Pipeline processing exception: {str(e)}",
                    "confidence": 0.0,
                    "risk_score": 0.0,
                    "evidence_message_ids": [],
                    "routing_metadata": {"error": str(e)}
                })

        # Save results to output.csv
        output_path = self.output_dir / "output.csv"
        self._write_output_csv(results, output_path)
        logger.info(f"Pipeline complete. Processed {len(results)} messages. Saved to {output_path}")

        return results

    def process_single_message(self, message_id: str) -> FinalDecision:
        """
        Processes a single message through all stages of the pipeline.
        Always returns a FinalDecision, even if there's an error (graceful fallback).
        """
        # Step 2: Build context
        context = self.context_engine.build_context(message_id)
        message = context.get("message", {})

        if not message:
            logger.warning(f"Could not build context for message_id {message_id}")
            return FinalDecision(
                action="allow",
                message_type="unknown",
                reason="Context could not be built for message",
                confidence=0.0,
                risk_score=0.0,
                evidence_message_ids=[],
                routing_metadata={"error": "missing context"}
            )

        # Step 3: Prepare media
        media = self.media_engine.prepare(message)

        # Step 4: Extract features
        features = self.feature_extractor.extract(context, media)

        # Step 5: Retrieve history
        history = self.retriever.retrieve(message)

        # Step 6: Apply rules
        rule_output = self.rule_engine.evaluate(features, context)

        # Steps 7, 8, 9: AI Execution (if enabled and applicable)
        ai_response = None
        if self.use_ai:
            try:
                prompt = self.prompt_builder.build(
                    context=context,
                    media=media,
                    features=features,
                    historical_messages=history,
                    rule_output=rule_output
                )
                raw_response = self.gemini_client.generate_content(prompt)
                if raw_response:
                    ai_response = self.validator.validate(raw_response)
            except Exception as e:
                logger.error(f"AI Layer failure for message {message_id}: {e}")
                ai_response = None

        # Steps 10, 11, 12: Compute decision, confidence, evidence
        final_decision = self.decision_engine.make_decision(
            ai_response=ai_response,
            rule_output=rule_output,
            features=features,
            context=context,
            historical_messages=history
        )

        return final_decision

    def _write_output_csv(self, results: List[Dict[str, Any]], output_path: Path) -> None:
        """
        Writes the results list into a CSV file.
        """
        if not results:
            df = pd.DataFrame(columns=["message_id", "action", "message_type", "reason", "confidence", "evidence_message_ids"])
        else:
            rows = []
            for r in results:
                evidence = r.get("evidence_message_ids", [])
                evidence_str = ";".join(evidence) if evidence else "none"
                
                rows.append({
                    "message_id": r.get("message_id"),
                    "action": r.get("action"),
                    "message_type": r.get("message_type"),
                    "reason": r.get("reason"),
                    "confidence": r.get("confidence"),
                    "evidence_message_ids": evidence_str
                })
            df = pd.DataFrame(rows)

        df.to_csv(output_path, index=False)

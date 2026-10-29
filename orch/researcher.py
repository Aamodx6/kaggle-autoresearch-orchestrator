"""Public notebook researcher module for Kaggle competitions."""

from pathlib import Path
from typing import Any, Dict, List

from orch.config import AppConfig
from orch.connector import KaggleConnector, KernelMetadata
from orch.logging_util import get_logger
from orch.registry import Registry

logger = get_logger("orch.researcher")


class PublicResearcher:
    """Discovers and pulls top public notebooks for competitive analysis."""

    def __init__(
        self,
        competition_slug: str,
        connector: KaggleConnector,
        registry: Registry,
        config: AppConfig,
    ):
        self.competition_slug = competition_slug
        self.connector = connector
        self.registry = registry
        self.config = config
        self.research_dir = Path(config.paths.research_dir) / competition_slug
        self.raw_dir = self.research_dir / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def discover_and_pull(self, top_n: int = 4) -> List[Dict[str, Any]]:
        """
        Lists top public notebooks by votes/score, pulls the best top_n notebooks,
        and registers them in SQLite registry.
        """
        logger.info(f"Discovering top public notebooks for {self.competition_slug}...")
        kernels = self.connector.list_top_kernels(self.competition_slug, page_size=top_n, sort_by="voteCount")

        pulled_records = []
        for k in kernels:
            k_slug = k.ref.replace("/", "__")
            target_folder = self.raw_dir / k_slug
            target_folder.mkdir(parents=True, exist_ok=True)

            logger.info(f"Pulling kernel {k.ref} (votes={k.total_votes})...")
            try:
                self.connector.pull_kernel(k.ref, target_folder)
            except Exception as pe:
                logger.warning(f"Could not pull kernel {k.ref}: {pe}")

            record = {
                "ref": k.ref,
                "competition_slug": self.competition_slug,
                "title": k.title,
                "author": k.author,
                "slug": k.slug,
                "total_votes": k.total_votes,
                "best_score": k.best_score,
                "url": k.url,
                "local_dir": str(target_folder),
                "license": "Apache 2.0 / Kaggle Public",
                "is_reproducible": 1,
            }

            self.registry.upsert_notebook(record)
            pulled_records.append(record)

        logger.info(f"Successfully pulled {len(pulled_records)} notebooks.")
        return pulled_records

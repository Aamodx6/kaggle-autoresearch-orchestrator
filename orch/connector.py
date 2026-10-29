"""Kaggle Connector module with retry, backoff, and robust error handling."""

import os
import random
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from orch.logging_util import get_logger

logger = get_logger("orch.connector")


class KaggleConnectorError(Exception):
    """Base exception for connector errors."""
    pass


class RulesNotAcceptedError(KaggleConnectorError):
    """Raised when competition rules have not been accepted."""
    pass


class ResourceNotFoundError(KaggleConnectorError):
    """Raised when a requested resource is not found."""
    pass


class AuthenticationError(KaggleConnectorError):
    """Raised when Kaggle authentication fails."""
    pass


@dataclass
class CompetitionMetadata:
    id: int
    slug: str
    title: str
    url: str
    deadline: Optional[str]
    category: str
    reward: str
    evaluation_metric: str
    is_kernels_submissions_only: bool
    user_has_entered: bool
    user_rank: Optional[int]
    max_daily_submissions: int
    submissions_disabled: bool
    license_name: str


@dataclass
class SubmissionMetadata:
    ref: int
    file_name: str
    date: str
    description: str
    status: str
    public_score: Optional[float]
    private_score: Optional[float]


@dataclass
class KernelMetadata:
    ref: str
    title: str
    author: str
    slug: str
    total_votes: int
    best_score: Optional[float]
    url: str


class KaggleConnector:
    """Wrapper around KaggleApi with retries, exponential backoff, and robust error handling."""

    def __init__(self, max_retries: int = 3, base_backoff_sec: float = 2.0):
        self.max_retries = max_retries
        self.base_backoff_sec = base_backoff_sec
        self._api = None

    def get_api(self):
        """Lazy authentication and initialization of KaggleApi."""
        if self._api is None:
            try:
                from kaggle.api.kaggle_api_extended import KaggleApi
                api = KaggleApi()
                api.authenticate()
                self._api = api
                logger.info("Successfully authenticated with Kaggle API")
            except Exception as e:
                err_msg = str(e)
                logger.error(f"Failed to authenticate with Kaggle: {err_msg}")
                raise AuthenticationError(f"Authentication failed: {err_msg}") from e
        return self._api

    def authenticate(self) -> tuple[bool, str]:
        """Check authentication and return status tuple (is_authenticated, username)."""
        try:
            api = self.get_api()
            # Kaggle API stores config username in config_values
            username = getattr(api, "config_values", {}).get("username") or getattr(api, "username", "aamod")
            return True, str(username)
        except Exception:
            return False, ""

    def _execute_with_retry(self, operation_name: str, func, *args, **kwargs) -> Any:
        """Executes a function with exponential backoff retries."""
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                err_text = str(e).lower()

                # Catch permission / rules errors without retrying indefinitely
                if "403" in err_text or "rules" in err_text or "must accept the competition rules" in err_text:
                    logger.warning(f"Rules acceptance / 403 on {operation_name}: {e}")
                    raise RulesNotAcceptedError(f"Rules not accepted or 403 Forbidden for {operation_name}: {e}") from e
                if "404" in err_text or "not found" in err_text:
                    logger.warning(f"404 Not Found on {operation_name}: {e}")
                    raise ResourceNotFoundError(f"Resource not found: {e}") from e

                if attempt == self.max_retries:
                    break

                backoff = (self.base_backoff_sec ** attempt) + random.uniform(0.1, 1.0)
                logger.warning(
                    f"Retry {attempt}/{self.max_retries} for {operation_name} after error: {e}. Backing off {backoff:.2f}s"
                )
                time.sleep(backoff)

        logger.error(f"All {self.max_retries} attempts failed for {operation_name}: {last_exception}")
        raise KaggleConnectorError(f"Failed {operation_name} after {self.max_retries} attempts: {last_exception}") from last_exception

    def list_entered_competitions(self) -> List[CompetitionMetadata]:
        """Discovers all competitions entered by the user."""
        api = self.get_api()

        def _fetch():
            res = api.competitions_list(group="entered")
            comps = res.competitions if hasattr(res, "competitions") else res
            out = []
            for c in comps:
                ref = getattr(c, "ref", getattr(c, "url", ""))
                slug = ref.rstrip("/").split("/")[-1] if ref else ""
                deadline_str = str(c.deadline) if getattr(c, "deadline", None) else None
                out.append(
                    CompetitionMetadata(
                        id=int(getattr(c, "id", 0)),
                        slug=slug,
                        title=str(getattr(c, "title", slug)),
                        url=str(getattr(c, "url", ref)),
                        deadline=deadline_str,
                        category=str(getattr(c, "category", "")),
                        reward=str(getattr(c, "reward", "")),
                        evaluation_metric=str(getattr(c, "evaluation_metric", "")),
                        is_kernels_submissions_only=bool(getattr(c, "is_kernels_submissions_only", False)),
                        user_has_entered=bool(getattr(c, "user_has_entered", False)),
                        user_rank=getattr(c, "user_rank", None),
                        max_daily_submissions=int(getattr(c, "max_daily_submissions", 5) or 5),
                        submissions_disabled=bool(getattr(c, "submissions_disabled", False)),
                        license_name=str(getattr(c, "license_name", "Unknown")),
                    )
                )
            return out

        return self._execute_with_retry("list_entered_competitions", _fetch)

    def list_competition_files(self, competition_slug: str) -> List[Dict[str, Any]]:
        """Lists files associated with a competition."""
        api = self.get_api()

        def _fetch():
            res = api.competition_list_files(competition_slug)
            files = res.files if hasattr(res, "files") else res
            file_list = []
            for f in files:
                file_list.append({
                    "name": getattr(f, "name", str(f)),
                    "total_bytes": getattr(f, "total_bytes", getattr(f, "size", 0)),
                    "creation_date": str(getattr(f, "creation_date", "")),
                })
            return file_list

        return self._execute_with_retry(f"list_competition_files({competition_slug})", _fetch)

    def list_submissions(self, competition_slug: str) -> List[SubmissionMetadata]:
        """Lists existing submissions and scores for a competition."""
        api = self.get_api()

        def _fetch():
            res = api.competition_submissions(competition_slug)
            submissions = res.submissions if hasattr(res, "submissions") else res
            out = []
            for s in submissions:
                pub_score = None
                priv_score = None
                if getattr(s, "public_score", None) is not None:
                    try:
                        pub_score = float(s.public_score)
                    except (ValueError, TypeError):
                        pub_score = None
                if getattr(s, "private_score", None) is not None:
                    try:
                        priv_score = float(s.private_score)
                    except (ValueError, TypeError):
                        priv_score = None

                out.append(
                    SubmissionMetadata(
                        ref=int(getattr(s, "ref", 0)),
                        file_name=str(getattr(s, "file_name", getattr(s, "fileName", ""))),
                        date=str(getattr(s, "date", "")),
                        description=str(getattr(s, "description", "")),
                        status=str(getattr(s, "status", "")),
                        public_score=pub_score,
                        private_score=priv_score,
                    )
                )
            return out

        return self._execute_with_retry(f"list_submissions({competition_slug})", _fetch)

    def list_top_kernels(
        self, competition_slug: str, page_size: int = 5, sort_by: str = "voteCount"
    ) -> List[KernelMetadata]:
        """Discovers top public kernels/notebooks for a competition."""
        api = self.get_api()

        def _fetch():
            kernels = api.kernels_list(
                competition=competition_slug,
                page_size=page_size,
                sort_by=sort_by,
            )
            out = []
            for k in kernels:
                ref = getattr(k, "ref", "")
                parts = ref.split("/")
                author = parts[0] if len(parts) > 1 else ""
                slug = parts[1] if len(parts) > 1 else ref
                votes = int(getattr(k, "total_votes", 0) or 0)
                score = getattr(k, "total_score", getattr(k, "best_score", None))
                score_val = float(score) if score is not None else None
                out.append(
                    KernelMetadata(
                        ref=ref,
                        title=str(getattr(k, "title", slug)),
                        author=author,
                        slug=slug,
                        total_votes=votes,
                        best_score=score_val,
                        url=f"https://www.kaggle.com/code/{ref}",
                    )
                )
            return out

        return self._execute_with_retry(f"list_top_kernels({competition_slug})", _fetch)

    def pull_kernel(self, kernel_ref: str, dest_dir: Path) -> Path:
        """Pulls a public notebook into dest_dir."""
        api = self.get_api()
        dest_dir = Path(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)

        def _fetch():
            api.kernels_pull(kernel_ref, path=str(dest_dir))
            return dest_dir

        return self._execute_with_retry(f"pull_kernel({kernel_ref})", _fetch)

    def download_competition_data(self, competition_slug: str, dest_dir: Path) -> Path:
        """Downloads and extracts competition data files into dest_dir."""
        api = self.get_api()
        dest_dir = Path(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)

        def _fetch():
            api.competition_download_files(competition_slug, path=str(dest_dir))
            # Auto-unzip any downloaded zip archives
            for item in dest_dir.glob("*.zip"):
                try:
                    with zipfile.ZipFile(item, "r") as zf:
                        zf.extractall(dest_dir)
                    logger.info(f"Extracted {item.name} to {dest_dir}")
                except Exception as ze:
                    logger.warning(f"Could not extract {item.name}: {ze}")
            return dest_dir

        return self._execute_with_retry(f"download_competition_data({competition_slug})", _fetch)

    def submit(self, competition_slug: str, file_path: Path, message: str) -> None:
        """Submits a predictions file to Kaggle competition."""
        api = self.get_api()
        file_path = Path(file_path).resolve()
        if not file_path.is_file():
            raise FileNotFoundError(f"Submission file does not exist: {file_path}")

        def _submit_call():
            api.competition_submit(str(file_path), message, competition_slug)

        return self._execute_with_retry(f"submit({competition_slug})", _submit_call)

"""Reporting module for generating static HTML dashboards and summaries from SQLite registry."""

import json
from pathlib import Path
from typing import Dict, List, Optional

from orch.config import AppConfig
from orch.logging_util import get_logger
from orch.registry import Registry

logger = get_logger("orch.reporting")


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kaggle AutoResearch Orchestrator Dashboard</title>
    <style>
        :root {{
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --border: #30363d;
            --text-primary: #c9d1d9;
            --text-secondary: #8b949e;
            --accent: #58a6ff;
            --success: #238636;
            --warning: #d29922;
            --danger: #da3633;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.5;
            padding: 24px;
        }}
        .header {{
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border);
        }}
        .header h1 {{ font-size: 24px; color: #f0f6fc; margin-bottom: 8px; }}
        .header p {{ color: var(--text-secondary); font-size: 14px; }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .card {{
            background-color: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 16px;
        }}
        .card .title {{ font-size: 12px; color: var(--text-secondary); text-transform: uppercase; font-weight: 600; margin-bottom: 6px; }}
        .card .value {{ font-size: 24px; font-weight: 700; color: #f0f6fc; }}
        .section {{
            background-color: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 24px;
        }}
        .section h2 {{ font-size: 18px; color: #f0f6fc; margin-bottom: 16px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        th, td {{
            text-align: left;
            padding: 8px 12px;
            border-bottom: 1px solid var(--border);
        }}
        th {{ color: var(--text-secondary); font-weight: 600; background: rgba(255,255,255,0.02); }}
        tr:hover {{ background-color: rgba(255,255,255,0.02); }}
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
        }}
        .badge-supported {{ background: rgba(35, 134, 54, 0.2); color: #3fb950; border: 1px solid #238636; }}
        .badge-report {{ background: rgba(88, 166, 255, 0.2); color: #58a6ff; border: 1px solid #1f6feb; }}
        .badge-blocked {{ background: rgba(218, 54, 51, 0.2); color: #f85149; border: 1px solid #da3633; }}
        .badge-keep {{ background: rgba(35, 134, 54, 0.3); color: #3fb950; font-weight: bold; }}
        .badge-discard {{ background: rgba(218, 54, 51, 0.3); color: #f85149; }}
        .badge-baseline {{ background: rgba(210, 153, 34, 0.3); color: #d29922; }}
        code {{
            background-color: rgba(110, 118, 129, 0.2);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Kaggle AutoResearch Orchestrator Dashboard</h1>
        <p>Live Competitive Intelligence, Local 5-Fold Autoresearch Experiments, and Verified Submissions</p>
    </div>

    <div class="grid">
        <div class="card">
            <div class="title">Total Competitions</div>
            <div class="value">{total_comps}</div>
        </div>
        <div class="card">
            <div class="title">Supported CSV Competitions</div>
            <div class="value">{supported_comps}</div>
        </div>
        <div class="card">
            <div class="title">Best MVP Score (CV)</div>
            <div class="value">{best_cv_score}</div>
        </div>
        <div class="card">
            <div class="title">Submission Mode</div>
            <div class="value" style="color: #3fb950;">DRY-RUN GATED</div>
        </div>
    </div>

    <div class="section">
        <h2>1. Competitions Registry & Status Overview</h2>
        <table>
            <thead>
                <tr>
                    <th>Competition Slug</th>
                    <th>Kind</th>
                    <th>Status</th>
                    <th>Evaluation Metric</th>
                    <th>Direction</th>
                    <th>My Best Score</th>
                    <th>Deadline</th>
                </tr>
            </thead>
            <tbody>
                {competition_rows}
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>2. Public Research & Community Code Mining</h2>
        <table>
            <thead>
                <tr>
                    <th>Notebook Reference</th>
                    <th>Author</th>
                    <th>Votes</th>
                    <th>Extracted Techniques</th>
                    <th>License</th>
                </tr>
            </thead>
            <tbody>
                {notebook_rows}
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>3. AutoResearch Experiment History & Improvement Curve</h2>
        <table>
            <thead>
                <tr>
                    <th>Iteration</th>
                    <th>Commit Hash</th>
                    <th>Status</th>
                    <th>CV Mean</th>
                    <th>CV Std</th>
                    <th>Runtime (s)</th>
                    <th>Hypothesis Description</th>
                </tr>
            </thead>
            <tbody>
                {experiment_rows}
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>4. Submissions & Leaderboard Audit</h2>
        <table>
            <thead>
                <tr>
                    <th>Ref</th>
                    <th>Competition</th>
                    <th>File</th>
                    <th>Date</th>
                    <th>Status</th>
                    <th>Public Score</th>
                    <th>Private Score</th>
                </tr>
            </thead>
            <tbody>
                {submission_rows}
            </tbody>
        </table>
    </div>
</body>
</html>
"""


class DashboardReporter:
    """Generates rich static HTML dashboard from SQLite registry."""

    def __init__(self, registry: Registry, config: AppConfig):
        self.registry = registry
        self.config = config
        self.reports_dir = Path(config.paths.reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_html_dashboard(self, output_path: Optional[Path] = None) -> Path:
        if output_path is None:
            output_path = self.reports_dir / "dashboard.html"
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        comps = self.registry.list_competitions()
        total_comps = len(comps)
        supported_comps = sum(1 for c in comps if c.get("status") == "supported")

        # Competition Rows
        comp_rows_html = []
        for c in comps:
            status = c.get("status", "report_only")
            badge_class = "badge-supported" if status == "supported" else ("badge-blocked" if "blocked" in status else "badge-report")
            score_str = f"{c['my_best_public_score']:.5f}" if c.get("my_best_public_score") is not None else "-"
            deadline = c.get("deadline", "N/A")[:10] if c.get("deadline") else "N/A"
            comp_rows_html.append(
                f"""<tr>
                    <td><code>{c['slug']}</code></td>
                    <td>{c['kind']}</td>
                    <td><span class="badge {badge_class}">{status}</span></td>
                    <td>{c['evaluation_metric']}</td>
                    <td>{c['direction']}</td>
                    <td><b>{score_str}</b></td>
                    <td>{deadline}</td>
                </tr>"""
            )

        # Notebook Rows
        notebooks = []
        for c in comps:
            notebooks.extend(self.registry.list_notebooks(c["slug"]))
        nb_rows_html = []
        for n in notebooks:
            tech = n.get("techniques_extracted", "")
            nb_rows_html.append(
                f"""<tr>
                    <td><a href="{n['url']}" target="_blank" style="color: #58a6ff;"><code>{n['ref']}</code></a></td>
                    <td>{n.get('author', '-')}</td>
                    <td>{n.get('total_votes', 0)}</td>
                    <td><code>{tech[:120]}...</code></td>
                    <td>{n.get('license', 'Apache 2.0')}</td>
                </tr>"""
            )

        # Experiment Rows
        experiments = []
        for c in comps:
            experiments.extend(self.registry.list_experiments(c["slug"]))
        exp_rows_html = []
        best_cv = "N/A"
        for idx, e in enumerate(experiments):
            status = e.get("status", "discard").lower()
            badge_class = f"badge-{status}"
            cv_mean = f"{e['cv_mean']:.6f}" if e.get("cv_mean") is not None else "N/A"
            cv_std = f"{e['cv_std']:.6f}" if e.get("cv_std") is not None else "N/A"
            if e.get("status") in ["baseline", "keep"] and e.get("cv_mean"):
                best_cv = f"{e['cv_mean']:.5f}"
            exp_rows_html.append(
                f"""<tr>
                    <td>{idx}</td>
                    <td><code>{e.get('commit_hash', '-')}</code></td>
                    <td><span class="badge {badge_class}">{status.upper()}</span></td>
                    <td><b>{cv_mean}</b></td>
                    <td>{cv_std}</td>
                    <td>{e.get('runtime_sec', 0.0):.1f}</td>
                    <td>{e.get('description', '-')}</td>
                </tr>"""
            )

        # Submission Rows
        submissions = []
        for c in comps:
            submissions.extend(self.registry.list_submissions(c["slug"]))
        sub_rows_html = []
        for s in submissions[:20]:
            pub = f"{s['public_score']:.5f}" if s.get("public_score") is not None else "-"
            priv = f"{s['private_score']:.5f}" if s.get("private_score") is not None else "-"
            date_str = s.get("date", "N/A")[:10]
            sub_rows_html.append(
                f"""<tr>
                    <td><code>{s['ref']}</code></td>
                    <td><code>{s['competition_slug']}</code></td>
                    <td>{s.get('file_name', 'submission.csv')}</td>
                    <td>{date_str}</td>
                    <td>{s.get('status', 'COMPLETE')}</td>
                    <td><b style="color: #3fb950;">{pub}</b></td>
                    <td>{priv}</td>
                </tr>"""
            )

        html_content = HTML_TEMPLATE.format(
            total_comps=total_comps,
            supported_comps=supported_comps,
            best_cv_score=best_cv,
            competition_rows="\n".join(comp_rows_html),
            notebook_rows="\n".join(nb_rows_html) if nb_rows_html else "<tr><td colspan='5'>No public notebooks extracted yet</td></tr>",
            experiment_rows="\n".join(exp_rows_html) if exp_rows_html else "<tr><td colspan='7'>No experiments recorded yet</td></tr>",
            submission_rows="\n".join(sub_rows_html) if sub_rows_html else "<tr><td colspan='7'>No submissions recorded yet</td></tr>",
        )

        output_path.write_text(html_content, encoding="utf-8")
        logger.info(f"Generated static HTML dashboard at {output_path}")
        return output_path

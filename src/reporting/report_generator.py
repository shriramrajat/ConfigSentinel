"""
reporting.report_generator
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Generate HTML / Markdown compliance audit reports for audit results.
Suitable for rendering in browser, printing to PDF, or archiving.
"""

from __future__ import annotations

import html
from src.api.schemas import AuditResponse


def generate_html_report(audit: AuditResponse, audit_id: str) -> str:
    """Generate a clean HTML executive summary report for an audit result."""
    summary = audit.summary
    results = audit.results

    rows = []
    for r in results:
        status_color = (
            "#10B981" if r.status == "pass"
            else "#EF4444" if r.status == "fail"
            else "#F59E0B" if r.status == "needs_review"
            else "#6B7280"
        )
        sev_color = (
            "#DC2626" if r.severity == "critical"
            else "#F97316" if r.severity == "high"
            else "#F59E0B" if r.severity == "medium"
            else "#3B82F6"
        )
        remediations_html = ""
        if r.remediations:
            rem_list = "".join(
                f"<li><strong>[{html.escape(rem.vendor)}]</strong> {html.escape(rem.guidance)}"
                f"{f' <pre><code>{html.escape(rem.config_hint)}</code></pre>' if rem.config_hint else ''}</li>"
                for rem in r.remediations
            )
            remediations_html = f"<ul class='rem-list'>{rem_list}</ul>"
        else:
            remediations_html = "<span class='no-rem'>None required</span>"

        rows.append(f"""
        <tr>
            <td><code>{html.escape(r.control_id)}</code></td>
            <td>{html.escape(r.control_name)}</td>
            <td><span class="badge" style="background-color: {sev_color};">{html.escape(r.severity.upper())}</span></td>
            <td><span class="badge" style="background-color: {status_color};">{html.escape(r.status.upper())}</span></td>
            <td>{r.risk_score:.1f} ({html.escape(r.risk_level.upper())})</td>
            <td>{remediations_html}</td>
        </tr>
        """)


    table_body = "\n".join(rows)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ConfigSentinel Audit Report - {html.escape(audit_id)}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0F172A; color: #E2E8F0; padding: 24px; margin: 0; }}
        .header {{ border-bottom: 2px solid #334155; padding-bottom: 16px; margin-bottom: 24px; }}
        h1 {{ color: #38BDF8; margin: 0 0 8px 0; }}
        .meta-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }}
        .card {{ background: #1E293B; border: 1px solid #334155; border-radius: 8px; padding: 16px; text-align: center; }}
        .card .val {{ font-size: 24px; font-weight: bold; margin-top: 4px; }}
        .val.pass {{ color: #34D399; }}
        .val.fail {{ color: #F87171; }}
        .val.review {{ color: #FBBF24; }}
        .val.total {{ color: #38BDF8; }}
        table {{ width: 100%; border-collapse: collapse; background: #1E293B; border-radius: 8px; overflow: hidden; }}
        th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid #334155; vertical-align: top; }}
        th {{ background: #0F172A; color: #94A3B8; text-transform: uppercase; font-size: 12px; }}
        .badge {{ padding: 4px 8px; border-radius: 4px; color: #FFF; font-weight: bold; font-size: 11px; display: inline-block; }}
        pre {{ background: #0F172A; padding: 8px; border-radius: 4px; margin: 4px 0 0 0; white-space: pre-wrap; word-break: break-all; font-size: 12px; color: #A7F3D0; }}
        ul.rem-list {{ margin: 0; padding-left: 16px; font-size: 13px; }}
        .no-rem {{ color: #64748B; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>ConfigSentinel Executive Audit Report</h1>
        <div>Audit ID: <code>{html.escape(audit_id)}</code> | Vendor: <strong>{html.escape(summary.vendor.upper())}</strong> | Hostname: <strong>{html.escape(summary.hostname or "N/A")}</strong></div>
    </div>

    <div class="meta-grid">
        <div class="card"><div class="lbl">Pass Count</div><div class="val pass">{summary.pass_count}</div></div>
        <div class="card"><div class="lbl">Fail Count</div><div class="val fail">{summary.fail_count}</div></div>
        <div class="card"><div class="lbl">Needs Review</div><div class="val review">{summary.needs_review_count}</div></div>
        <div class="card"><div class="lbl">Total Controls</div><div class="val total">{summary.total_controls}</div></div>
    </div>

    <h2>Control Audit Results</h2>
    <table>
        <thead>
            <tr>
                <th>Control ID</th>
                <th>Title</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Risk Score</th>
                <th>Remediation Guidance</th>
            </tr>
        </thead>
        <tbody>
            {table_body}
        </tbody>
    </table>
</body>
</html>
"""

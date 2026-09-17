"""Numbers in, PDF out.

You don't draw a PDF. You write a small web page and ask a browser to print it,
which means ordinary HTML and CSS are the whole layout language.
"""
from datetime import date
from pathlib import Path

from playwright.sync_api import sync_playwright

CSS = """
  body { font-family: system-ui, sans-serif; color: #222; margin: 0; }
  h1 { margin: 0 0 4px; font-size: 22px; }
  .sub { color: #666; margin-bottom: 20px; font-size: 12px; }
  .totals { display: flex; gap: 16px; margin-bottom: 22px; }
  .card { border: 1px solid #ddd; border-radius: 8px; padding: 12px 16px; flex: 1; }
  .card .n { font-size: 24px; font-weight: 600; }
  .card .l { color: #666; font-size: 11px; text-transform: uppercase; }
  h2 { font-size: 14px; margin: 18px 0 6px; }
  table { border-collapse: collapse; width: 100%; font-size: 11px; }
  th { background: #f4f4f4; text-align: left; }
  th, td { border: 1px solid #ddd; padding: 5px 7px; }
  td.num, th.num { text-align: right; }

  /* The page-break trap. A long table gets sliced by the printer, and without
     these two rules a row is cut in half across the page boundary and the
     header only ever appears on page 1. */
  thead { display: table-header-group; }
  tr { break-inside: avoid; }
"""


def build_html(d: dict) -> str:
    top = "".join(
        f"<tr><td>{p['product']}</td><td class='num'>{p['orders']}</td>"
        f"<td class='num'>{p['revenue']:.2f}</td></tr>" for p in d["top_products"])
    days = "".join(
        f"<tr><td>{r['day']}</td><td class='num'>{r['orders']}</td>"
        f"<td class='num'>{r['revenue']:.2f}</td></tr>" for r in d["orders_per_day"])
    rows = "".join(
        f"<tr><td class='num'>{o['id']}</td><td>{o['customer']}</td><td>{o['product']}</td>"
        f"<td class='num'>{o['amount']:.2f}</td><td>{o['created_at']}</td></tr>"
        for o in d["orders"])
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body>
  <h1>Sales report</h1>
  <div class="sub">Generated {date.today().isoformat()}</div>
  <div class="totals">
    <div class="card"><div class="n">{d['total_orders']}</div><div class="l">Orders</div></div>
    <div class="card"><div class="n">{d['total_revenue']:.2f}</div><div class="l">Revenue</div></div>
  </div>
  <h2>Top 5 products by revenue</h2>
  <table><thead><tr><th>Product</th><th class="num">Orders</th><th class="num">Revenue</th></tr></thead>
  <tbody>{top}</tbody></table>
  <h2>Last 7 days</h2>
  <table><thead><tr><th>Day</th><th class="num">Orders</th><th class="num">Revenue</th></tr></thead>
  <tbody>{days}</tbody></table>
  <h2>Every order ({d['total_orders']})</h2>
  <table><thead><tr><th class="num">#</th><th>Customer</th><th>Product</th>
  <th class="num">Amount</th><th>Date</th></tr></thead><tbody>{rows}</tbody></table>
</body></html>"""


def render_pdf(d: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(build_html(d), wait_until="load")
        page.pdf(path=str(path), format="A4", print_background=True,
                 margin={"top": "15mm", "bottom": "15mm", "left": "12mm", "right": "12mm"})
        browser.close()
    return path


if __name__ == "__main__":
    from report_data import get_report_data
    out = render_pdf(get_report_data(), Path("reports/test.pdf"))
    print(f"wrote {out} ({out.stat().st_size:,} bytes)")

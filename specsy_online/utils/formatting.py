REGION_TAGS_STYLE = """
                    <style>
                    .region-card {
                        border: 1px solid #30363d;
                        border-radius: 10px;
                        padding: 1.2rem 1.4rem 1rem;
                        margin-bottom: 1rem;
                        position: relative;
                    }
                    .region-card::before {
                        content: '';
                        position: absolute;
                        top: 0; left: 0;
                        width: 4px; height: 100%;
                        border-radius: 10px 0 0 10px;
                    }
                    .region-low::before    { background: #58a6ff; }
                    .region-med::before    { background: #3fb950; }
                    .region-high::before   { background: #f78166; }
                    .region-vhigh::before  { background: #d2a8ff; }
                    .region-region::before { background: #ffa657; }
                    </style>
                    """

REGION_TAGS_COLORS = {"region": "#ffa657", "low": "#58a6ff",
                      "med": "#3fb950", "high": "#f78166", "vhigh": "#d2a8ff"}


REGION_LABELS = {1: ["region"],
                 2: ["low", "high"],
                 3: ["low", "med", "high"],
                 4: ["low", "med", "high", "vhigh"]}


def card_formating(label):
    msg = (f'<div class="region-card region-{label}">'
           f'<p style="color:{REGION_TAGS_COLORS[label]};font-size:0.75rem;font-weight:600;'
           f'text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem;">'
           f'Region · {label.upper()}</p>')

    return msg



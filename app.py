"""
CS 178 - Lab 20: Data Visualization
Flask app serving three Plotly charts on a single page,
using live data fetched from PokéAPI.

The page loads with Charizard by default. Searching for a new Pokémon
updates all three charts simultaneously without a page reload.

Run with:
    python3 app.py
Then open: http://localhost:8888
"""

from flask import Flask, render_template, request, jsonify
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests

app = Flask(__name__)


# ── Data Fetch ────────────────────────────────────────────────────────────────

def fetch_pokemon(name="charizard"):
    """
    Fetches base stats, sprite, types, and display name for a single Pokémon.
    Returns a tuple: (DataFrame, sprite_url, display_name, types)

    DataFrame has one row per stat, columns: "stat", "value"
    sprite_url   — front sprite image URL (pixel art)
    display_name — capitalized Pokémon name for use in chart titles
    types        — list of type name strings, e.g. ["fire", "flying"]

    Returns (None, None, None, None) if the Pokémon name is not found.
    """
    url = f"https://pokeapi.co/api/v2/pokemon/{name}"
    response = requests.get(url)

    if response.status_code != 200:
        return None, None, None, None

    data = response.json()

    # The 'stats' list contains one dict per stat.
    # Each looks like: {"base_stat": 78, "stat": {"name": "hp"}}
    stats = [
        {
            "stat": entry["stat"]["name"],   # e.g. "hp", "attack", "special-attack"
            "value": entry["base_stat"]      # e.g. 78
        }
        for entry in data["stats"]
    ]

    df = pd.DataFrame(stats)
    sprite_url   = data["sprites"]["front_default"]
    display_name = data["name"].capitalize()

    # The 'types' list contains one dict per type slot.
    # Each looks like: {"slot": 1, "type": {"name": "fire"}}
    # We extract just the type names in slot order, so types[0] is always primary.
    types = [entry["type"]["name"] for entry in data["types"]]

    return df, sprite_url, display_name, types


# ── Chart Builders ────────────────────────────────────────────────────────────

# Dark theme values — Monokai palette, matching CSS variables in index.html
_BG      = "#3e3d32"         # --surface
_PAPER   = "rgba(0,0,0,0)"  # transparent so card background shows through
_TEXT    = "#f8f8f2"         # --text (Monokai foreground)
_GRID    = "#49483e"         # --surface2 (subtle grid lines)


def apply_dark_theme(fig):
    """
    Applies a dark theme to any Plotly figure so charts blend into the
    dark card UI instead of rendering with a jarring white background.

    Called at the end of every chart builder — students don't need to
    worry about this, but they can override it in their own charts if
    they want a different look.
    """
    fig.update_layout(
        paper_bgcolor=_PAPER,   # transparent — card background shows through
        plot_bgcolor=_BG,       # matches the card surface color
        font=dict(color=_TEXT, family="DM Sans, sans-serif"),
        xaxis=dict(gridcolor=_GRID, zerolinecolor=_GRID),
        yaxis=dict(gridcolor=_GRID, zerolinecolor=_GRID),
        # Polar axis theming — applies to radar charts, ignored by other types
        polar=dict(
            bgcolor=_BG,
            radialaxis=dict(gridcolor=_GRID, linecolor=_GRID, tickfont=dict(color=_TEXT)),
            angularaxis=dict(gridcolor=_GRID, linecolor=_GRID),
        ),
        # autosize=True lets Plotly fill whatever container it's placed in.
        # The chart-container div in index.html controls the actual width.
        autosize=True,
        height=340,
        margin=dict(t=40, b=24, l=24, r=24),
    )
    return fig


def build_bad_chart(df):
    """
    Builds the deliberately broken pie chart.
    """
    fig = px.pie(
        df,
        names="stat",    # raw API names — not human-readable
        values="value",
        color="stat",    # rainbow — one color per stat, conveys nothing
    )
    return apply_dark_theme(fig)


def build_good_chart(df, display_name, types):
    """
    TODO (Part A): Students replace the pie chart below with a radar chart,
    then update the fillcolor and line color to match the Pokémon's type.

    'types' is a list of type name strings, e.g. ["fire", "flying"].
    types[0] is the primary type. Use TYPE_COLORS[types[0]] to get its hex color.
    """

    # ── Type color reference ───────────────────────────────────────────────────
    # Standard Pokémon type colors — same palette used in the games and Bulbapedia.
    # Use this dict to look up the hex color for any type name.
    TYPE_COLORS = {
        "normal":   "#A8A878", "fire":     "#F08030", "water":    "#6890F0",
        "electric": "#F8D030", "grass":    "#78C850", "ice":      "#98D8D8",
        "fighting": "#C03028", "poison":   "#A040A0", "ground":   "#E0C068",
        "flying":   "#A890F0", "psychic":  "#F85888", "bug":      "#A8B820",
        "rock":     "#B8A038", "ghost":    "#705898", "dragon":   "#7038F8",
        "dark":     "#705848", "steel":    "#B8B8D0", "fairy":    "#EE99AC",
    }

    # ── START: Replace this with your radar chart, then update the color ───────

      # Convert primary type's hex color to rgba
    hex_color = TYPE_COLORS[types[0]]
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)

    fill   = f"rgba({r}, {g}, {b}, 0.3)"
    border = f"rgba({r}, {g}, {b}, 1.0)"

    stats  = df["stat"].tolist()
    values = df["value"].tolist()
    stats_closed  = stats  + [stats[0]]
    values_closed = values + [values[0]]

    good_fig = go.Figure()
    good_fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=stats_closed,
        fill="toself",
        fillcolor=fill,    # ← dynamic type color (semi-transparent)
        line=dict(color=border),  # ← dynamic type color (fully opaque)
        name=display_name,
    ))
    good_fig.update_layout(
        title=f"{display_name} — Base Stat Radar",
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 160],
            )
        ),
    )

    # Step 2 — replace the hardcoded fillcolor and line color with the
    #           color for this Pokémon's primary type. For example, if the
    #           primary type is "fire" the color would be TYPE_COLORS["fire"].
    #           Use types[0] to always get the primary type dynamically.



    # ── END ────────────────────────────────────────────────────────────────────
    return apply_dark_theme(good_fig)


def build_my_chart(df, display_name, types):
    """
    Horizontal lollipop chart sorted by stat value (ascending, so the
    highest stat sits at the top).  Uses a colorblind-safe Okabe-Ito
    palette — one color per stat so bars are easy to distinguish at a
    glance.
    """

    # ── Colorblind-safe Okabe-Ito palette (6 colors for 6 stats) ──────────
    OKABE_ITO = ["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00"]

    # Sort ascending so the strongest stat appears at the top of the chart
    df_sorted = df.sort_values("value", ascending=True).reset_index(drop=True)

    colors = [OKABE_ITO[i % len(OKABE_ITO)] for i in range(len(df_sorted))]

    fig = go.Figure()

    # ── Stems (horizontal lines from 0 → value) ───────────────────────────
    for i, row in df_sorted.iterrows():
        fig.add_shape(
            type="line",
            x0=0, x1=row["value"],
            y0=i, y1=i,
            line=dict(color=colors[i], width=2),
        )

    # ── Dots at the tip of each stem ──────────────────────────────────────
    fig.add_trace(
        go.Scatter(
            x=df_sorted["value"],
            y=df_sorted["stat"],
            mode="markers+text",
            marker=dict(color=colors, size=14, line=dict(width=1, color="white")),
            text=df_sorted["value"],
            textposition="middle right",
            textfont=dict(size=12),
            hovertemplate="<b>%{y}</b>: %{x}<extra></extra>",
            showlegend=False,
        )
    )

    # ── Layout ─────────────────────────────────────────────────────────────
    fig.update_layout(
        title=dict(
            text=f"{display_name} — Base Stats",
            font=dict(size=18),
        ),
        xaxis=dict(
            title="Base Stat Value",
            range=[0, max(df_sorted["value"]) * 1.2],   # room for labels
            showgrid=True,
            gridwidth=1,
        ),
        yaxis=dict(
            title="Stat",
            tickmode="array",
            tickvals=list(range(len(df_sorted))),
            ticktext=df_sorted["stat"].tolist(),
        ),
        margin=dict(l=80, r=60, t=60, b=50),
        height=380,
    )

    return apply_dark_theme(fig)


# ── Helper ────────────────────────────────────────────────────────────────────

def to_html(fig, first=False):
    """
    Convert a Plotly figure to an embeddable HTML string.

    full_html=False  → just the <div>, not a complete HTML document
    include_plotlyjs → "cdn" on the first chart only — subsequent charts
                       reuse the already-loaded Plotly JS library.
    """
    return fig.to_html(
        full_html=False,
        include_plotlyjs="cdn" if first else False,
    )


def build_all_charts(name):
    """
    Fetches a Pokémon and builds all three chart HTML strings.
    Returns a dict ready to pass to the template or serialize as JSON.
    Returns None if the Pokémon name is not found.
    """
    df, sprite_url, display_name, types = fetch_pokemon(name)

    if df is None:
        return None

    bad_html  = to_html(build_bad_chart(df),                         first=True)
    good_html = to_html(build_good_chart(df, display_name, types))
    my_html   = to_html(build_my_chart(df, display_name, types))

    return {
        "sprite_url":   sprite_url,
        "display_name": display_name,
        "types":        types,
        "bad_chart":    bad_html,
        "good_chart":   good_html,
        "my_chart":     my_html,
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """
    Renders the page with Charizard pre-loaded.
    All three charts and the sprite are server-rendered on first load.
    """
    charts = build_all_charts("charizard")
    return render_template("index.html", **charts)


@app.route("/search")
def search():
    """
    Returns JSON containing the sprite URL and all three chart HTML strings
    for the requested Pokémon. Called by the search box via fetch() —
    no page reload required.

    Example: GET /search?pokemon=pikachu
    """
    name = request.args.get("pokemon", "").strip().lower()

    if not name:
        return jsonify({"error": "No Pokémon name provided."}), 400

    charts = build_all_charts(name)

    if charts is None:
        return jsonify({"error": f"'{name}' not found. Check the spelling."}), 404

    return jsonify(charts)


if __name__ == "__main__":
    # Port 8888 avoids conflict with Project 1 (port 5000) and Lab 12 (port 8080).
    app.run(host="0.0.0.0", port=8888, debug=True)

"""Light, system, and dark appearance styles."""

LIGHT = {
    "bg": "#f8fafc",
    "panel": "#ffffff",
    "fg": "#172033",
    "muted": "#536174",
    "border": "#cbd5e1",
    "start_bg": "#ecfdf5",
    "start_fg": "#047857",
    "start_border": "#86efac",
    "end_bg": "#fff1f2",
    "end_fg": "#be123c",
    "end_border": "#fda4af",
    "length_bg": "#eff6ff",
    "length_fg": "#1d4ed8",
}

DARK = {
    "bg": "#0b1220",
    "panel": "#172338",
    "fg": "#e8eef8",
    "muted": "#b7c5d9",
    "border": "#52647e",
    "start_bg": "#12362f",
    "start_fg": "#8af0ba",
    "start_border": "#219e74",
    "end_bg": "#3a1d2b",
    "end_fg": "#ff9eae",
    "end_border": "#d65a78",
    "length_bg": "#1b3157",
    "length_fg": "#a8c8ff",
}


def _variables(colors: dict[str, str], mode: str) -> str:
    declarations = "".join(f"--mc-{name.replace('_', '-')}: {value};" for name, value in colors.items())
    return f".stApp {{{declarations} color-scheme: {mode};}}"


def theme_css(selection: str) -> str:
    """Return CSS for the selected appearance mode."""
    if selection == "Dark":
        variables = _variables(DARK, "dark")
    elif selection == "Light":
        variables = _variables(LIGHT, "light")
    else:
        variables = (
            _variables(LIGHT, "light")
            + "@media (prefers-color-scheme: dark) {"
            + _variables(DARK, "dark")
            + "}"
        )
    return f"""
<style>
{variables}
.stApp {{background: var(--mc-bg) !important; color: var(--mc-fg) !important;}}
.stApp [data-testid="stHeader"],
.stApp [data-testid="stBottom"] {{background: var(--mc-bg) !important;}}
.stApp [data-testid="stMarkdownContainer"] h1,
.stApp [data-testid="stMarkdownContainer"] h2,
.stApp [data-testid="stMarkdownContainer"] h3,
.stApp [data-testid="stMarkdownContainer"] h4,
.stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stWidgetLabel"] p {{color: var(--mc-fg) !important;}}
.stApp label,
.stApp label span,
.stApp label p,
.stApp [data-testid="stWidgetLabel"] span {{color: var(--mc-fg) !important;}}
.stApp [data-testid="stCaptionContainer"] p {{color: var(--mc-muted) !important;}}
.stApp .sub-caption {{color: var(--mc-muted) !important;}}
.stApp [data-testid="stFileUploader"],
.stApp [data-testid="stFileUploaderDropzone"],
.stApp [data-testid="stExpander"],
.stApp div[data-baseweb="select"] > div,
.stApp .react-aria-ComboBox > [role="group"],
.stApp input[role="combobox"],
.stApp input[data-testid="stTextInputField"] {{
    background: var(--mc-panel) !important;
    color: var(--mc-fg) !important;
    border-color: var(--mc-border) !important;
}}
.stApp .react-aria-ComboBox [aria-haspopup="listbox"] {{
    background: var(--mc-panel) !important;
    color: var(--mc-fg) !important;
}}
.stApp [data-testid="stFileUploaderDropzone"] button,
.stApp [data-testid="stFileUploaderDropzone"] button span {{
    background: var(--mc-panel) !important;
    color: var(--mc-fg) !important;
    border-color: var(--mc-border) !important;
}}
.stApp [data-testid="stTable"] table,
.stApp [data-testid="stTable"] thead,
.stApp [data-testid="stTable"] tbody,
.stApp [data-testid="stTable"] tr,
.stApp [data-testid="stTable"] th,
.stApp [data-testid="stTable"] td {{
    background: var(--mc-panel) !important;
    color: var(--mc-fg) !important;
    border-color: var(--mc-border) !important;
}}
.stApp [data-testid="stSlider"] [role="slider"] {{
    background: #1d4ed8 !important;
    border-color: #93c5fd !important;
}}
.stApp [data-testid="stSliderThumbValue"],
.stApp [data-testid="stSliderThumbValue"] p {{
    background: #1e3a8a !important;
    color: #ffffff !important;
}}
.stApp [data-testid="stAlert"] p {{color: var(--mc-fg) !important;}}
html body .stApp .stMainBlockContainer .react-aria-ComboBox > div[data-rac][role="group"],
html body .stApp .stMainBlockContainer .react-aria-ComboBox > div[data-rac][role="group"] > input {{
    background-color: var(--mc-panel) !important;
    color: var(--mc-fg) !important;
}}
.stApp .range-heading {{color: var(--mc-fg) !important;}}
.stApp .cut-length {{
    background: var(--mc-length-bg) !important;
    color: var(--mc-length-fg) !important;
    border-color: var(--mc-border) !important;
}}
.stApp input[aria-label="Start time input"],
.stApp input[aria-label="Start time input"] {{
    background: var(--mc-start-bg) !important;
    color: var(--mc-start-fg) !important;
    border-color: var(--mc-start-border) !important;
}}
.stApp input[aria-label="End time input"],
.stApp input[aria-label="End time input"] {{
    background: var(--mc-end-bg) !important;
    color: var(--mc-end-fg) !important;
    border-color: var(--mc-end-border) !important;
}}
</style>
"""

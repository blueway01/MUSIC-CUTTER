import json
import hashlib
import io
import os
import re
import subprocess
from pathlib import Path
import streamlit as st
from pydub import AudioSegment
from auto_split import find_song_boundaries, make_ranges
from clip_editor import clip_duration, list_saved_clips, preview_segment, save_revised_clip
from cut_storage import clean_title, delete_history_entry, read_history, save_cuts
from folder_actions import open_folder, select_folder
from public_storage import reset_session_directory, session_directory
from save_location import output_directory
from ui_text import translate
from ui_theme import theme_css
from waveform import waveform_levels

SOURCE_DIR = Path(__file__).resolve().parent
ICON_PATH = SOURCE_DIR / "assets" / "music-cutter-icon.png"
st.set_page_config(
    page_title="MUSIC CUTTER",
    page_icon=str(ICON_PATH) if ICON_PATH.is_file() else "✂️",
    layout="centered",
)
APP_DIR = Path(os.environ.get("MUSIC_CUTTER_APP_DIR", Path(__file__).resolve().parent)).resolve()
PUBLIC_MODE = os.environ.get("MUSIC_CUTTER_PUBLIC") == "1"


def T(key: str, **values: object) -> str:
    """Return a message in the selected interface language."""
    return translate(key, st.session_state.get("language", "English"), **values)


theme_column, language_column = st.columns(2)
with theme_column:
    st.selectbox(
        T('Appearance'),
        ['Light', 'System', 'Dark'],
        index=2,
        key="theme_mode",
        format_func=T,
    )
with language_column:
    st.selectbox(
        T('Language'),
        ['English', 'Japanese'],
        index=0,
        key="language",
        format_func=lambda value: "\u65e5\u672c\u8a9e" if value == "Japanese" else "English",
    )

# Application workflow.
AUTO_MIN_SONG_SECONDS = 45
WAVE_COLORS = ["#38bdf8", "#a78bfa", "#34d399", "#fbbf24", "#fb7185", "#22d3ee", "#c084fc", "#a3e635"]

# Application workflow.
st.markdown("""
    <style>
    /* Layout and visual styling. */
    .block-container {
        max-width: 780px !important;
        padding-top: 5rem !important;
        padding-bottom: 1rem !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Layout and visual styling. */
    [data-testid="stMainBlockContainer"] {
        padding-top: 5rem !important;
    }

    @media (max-width: 640px) {
        .block-container,
        [data-testid="stMainBlockContainer"] {
            padding-top: 4.5rem !important;
        }
    }
    
    /* Layout and visual styling. */
    div.stElementContainer, div.stMarkdown {
        margin-bottom: 0.3rem !important;
    }

    /* Layout and visual styling. */
    .header-container {
        text-align: center;
        margin-bottom: 0.8rem;
        padding: 0.2rem 0;
    }
    .main-title {
        font-size: 2.2rem;
        font-weight: 900;
        letter-spacing: 1px;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        text-shadow: 0 5px 15px rgba(59, 130, 246, 0.15);
    }
    .sub-caption {
        color: #64748b;
        font-size: 0.85rem;
        font-weight: 500;
        margin-top: 0;
    }

    /* Layout and visual styling. */
    div[data-testid="stFileUploader"] {
        background: #ffffff;
        padding: 0.8rem 1.2rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 15px -3px rgba(0, 0, 0, 0.03);
        margin-bottom: 0.8rem;
    }
    
    /* Layout and visual styling. */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 700 !important;
        min-height: 2.75rem !important;
        background: #1d4ed8 !important;
        color: #ffffff !important;
        border: 2px solid #1e40af !important;
        box-shadow: 0 3px 8px rgba(37, 99, 235, 0.2) !important;
    }
    .stButton > button:hover {
        background: #1e40af !important;
        border-color: #172554 !important;
    }
    .stButton > button:disabled {
        background: #94a3b8 !important;
        border-color: #94a3b8 !important;
        box-shadow: none !important;
    }

    /* Layout and visual styling. */
    /* Layout and visual styling. */
    input[aria-label="Start time input"] {
        text-align: center !important;
        font-size: 20px !important;
        font-weight: 800 !important;
        color: #059669 !important;
        border-radius: 8px !important;
        border: 2px solid #a7f3d0 !important;
        background-color: #ecfdf5 !important;
        padding: 4px 0 !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.02) !important;
    }
    input[aria-label="Start time input"]:focus {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2) !important;
    }

    /* Layout and visual styling. */
    input[aria-label="End time input"] {
        text-align: center !important;
        font-size: 20px !important;
        font-weight: 800 !important;
        color: #e11d48 !important;
        border-radius: 8px !important;
        border: 2px solid #fecdd3 !important;
        background-color: #fff1f2 !important;
        padding: 4px 0 !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.02) !important;
    }
    input[aria-label="End time input"]:focus {
        border-color: #f43f5e !important;
        box-shadow: 0 0 0 3px rgba(244, 63, 94, 0.2) !important;
    }
    </style>
""", unsafe_allow_html=True)
st.markdown(theme_css(st.session_state.get("theme_mode", 'Dark')), unsafe_allow_html=True)

# Application workflow.
st.markdown(f"""
    <div class="header-container">
        <div class="main-title">🎵 MUSIC CUTTER</div>
        <div class="sub-caption">{T("Waveform editor with precise audio trimming")}</div>
    </div>
""", unsafe_allow_html=True)

def format_time(seconds):
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins:02d}:{secs:06.3f}"

def parse_time_str(time_str):
    """English implementation note."""
    try:
        time_str = time_str.replace("：", ":").strip()
        parts = time_str.split(":")
        if len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 1:
            return float(parts[0])
    except ValueError:
        pass
    return 0.0


def read_input_time(value: str) -> float | None:
    """English implementation note."""
    normalized = value.strip().replace("：", ":")
    if not re.fullmatch(r"\d+(?::\d{1,2})?(?:\.\d{1,3})?", normalized):
        return None
    return round(parse_time_str(normalized), 3)


def repair_selection(duration: float) -> None:
    """English implementation note."""
    if duration < 0.001:
        return
    slider = st.session_state.get("cut_slider", (0.0, duration))
    if not isinstance(slider, (tuple, list)) or len(slider) != 2:
        slider = (0.0, duration)
    slider_start, slider_end = slider
    if not 0 <= slider_start < slider_end <= duration:
        slider_start, slider_end = 0.0, duration

    start = read_input_time(str(st.session_state.get("start_input", "")))
    end = read_input_time(str(st.session_state.get("end_input", "")))
    start = slider_start if start is None else start
    end = slider_end if end is None else end
    start = round(max(0.0, min(start, duration - 0.001)), 3)
    end = round(max(start + 0.001, min(end, duration)), 3)

    st.session_state.start_input = format_time(start)
    st.session_state.end_input = format_time(end)
    st.session_state.cut_slider = (start, end)
    st.session_state.pop("range_error", None)


def sync_slider_to_inputs() -> None:
    """English implementation note."""
    start, end = st.session_state.cut_slider
    st.session_state.start_input = format_time(start)
    st.session_state.end_input = format_time(end)
    repair_selection(st.session_state.source_duration)


def sync_inputs_to_slider(duration: float) -> None:
    """English implementation note."""
    repair_selection(duration)


def sync_clip_slider() -> None:
    """English implementation note."""
    start = read_input_time(str(st.session_state.get("clip_start", "")))
    end = read_input_time(str(st.session_state.get("clip_end", "")))
    duration = st.session_state.get("clip_duration_seconds", 0.0)
    if start is not None and end is not None and 0 <= start < end <= duration:
        st.session_state.clip_slider = (start, end)


def sync_clip_inputs() -> None:
    """English implementation note."""
    start, end = st.session_state.clip_slider
    st.session_state.clip_start = format_time(start)
    st.session_state.clip_end = format_time(end)


def add_current_range(duration: float) -> None:
    """English implementation note."""
    try:
        repair_selection(duration)
        start = round(parse_time_str(st.session_state.start_input), 3)
        end = round(parse_time_str(st.session_state.end_input), 3)
        if not 0 <= start < end <= duration:
            raise ValueError('Set start and end within the audio duration.')
        title = clean_title(st.session_state.cut_title)
        st.session_state.pop("save_notice", None)
        song_number = st.session_state.completed_in_session + len(st.session_state.cut_ranges) + 1
        st.session_state.cut_ranges.append({"start": start, "end": end, "title": title})
        st.session_state.range_notice = (song_number, None)
        if end < duration:
            st.session_state.start_input = format_time(end)
            st.session_state.end_input = format_time(duration)
            st.session_state.cut_slider = (end, duration)
            next_number = song_number + 1
            st.session_state.cut_title = f"{st.session_state.source_title}_{next_number:02d}"
            st.session_state.range_notice = (song_number, next_number)
    except ValueError as error:
        st.session_state.range_error = str(error)


def wav_preview(segment):
    """English implementation note."""
    stream = io.BytesIO()
    segment.export(stream, format="wav")
    return stream.getvalue()


def range_player_html(start: float, end: float) -> str:
    """English implementation note."""
    return f"""
    <audio id="rangeAudio" controls preload="metadata" style="width:100%;height:40px;"></audio>
    <script>
        const source = window.parent.document.querySelector('.st-key-source_player audio');
        const player = document.getElementById('rangeAudio');
        const start = {start};
        const end = {end};
        if (source) {{
            player.addEventListener('loadedmetadata', () => {{ player.currentTime = start; }});
            player.addEventListener('play', () => {{
                if (player.currentTime < start || player.currentTime >= end) player.currentTime = start;
            }});
            player.addEventListener('timeupdate', () => {{
                if (player.currentTime >= end) {{
                    player.pause();
                    player.currentTime = end;
                }}
            }});
            player.src = source.currentSrc || source.src;
        }}
    </script>
    """


def reset_work() -> None:
    """English implementation note."""
    if PUBLIC_MODE:
        reset_session_directory(st.session_state)
    st.session_state.upload_nonce = st.session_state.get("upload_nonce", 0) + 1
    work_keys = {
        "source_id", "decoded_source_id", "source_audio", "source_wave_data",
"cut_ranges", "start_input", "end_input", "cut_title", "saved_through",
        "cut_slider", "source_title", "source_duration", "completed_in_session", "range_notice",
        "range_error", "save_notice", "auto_notice", "range_preview", "auto_result", "auto_applied_signature", "work_mode",
        "auto_extra_boundaries",
        "clip_save_notice", "clip_selected_path", "clip_duration_seconds",
        "clip_start", "clip_end", "clip_slider", "clip_title", "download_clip",
    }
    for key in list(st.session_state):
        if key in work_keys or (key.startswith("upload_") and key != "upload_nonce") or key.startswith(("auto_candidate_", "range_title_")):
            del st.session_state[key]


def choose_folder() -> None:
    """English implementation note."""
    try:
        selected = select_folder(
            st.session_state.get("custom_dir") or str(APP_DIR),
        )
        if selected:
            st.session_state.custom_dir = selected
        st.session_state.pop("folder_picker_error", None)
    except Exception as error:
        st.session_state.folder_picker_error = str(error)

# Application workflow.
st.markdown(f"### {T('① Choose an audio file')}")
uploaded_file = st.file_uploader(
    T('Upload audio (.mp3, .wav, .m4a)'),
    type=["mp3", "wav", "m4a"],
    key=f"upload_{st.session_state.get('upload_nonce', 0)}",
)
output_dir = None

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()

    try:
        source_id = (uploaded_file.name, hashlib.sha256(file_bytes).hexdigest())
        if st.session_state.get("decoded_source_id") != source_id:
            st.session_state.pop("source_audio", None)
            st.session_state.pop("source_wave_data", None)
            decoded_audio = AudioSegment.from_file(io.BytesIO(file_bytes))
            st.session_state.source_wave_data = waveform_levels(decoded_audio)
            st.session_state.source_audio = decoded_audio
            st.session_state.decoded_source_id = source_id
        audio = st.session_state.source_audio
        duration_sec = len(audio) / 1000.0
        wave_data = st.session_state.source_wave_data
        st.info(T(
            'Loaded source: {name} / Duration {duration}',
            name=uploaded_file.name,
            duration=format_time(duration_sec),
        ))

        if st.session_state.get("source_id") != source_id:
            st.session_state.source_id = source_id
            st.session_state.cut_ranges = []
            st.session_state.start_input = "00:00.0"
            st.session_state.end_input = format_time(duration_sec)
            st.session_state.cut_slider = (0.0, duration_sec)
            st.session_state.cut_title = f"{Path(uploaded_file.name).stem}_01"
            st.session_state.source_title = Path(uploaded_file.name).stem
            st.session_state.source_duration = duration_sec
            st.session_state.completed_in_session = 0
            st.session_state.saved_through = 0.0
            st.session_state.pop("range_notice", None)
            st.session_state.pop("range_error", None)
            st.session_state.pop("save_notice", None)
            st.session_state.pop("auto_notice", None)
            st.session_state.pop("range_preview", None)
            st.session_state.pop("auto_result", None)
            st.session_state.pop("auto_applied_signature", None)
            st.session_state.pop("auto_extra_boundaries", None)
            for key in list(st.session_state):
                if key.startswith(("auto_candidate_", "range_title_")):
                    del st.session_state[key]

        default_end_str = format_time(duration_sec)

        if "start_input" not in st.session_state:
            st.session_state.start_input = "00:00.0"
        if "end_input" not in st.session_state:
            st.session_state.end_input = default_end_str
        if "cut_slider" not in st.session_state:
            st.session_state.cut_slider = (0.0, duration_sec)
        st.session_state.source_duration = duration_sec
        repair_selection(duration_sec)

        st.markdown(f"### {T('② Choose a splitting method')}")
        work_mode = st.radio(T('Splitting method'), ['Manual', 'Automatic'], horizontal=True, key="work_mode", format_func=T)
        st.caption(T('Set start and end times manually, or analyze the gaps between songs automatically.'))

        # ---------------------------------------------------------
        # Application workflow.
        # ---------------------------------------------------------
        calc_start = parse_time_str(st.session_state.start_input)
        calc_end = min(parse_time_str(st.session_state.end_input), duration_sec)
        cut_length = max(0.0, calc_end - calc_start)
        last_listed_end = st.session_state.cut_ranges[-1]["end"] if st.session_state.cut_ranges else st.session_state.get("saved_through", 0.0)
        has_manual_selection = (
            work_mode == 'Manual'
            and last_listed_end < duration_sec
            and last_listed_end <= calc_start < calc_end
        )

        mime_type = {
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".m4a": "audio/mp4",
        }[Path(uploaded_file.name).suffix.lower()]
        wave_json = json.dumps(wave_data)
        preview_ranges = list(st.session_state.cut_ranges)
        if has_manual_selection:
            preview_ranges.append({"start": calc_start, "end": calc_end})
        cut_ranges_json = json.dumps(
            [{"start": item["start"], "end": item["end"]} for item in preview_ranges]
        )
        colors_json = json.dumps(WAVE_COLORS)
        cut_count = len(preview_ranges)
        color_legend = "".join(
            f'<span style="display:inline-flex;align-items:center;gap:4px;color:#e2e8f0;font-size:11px;">'
            f'<span style="width:10px;height:10px;border-radius:3px;background:{WAVE_COLORS[idx % len(WAVE_COLORS)]};"></span>'
            f'{T("Track {number}", number=st.session_state.completed_in_session + idx + 1)}</span>'
            for idx in range(cut_count)
        )

        player_html = f"""
        <div style="background: linear-gradient(145deg, #1e293b, #0f172a); padding: 12px 16px; border-radius: 12px; box-shadow: 0 8px 20px -8px rgba(15, 23, 42, 0.3); margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <div style="font-size: 13px; font-weight: 700; color: #f8fafc; letter-spacing: 0.5px;">
                    📈 {T("WAVEFORM PREVIEW")}
                </div>
                <div style="background:#0ea5e9;color:white;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:800;">
                    {T("Split songs: {count}", count=cut_count)}
                </div>
                <button onclick="jumpToStart()" style="background: linear-gradient(135deg, #10b981, #059669); color: white; border: none; padding: 5px 12px; border-radius: 6px; font-size: 11px; font-weight: 700; cursor: pointer; box-shadow: 0 2px 6px rgba(16, 185, 129, 0.3);">
                    {T("▶ Play from start")}
                </button>
            </div>
            <canvas id="waveformCanvas" width="900" height="70" style="width: 100%; margin-top: 6px; background: #020617; border-radius: 8px; border: 1px solid #1e293b;"></canvas>
            <div style="display:flex;flex-wrap:wrap;gap:5px 12px;margin-top:6px;min-height:14px;">{color_legend}</div>
        </div>
        <script>
            let audio = null;
            const canvas = document.getElementById('waveformCanvas');
            const ctx = canvas.getContext('2d');
            
            const duration = {duration_sec};
            const startTime = {calc_start};
            const endTime = {calc_end};
            const barHeights = {wave_json};
            const cutRanges = {cut_ranges_json};
            const cutColors = {colors_json};
            const bars = barHeights.length;

            function connectPlayer() {{
                audio = window.parent.document.querySelector('.st-key-source_player audio');
                if (!audio) return false;
                const seekToStart = () => {{ audio.currentTime = startTime; }};
                if (audio.readyState >= 1) seekToStart();
                else audio.addEventListener('loadedmetadata', seekToStart, {{ once: true }});
                audio.addEventListener('timeupdate', () => {{
                    if (audio.duration) drawWaveform(audio.currentTime);
                }});
                audio.addEventListener('seeked', () => drawWaveform(audio.currentTime));
                return true;
            }}

            if (!connectPlayer()) {{
                const parentObserver = new MutationObserver(() => {{
                    if (connectPlayer()) parentObserver.disconnect();
                }});
                parentObserver.observe(window.parent.document.body, {{ childList: true, subtree: true }});
            }}

            function jumpToStart() {{
                if (!audio) return;
                audio.currentTime = startTime;
                audio.play();
            }}

            canvas.addEventListener('click', (event) => {{
                if (!audio || !duration) return;
                const bounds = canvas.getBoundingClientRect();
                const fraction = Math.min(1, Math.max(0, (event.clientX - bounds.left) / bounds.width));
                audio.currentTime = fraction * duration;
            }});

            function drawWaveform(currentTime = -1) {{
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                const barWidth = canvas.width / bars;
                
                for (let i = 0; i < bars; i++) {{
                    const x = i * barWidth;
                    const h = barHeights[i] * (canvas.height * 0.8);
                    const y = (canvas.height - h) / 2;
                    
                    const t = (i / bars) * duration;
                    const cutIndex = cutRanges.findIndex(range => t >= range.start && t <= range.end);
                    if (cutIndex >= 0) {{
                        ctx.fillStyle = cutColors[cutIndex % cutColors.length];
                    }} else if (t >= startTime && t <= endTime) {{
                        ctx.fillStyle = '#f43f5e';
                    }} else {{
                        ctx.fillStyle = '#334155';
                    }}
                    ctx.fillRect(x, y, Math.max(barWidth - 0.5, 1), h);
                }}

                const startX = (startTime / duration) * canvas.width;
                const endX = (endTime / duration) * canvas.width;

                ctx.strokeStyle = '#10b981';
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.moveTo(startX, 0);
                ctx.lineTo(startX, canvas.height);
                ctx.stroke();

                ctx.strokeStyle = '#f43f5e';
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.moveTo(endX, 0);
                ctx.lineTo(endX, canvas.height);
                ctx.stroke();

                if (currentTime >= 0) {{
                    const playX = (currentTime / duration) * canvas.width;
                    ctx.strokeStyle = '#38bdf8';
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.moveTo(playX, 0);
                    ctx.lineTo(playX, canvas.height);
                    ctx.stroke();
                }}
            }}

            drawWaveform(startTime);
        </script>
        """
        st.iframe(player_html, height=145)
        with st.container(key="source_player"):
            st.audio(file_bytes, format=mime_type)

        # ---------------------------------------------------------
        # Application workflow.
        # ---------------------------------------------------------
        if work_mode == 'Manual':
            st.markdown(f"<h3 class='range-heading' style='font-size: 1.05rem; font-weight: 800; margin-top: 0.2rem; margin-bottom: 0.4rem;'>{T('✂️ Set split range (minutes:seconds)')}</h3>", unsafe_allow_html=True)
            st.caption(T('Start and end times are filled automatically. Edit them in minutes:seconds if needed.'))
        
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"<div style='text-align: center; font-weight: 700; color: var(--mc-start-fg); font-size: 0.85rem; margin-bottom: 2px;'>{T('🟢 Start')}</div>", unsafe_allow_html=True)
                st.text_input(T('Start time input'), key="start_input", label_visibility="collapsed", on_change=sync_inputs_to_slider, args=(duration_sec,))
            with col2:
                st.markdown(f"<div style='text-align: center; font-weight: 700; color: var(--mc-end-fg); font-size: 0.85rem; margin-bottom: 2px;'>{T('🔴 End')}</div>", unsafe_allow_html=True)
                st.text_input(T('End time input'), key="end_input", label_visibility="collapsed", on_change=sync_inputs_to_slider, args=(duration_sec,))
            with col3:
                st.markdown(f"<div style='text-align: center; font-weight: 700; color: var(--mc-length-fg); font-size: 0.85rem; margin-bottom: 2px;'>{T('📏 Duration')}</div>", unsafe_allow_html=True)
                st.markdown(
                    f"<div class='cut-length' style='padding: 4px 0; border-radius: 8px; border: 2px solid; font-weight: 800; font-size: 20px; text-align: center; box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);'>{format_time(cut_length)}</div>",
                    unsafe_allow_html=True
                )

            st.slider(
                T('Split range slider'),
                min_value=0.0,
                max_value=duration_sec,
                step=0.001,
                key="cut_slider",
                on_change=sync_slider_to_inputs,
                format_func=format_time,
                help=T('Moving either handle also updates the time fields.'),
            )
        if work_mode == 'Automatic':
            st.caption(T('Finds gaps using silence and changes in timbre, pitch, and rhythm. Listen to the results before saving.'))
            if st.session_state.get("auto_notice"):
                st.success(T('The split list was updated automatically. Review each track before saving.'))
            min_gap = st.slider(
                T('Minimum silence duration'),
                min_value=0.1,
                max_value=4.0,
                value=0.1,
                step=0.1,
                format="%.1f sec",
            )
            analysis_key = (source_id, min_gap)
            key_prefix = f"auto_candidate_{source_id[1][:12]}_{min_gap}_"
            reanalyze = st.button(T('Analyze song boundaries'), type="primary", width="stretch")
            if reanalyze or st.session_state.get("auto_result", (None,))[0] != analysis_key:
                for key in list(st.session_state):
                    if key.startswith(key_prefix):
                        del st.session_state[key]
                with st.spinner(T('Analyzing song boundaries…')):
                    st.session_state.auto_result = (
                        analysis_key,
                        find_song_boundaries(audio, min_song_seconds=AUTO_MIN_SONG_SECONDS, min_gap_seconds=min_gap),
                    )
                    st.session_state.pop("auto_applied_signature", None)
                    st.session_state.auto_extra_boundaries = (analysis_key, [])
            if st.session_state.get("auto_result", (None,))[0] == analysis_key:
                candidates = st.session_state.auto_result[1]
                selected_boundaries = []
                invalid_boundary = False
                if not candidates:
                    st.info(T('No song boundary met the criteria. The full audio is listed as one track; review it before saving.'))
                else:
                    st.markdown(f"#### {T('Song boundary candidates: {count}', count=len(candidates))}")
                    for idx, candidate in enumerate(candidates):
                        summary_col, time_col, gap_col = st.columns([2.1, 1.2, 1.2])
                        with summary_col:
                            selected = st.checkbox(
                                T('Use candidate {number}', number=idx + 1),
                                value=True,
                                key=f"{key_prefix}use_{idx}",
                            )
                        with time_col:
                            st.markdown(f"**{format_time(candidate['seconds'])}**")
                        with gap_col:
                            st.caption(T('Silence: {seconds} sec', seconds=candidate["silence_seconds"]))
                        with st.expander(T('Candidate {number}: preview and details', number=idx + 1), expanded=False):
                            edited_time = st.text_input(
                                T('Candidate {number} boundary (min:sec.milliseconds)', number=idx + 1),
                                value=format_time(candidate["seconds"]),
                                key=f"{key_prefix}time_{idx}",
                            )
                            boundary_seconds = read_input_time(edited_time)
                            st.caption(T(
                                'Timbre similarity {timbre} / Pitch similarity {pitch} / Rhythm similarity {rhythm}',
                                timbre=candidate["timbre_similarity"],
                                pitch=candidate["pitch_similarity"],
                                rhythm=candidate["rhythm_similarity"],
                            ))
                            if boundary_seconds is not None and 0 < boundary_seconds < duration_sec:
                                before_ms = round(candidate["silence_start_seconds"] * 1000)
                                after_ms = round(candidate["silence_end_seconds"] * 1000)
                                before_col, after_col = st.columns(2)
                                with before_col:
                                    st.caption(T('3 sec before silence'))
                                    st.audio(wav_preview(audio[max(0, before_ms - 3000):before_ms]), format="audio/wav")
                                with after_col:
                                    st.caption(T('3 sec after silence'))
                                    st.audio(wav_preview(audio[after_ms:min(len(audio), after_ms + 3000)]), format="audio/wav")
                            else:
                                st.error(T('Set the boundary within the audio duration.'))
                                invalid_boundary = invalid_boundary or selected
                            if selected and boundary_seconds is not None:
                                selected_boundaries.append(boundary_seconds)

                st.markdown(f"#### {T('Add a missed song boundary')}")
                st.caption(T('Enter a boundary missed by automatic analysis. It will be added without removing the detected boundaries.'))
                extra_col, add_col = st.columns([3, 1])
                with extra_col:
                    extra_time = st.text_input(
                        T('Boundary to add (min:sec.milliseconds)'),
                        placeholder="08:31.000",
                        key=f"{key_prefix}extra_time",
                    )
                with add_col:
                    add_extra = st.button(
                        T('Add boundary'),
                        key=f"{key_prefix}extra_add",
                        type="primary",
                        width="stretch",
                    )
                stored_extra = st.session_state.get("auto_extra_boundaries", (analysis_key, []))
                extra_boundaries = list(stored_extra[1]) if stored_extra[0] == analysis_key else []
                if add_extra:
                    extra_seconds = read_input_time(extra_time)
                    if extra_seconds is None or not 0 < extra_seconds < duration_sec:
                        st.error(T(
                            '{time} is outside the loaded audio duration ({duration}). Choose the original audio containing all tracks.',
                            time=extra_time or T('blank'),
                            duration=format_time(duration_sec),
                        ))
                        invalid_boundary = True
                    elif all(abs(extra_seconds - value) >= 0.001 for value in extra_boundaries):
                        extra_boundaries.append(extra_seconds)
                        extra_boundaries.sort()
                        st.session_state.auto_extra_boundaries = (analysis_key, extra_boundaries)
                        st.session_state.pop("auto_applied_signature", None)
                        st.rerun()
                for idx, extra_seconds in enumerate(extra_boundaries):
                    extra_label, extra_delete = st.columns([4, 1])
                    with extra_label:
                        st.info(T('Added boundary: {time}', time=format_time(extra_seconds)))
                    with extra_delete:
                        if st.button(T('Remove'), key=f"{key_prefix}extra_delete_{idx}", width="stretch"):
                            extra_boundaries.pop(idx)
                            st.session_state.auto_extra_boundaries = (analysis_key, extra_boundaries)
                            st.session_state.pop("auto_applied_signature", None)
                            st.rerun()
                selected_boundaries.extend(extra_boundaries)

                if not invalid_boundary:
                    signature = (analysis_key, tuple(selected_boundaries))
                    if st.session_state.get("auto_applied_signature") != signature:
                        try:
                            ranges = make_ranges(
                                duration_sec,
                                selected_boundaries,
                                clean_title(Path(uploaded_file.name).stem),
                                min_song_seconds=0.001 if extra_boundaries else (AUTO_MIN_SONG_SECONDS if selected_boundaries else 0.001),
                            )
                            for idx, item in enumerate(ranges):
                                item["title"] = f"{st.session_state.source_title}_{st.session_state.completed_in_session + idx + 1:02d}"
                            for key in list(st.session_state):
                                if key.startswith("range_title_"):
                                    del st.session_state[key]
                            st.session_state.cut_ranges = ranges
                            st.session_state.pop("range_preview", None)
                            next_song_number = st.session_state.completed_in_session + len(ranges) + 1
                            st.session_state.cut_title = f"{st.session_state.source_title}_{next_song_number:02d}"
                            st.session_state.auto_applied_signature = signature
                            st.session_state.auto_notice = True
                            st.rerun()
                        except ValueError as error:
                            st.error(T('Could not update the split list: {error}', error=T(str(error))))

        # ---------------------------------------------------------
        # Application workflow.
        # ---------------------------------------------------------
        st.markdown(f"### {T('③ Review ranges and titles')}")
        pending_range = None
        if work_mode == 'Manual':
            next_song_number = st.session_state.completed_in_session + len(st.session_state.cut_ranges) + 1
            last_end = st.session_state.cut_ranges[-1]["end"] if st.session_state.cut_ranges else st.session_state.get("saved_through", 0.0)
            if has_manual_selection:
                if not str(st.session_state.get("cut_title", "")).strip():
                    st.session_state.cut_title = f"{st.session_state.source_title}_{next_song_number:02d}"
                st.markdown(f"**{T('Next: track {number} · Start {start} / End {end}', number=next_song_number, start=format_time(calc_start), end=format_time(calc_end))}**")
                st.text_input(T('Title for this range (numbered automatically)'), key="cut_title")
                pending_range = {"start": calc_start, "end": calc_end, "title": clean_title(st.session_state.cut_title)}
                if calc_end < duration_sec:
                    st.button(T('Add range and continue to next track'), on_click=add_current_range, args=(duration_sec,), type="primary", width="stretch")
            elif last_end >= duration_sec:
                st.info(T('All audio has been added to the split list.'))
            else:
                st.error(T('Set the next range after the previous track.'))
            if st.session_state.get("range_error"):
                st.error(T(st.session_state.range_error))
            if st.session_state.get("range_notice"):
                added_number, following_number = st.session_state.range_notice
                notice = T('Added track {number} to the list.', number=added_number)
                if following_number is not None:
                    notice += T(' You can now set track {number}.', number=following_number)
                st.success(notice)

        ranges_to_save = list(st.session_state.cut_ranges)
        if pending_range is not None:
            ranges_to_save.append(pending_range)
        if ranges_to_save:
            st.markdown("<hr style='margin: 12px 0 10px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
            st.markdown(f"#### {T('Split tracks ({count})', count=len(ranges_to_save))}")
            range_overview = []
            for idx, item in enumerate(ranges_to_save):
                song_number = st.session_state.completed_in_session + idx + 1
                range_overview.append({
                    T('Track'): T('Track {number}', number=song_number),
                    T('Start'): format_time(item["start"]),
                    T('End'): format_time(item["end"]),
                    T('Cut duration'): format_time(item["end"] - item["start"]),
                    T('Title'): item["title"],
                })
            st.caption(T('All track ranges are shown below, including track 3 and later.'))
            st.table(range_overview)
            
            for idx, r in enumerate(st.session_state.cut_ranges):
                c_info, c_play, c_del = st.columns([3.3, 1, 1])
                with c_info:
                    song_number = st.session_state.completed_in_session + idx + 1
                    range_label = T('Track {number} · Start {start} / End {end}', number=song_number, start=format_time(r["start"]), end=format_time(r["end"]))
                    st.markdown(f"**{range_label} · {T('Cut duration')}: {format_time(r['end'] - r['start'])}**")
                    title_key = f"range_title_{source_id[1][:12]}_{idx}_{round(r['start'] * 1000)}_{round(r['end'] * 1000)}"
                    r["title"] = st.text_input(T('Track {number} title', number=song_number), value=r["title"], key=title_key)
                with c_play:
                    if st.button(T('▶ Play'), key=f"play_{idx}", width="stretch"):
                        st.session_state.range_preview = (
                            source_id,
                            idx,
                            r["start"],
                            r["end"],
                        )
                with c_del:
                    if st.button(T('Remove from list'), key=f"del_{idx}", width="stretch"):
                        st.session_state.cut_ranges.pop(idx)
                        st.session_state.pop("range_preview", None)
                        st.rerun()
                preview = st.session_state.get("range_preview")
                if preview and preview[0] == source_id and preview[1] == idx:
                    st.iframe(range_player_html(preview[2], preview[3]), height=55)
        else:
            st.caption(T('Added ranges and titles appear here.'))

        if PUBLIC_MODE:
            st.markdown(f"### {T('④ Download the split tracks')}")
            st.caption(T('Files are temporary. Download them before closing or resetting the page.'))
            output_dir = session_directory(st.session_state)
        else:
            st.markdown(f"### {T('④ Choose where to save')}")
            save_mode = st.radio(T('Save location'), ['Default', 'Choose a folder'], horizontal=True, key="save_mode", format_func=T)
            if save_mode == 'Choose a folder':
                dir_col, browse_col = st.columns([4, 1])
                with dir_col:
                    st.text_input(T('Parent folder for saved files'), key="custom_dir", placeholder=r"C:\Music")
                with browse_col:
                    st.markdown("<div style='height: 1.7rem'></div>", unsafe_allow_html=True)
                    st.button(T('Browse'), on_click=choose_folder, width="stretch")
                if st.session_state.get("folder_picker_error"):
                    st.error(T('Could not open the folder picker: {error}', error=st.session_state.folder_picker_error))
            try:
                output_dir = output_directory(APP_DIR, save_mode, st.session_state.get("custom_dir", ""))
                st.caption(T('Save folder: {path}', path=output_dir))
            except (OSError, ValueError) as error:
                output_dir = None
                st.error(T(str(error)))

        if st.button(
            T('Cut and save'),
            type="primary",
            width="stretch",
            disabled=not ranges_to_save or output_dir is None,
        ):
            try:
                numbered_ranges = [
                    {**item, 'track_order': st.session_state.completed_in_session + idx + 1}
                    for idx, item in enumerate(ranges_to_save)
                ]
                saved = save_cuts(audio, numbered_ranges, uploaded_file.name, output_dir)
                st.session_state.completed_in_session += len(saved)
                saved_end = max(item["end"] for item in ranges_to_save)
                st.session_state.saved_through = saved_end
                st.session_state.cut_ranges = []
                if saved_end < duration_sec:
                    st.session_state.start_input = format_time(saved_end)
                    st.session_state.end_input = format_time(duration_sec)
                    st.session_state.cut_slider = (saved_end, duration_sec)
                    st.session_state.cut_title = f"{st.session_state.source_title}_{st.session_state.completed_in_session + 1:02d}"
                st.session_state.pop("range_notice", None)
                st.session_state.save_notice = (len(saved), str(output_dir))
                st.balloons()
                st.rerun()
            except Exception as error:
                st.error(T('Save failed: {error}', error=T(str(error))))
        if st.session_state.get("save_notice"):
            saved_count, saved_path = st.session_state.save_notice
            if PUBLIC_MODE:
                st.success(T('Created {count} tracks. Download them below.', count=saved_count))
            else:
                st.success(T('Saved {count} tracks to {path}. Return to step ③ to continue with this audio.', count=saved_count, path=saved_path))

        st.markdown(f"### {T('⑤ Next task')}")
        st.button(T('Start a new task (reset)'), on_click=reset_work, type="primary", width="stretch")

    except Exception as e:
        st.error(T('Audio processing failed: {error}', error=T(str(e))))

if output_dir is None:
    if PUBLIC_MODE:
        output_dir = session_directory(st.session_state)
    else:
        try:
            output_dir = output_directory(
                APP_DIR,
                st.session_state.get("save_mode", 'Default'),
                st.session_state.get("custom_dir", ""),
            )
        except (OSError, ValueError):
            output_dir = None

if output_dir is not None:
    if PUBLIC_MODE:
        downloadable_clips = list_saved_clips(output_dir)
        if downloadable_clips:
            st.markdown(f"### {T('Download an MP3 file')}")
            download_clip = st.selectbox(
                T('Select a file to download'), downloadable_clips,
                format_func=lambda path: path.name,
                key="download_clip",
            )
            st.download_button(
                T('Download selected MP3'),
                data=download_clip.read_bytes(),
                file_name=download_clip.name,
                mime="audio/mpeg",
                width="stretch",
                on_click="ignore",
            )
    else:
        if st.button(T('📂 Open save folder'), key="open_output_folder", type="secondary", width="stretch"):
            try:
                open_folder(output_dir)
                st.session_state.pop("open_folder_error", None)
            except OSError as error:
                st.session_state.open_folder_error = str(error)
        if st.session_state.get("open_folder_error"):
            st.error(T('Could not open the save folder: {error}', error=st.session_state.open_folder_error))

    st.markdown(f"### {T('✂️ Edit a saved clip')}")
    st.caption(T('Select a range in a saved MP3. The original remains; the revision is saved with a new number. The range cannot extend outside the saved file.'))
    if st.session_state.get("clip_save_notice"):
        st.success(T('Saved revision: {name}', name=st.session_state.clip_save_notice))
    saved_clips = list_saved_clips(output_dir)
    if saved_clips:
        selected_clip = st.selectbox(
            T('MP3 to edit'), saved_clips,
            format_func=lambda path: str(path.relative_to(output_dir)),
        )
        try:
            if st.session_state.get("clip_selected_path") != str(selected_clip):
                selected_duration = int(clip_duration(selected_clip) * 1000) / 1000
                if selected_duration <= 0:
                    raise ValueError(T('Could not determine the clip duration.'))
                st.session_state.clip_selected_path = str(selected_clip)
                st.session_state.clip_duration_seconds = selected_duration
                st.session_state.clip_start = format_time(0)
                st.session_state.clip_end = format_time(selected_duration)
                st.session_state.clip_slider = (0.0, selected_duration)
                clip_stem = selected_clip.stem
                st.session_state.clip_title = re.sub(r"^\d+_", "", clip_stem)
            duration = st.session_state.clip_duration_seconds
            st.caption(T('Clip duration: {duration}', duration=format_time(duration)))
            start_col, end_col = st.columns(2)
            with start_col:
                st.text_input(T('Revised start'), key="clip_start", on_change=sync_clip_slider)
            with end_col:
                st.text_input(T('Revised end'), key="clip_end", on_change=sync_clip_slider)
            st.slider(
                T('Revision range'), min_value=0.0, max_value=duration,
                step=0.001, key="clip_slider", on_change=sync_clip_inputs,
            )
            st.text_input(T('Revised title'), key="clip_title")
            clip_start = read_input_time(st.session_state.clip_start)
            clip_end = read_input_time(st.session_state.clip_end)
            valid_clip = (
                clip_start is not None and clip_end is not None
                and 0 <= clip_start < clip_end <= duration
            )
            if not valid_clip:
                st.error(T("Set the start and end positions within the file duration."))
            start_preview_col, end_preview_col = st.columns(2)
            with start_preview_col:
                preview_start_clicked = st.button(T('▶ Preview start'), disabled=not valid_clip, width="stretch")
            with end_preview_col:
                preview_end_clicked = st.button(T('▶ Preview end'), disabled=not valid_clip, width="stretch")
            save_col = st.container()
            with save_col:
                save_clicked = st.button(T('✂️ Save revision'), disabled=not valid_clip, type="primary", width="stretch")
            if preview_start_clicked:
                st.audio(
                    preview_segment(selected_clip, clip_start, min(clip_end, clip_start + 5)),
                    format="audio/wav",
                )
            if preview_end_clicked:
                st.audio(
                    preview_segment(selected_clip, max(clip_start, clip_end - 5), clip_end),
                    format="audio/wav",
                )
            if save_clicked:
                record = save_revised_clip(
                    output_dir, selected_clip, clip_start, clip_end, st.session_state.clip_title,
                )
                st.session_state.clip_save_notice = record['filename']
                st.rerun()
        except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
            st.error(T('Clip editing failed: {error}', error=T(str(error))))
    else:
        st.caption(T('No saved MP3 files found.'))

st.markdown(f"### {T('📋 Work history')}")
try:
    history = read_history(output_dir) if output_dir is not None else []
    if history:
        counts_by_source = {}
        numbered_history = []
        for item in history:
            source_name = item['source_file']
            counts_by_source[source_name] = counts_by_source.get(source_name, 0) + 1
            song_order = item.get('track_order', counts_by_source[source_name])
            numbered_history.append({**item, 'track_label': T('Track {number}', number=song_order)})
        history_columns = {
            'Track': 'track_label',
            'Number': 'number',
            'Title': 'title',
            'Source file': 'source_file',
            'Start (sec)': 'start_seconds',
            'End (sec)': 'end_seconds',
            'Saved at': 'saved_at',
            'File name': 'filename',
        }
        displayed_history = [
            {T(column): item.get(field, "") for column, field in history_columns.items()}
            for item in reversed(numbered_history)
        ]
        st.dataframe(
            displayed_history,
            width="stretch",
            hide_index=True,
            column_order=[T(column) for column in history_columns],
        )
        by_number = {int(item['number']): item for item in history}
        selected_number = st.selectbox(
            T('History entry to remove'),
            options=list(reversed(by_number)),
            format_func=lambda number: f"{number:04d}  {by_number[number]['title']}  {by_number[number]['filename']}",
        )
        if st.button(T('Remove selected history entry'), type="secondary"):
            if delete_history_entry(output_dir, selected_number):
                st.rerun()
    else:
        st.caption(T('No saved work yet.'))
except (OSError, ValueError, KeyError) as error:
    st.error(T('Could not load work history: {error}', error=T(str(error))))

# ---------------------------------------------------------
# Application workflow.
# ---------------------------------------------------------
st.markdown("<hr style='margin: 15px 0 10px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align: center; color: #94a3b8; font-size: 0.85rem; font-weight: 500; margin-bottom: 5px;'>"
    "© 2026 MUSIC CUTTER"
    "</div>",
    unsafe_allow_html=True,
)


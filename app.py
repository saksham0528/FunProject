"""Streamlit user interface for the Smart Attendance Management System."""

from __future__ import annotations

import base64
from datetime import date, timedelta
from io import StringIO
from pathlib import Path

import pandas as pd
import streamlit as st
from pymongo.errors import DuplicateKeyError, PyMongoError

from analytics import build_attendance_summary
from db import add_student, get_all_students, get_attendance_records, mark_attendance


class Main:
    """Encapsulates the Streamlit app flow for the attendance dashboard."""

    @staticmethod
    def _highlight_defaulters(row: pd.Series, total_sessions: int) -> list[str]:
        percentage = row["Attendance %"]
        color = "background-color: #fee2e2; color: #991b1b" if (
            total_sessions and percentage < 75
        ) else ""
        return [color] * len(row.index)

    @staticmethod
    def _inject_styles() -> None:
        st.markdown(
            """
            <style>
            @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
            :root {
                --ink: #0f172a;
                --muted: #475569;
                --app-bg: #f8fafc;
                --card-bg: #ffffff;
                --border: #e2e8f0;
                --primary: #2563eb;
                --success: #059669;
                --box-blue: #2563eb;
                --box-blue-hover: #1d4ed8;
                --box-text-white: #fff;
                --date-text-blue: #2563eb;
                --calendar-black: #000;
                --icon-color: #172033;
                --mint: #dff7ed;
            }
            html, body, .stApp { font-family: 'DM Sans', sans-serif; color: var(--ink); }
            [class*="css"] { font-family: 'DM Sans', sans-serif; }
            h1, h2, h3, h4, h5, h6 { font-family: 'Space Grotesk', sans-serif; color: var(--ink) !important; font-weight: 700 !important; }
            .stApp { background: linear-gradient(145deg, #f8fbff 0%, #eef5ff 48%, #f7fbf8 100%); color: var(--ink) !important; }
            .stApp svg,
            .stApp [data-testid="stIconMaterial"],
            .stApp [class*="material-symbols"] {
                color: var(--icon-color) !important;
                opacity: 1 !important;
                visibility: visible !important;
                font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons", sans-serif !important;
                font-style: normal !important;
                font-weight: 400 !important;
                font-size: 1.25rem !important;
                line-height: 1 !important;
                font-variation-settings: "FILL" 1, "wght" 400, "GRAD" 0, "opsz" 24;
            }
            .stApp svg { display: inline-block !important; }
            .stApp svg path,
            .stApp svg line,
            .stApp svg polyline,
            .stApp svg circle {
                opacity: 1 !important;
                visibility: visible !important;
            }
            .stApp [data-testid="stMarkdownContainer"] p,
            .stApp [data-testid="stMarkdownContainer"] li,
            .stApp label,
            .stApp legend,
            .stApp [data-testid="stWidgetLabel"] p,
            .stApp [data-testid="stWidgetLabel"] label,
            .stApp [role="tab"] { color: var(--ink) !important; font-weight: 600 !important; }
            .stApp [role="tab"][aria-selected="true"] { color: var(--primary) !important; }
            .stApp [data-testid="stCaptionContainer"] *,
            .stApp [data-testid="stAlert"] * { color: var(--muted) !important; }
            .stApp [data-testid="stCheckbox"] label,
            .stApp [data-testid="stCheckbox"] label p,
            .stApp [data-testid="stCheckbox"] label span { color: var(--ink) !important; font-weight: 700 !important; }
            .stApp [data-testid="stAlert"] { background: var(--card-bg) !important; border: 1px solid var(--border) !important; color: var(--ink) !important; }
            .stApp input, .stApp textarea, .stApp select {
                color: var(--box-text-white) !important;
                background-color: var(--box-blue) !important;
                border: 2px solid var(--box-blue-hover) !important;
                font-weight: 700 !important;
                caret-color: var(--box-text-white) !important;
            }
            .stApp input:focus, .stApp textarea:focus, .stApp select:focus {
                background-color: var(--box-blue-hover) !important;
                border-color: #1e3a8a !important;
                box-shadow: 0 0 0 2px #93c5fd !important;
            }
            .stApp input::placeholder, .stApp textarea::placeholder { color: var(--box-text-white) !important; opacity: .9; }
            .stApp [data-baseweb="input"] { background-color: var(--box-blue) !important; }
            .stApp .stDateInput [role="group"][aria-label="Attendance date"],
            .stApp .stDateInput [role="group"][aria-label="Attendance date"] [data-type],
            .stApp .stDateInput [role="group"][aria-label="Attendance date"] [data-type="literal"] {
                color: var(--box-text-white) !important;
                background-color: var(--calendar-black) !important;
                font-weight: 700 !important;
            }
            .stApp .stDateInput [role="group"][aria-label="Attendance date"] {
                border: 2px solid var(--calendar-black) !important;
                border-radius: 8px;
            }
            .stApp [data-baseweb="calendar"],
            .stApp [data-baseweb="calendar"] *,
            .stApp [data-baseweb="calendar"] button,
            .stApp [data-baseweb="calendar"] [role="gridcell"] {
                color: var(--box-text-white) !important;
                font-weight: 700 !important;
            }
            .stApp [role="dialog"] [role="gridcell"],
            .stApp [role="dialog"] [role="gridcell"] button,
            .stApp [role="dialog"] [role="gridcell"] * {
                color: var(--box-text-white) !important;
                font-weight: 700 !important;
            }
            .stApp [data-baseweb="calendar"] {
                background: var(--calendar-black) !important;
            }
            .stApp [role="dialog"] {
                background: var(--calendar-black) !important;
                color: var(--box-text-white) !important;
            }
            .stApp [role="dialog"] [role="grid"],
            .stApp [role="dialog"] [role="gridcell"] button {
                background: var(--calendar-black) !important;
                color: var(--box-text-white) !important;
            }
            .stApp [data-baseweb="calendar"] button:hover,
            .stApp [data-baseweb="calendar"] [aria-selected="true"],
            .stApp [data-baseweb="calendar"] [data-highlighted="true"],
            .stApp [role="dialog"] [role="gridcell"] button:hover,
            .stApp [role="dialog"] [role="gridcell"][aria-selected="true"] {
                background: var(--box-blue-hover) !important;
                color: var(--box-text-white) !important;
            }
            /* Streamlit renders the calendar popup in a portal; keep this selector global. */
            [role="dialog"] [role="application"],
            [role="dialog"] [role="application"] *,
            [role="dialog"] [role="gridcell"],
            [role="dialog"] [role="gridcell"] button {
                color: var(--box-text-white) !important;
                font-weight: 700 !important;
            }
            [role="dialog"] [role="application"],
            [role="dialog"] [role="grid"],
            [role="dialog"] [role="gridcell"] button {
                background: var(--calendar-black) !important;
            }
            [role="dialog"] [role="gridcell"] button:hover,
            [role="dialog"] [role="gridcell"][aria-selected="true"] button,
            [role="dialog"] [role="gridcell"] button[aria-current="date"] {
                background: var(--box-blue-hover) !important;
                color: var(--box-text-white) !important;
            }
            [role="dialog"] [role="gridcell"] button:disabled {
                color: var(--box-text-white) !important;
                opacity: .8 !important;
            }
            .quadrant-box {
                background: var(--box-blue);
                color: var(--box-text-white);
            }
            .quadrant-box:hover, .quadrant-box:focus, .quadrant-box[aria-selected="true"] {
                background: var(--box-blue-hover);
                color: var(--box-text-white);
            }
            [data-testid="stHeader"] { background: transparent; }
            [data-testid="stSidebar"] { background: var(--card-bg); border-right: 1px solid var(--border); color: var(--ink) !important; }
            [data-testid="stSidebar"] *, [data-testid="stSidebar"] p,
            [data-testid="stSidebar"] label { color: var(--ink) !important; font-weight: 600 !important; }
            [data-testid="stSidebar"] [data-testid="stImage"] button,
            [data-testid="stSidebar"] [data-testid="stImage"] [data-testid="stElementToolbar"],
            [data-testid="stSidebar"] button[aria-label="Fullscreen"],
            [data-testid="stSidebar"] button[title="Fullscreen"] {
                display: none !important;
            }
            .stulib-logo {
                display: block;
                width: 128px;
                height: auto;
                margin: 0 auto .6rem;
                border-radius: 18px;
            }
            .stulib-loader {
                position: fixed;
                z-index: 999999;
                inset: 0;
                display: grid;
                place-items: center;
                overflow: hidden;
                background: #081428;
                color: #fff;
                isolation: isolate;
                pointer-events: none;
                animation: stulib-loader-out .75s cubic-bezier(.65, 0, .35, 1) 1.15s forwards;
            }
            .stulib-loader.is-done {
                animation: stulib-loader-out .75s cubic-bezier(.65, 0, .35, 1) 0s forwards;
            }
            .stulib-loader::before,
            .stulib-loader::after {
                position: absolute;
                content: "";
                border-radius: 50%;
                pointer-events: none;
            }
            .stulib-loader::before {
                width: min(74vw, 540px);
                aspect-ratio: 1;
                background: radial-gradient(circle, #38bdf840 0%, #38bdf818 34%, transparent 70%);
                filter: blur(16px);
                animation: stulib-breathe 2.8s ease-in-out infinite;
            }
            .stulib-loader::after {
                width: min(88vw, 760px);
                aspect-ratio: 1;
                border: 1px solid #38bdf81c;
                box-shadow: 0 0 80px #38bdf40d inset;
            }
            .stulib-loader-content {
                position: relative;
                z-index: 1;
                display: flex;
                width: min(88vw, 420px);
                flex-direction: column;
                align-items: center;
                gap: 1.2rem;
                text-align: center;
            }
            .stulib-loader-logo-wrap {
                position: relative;
                display: grid;
                width: clamp(132px, 31vw, 190px);
                aspect-ratio: 1;
                place-items: center;
                animation: stulib-float 3.2s ease-in-out infinite;
            }
            .stulib-loader-logo-wrap::before {
                position: absolute;
                inset: -15px;
                border: 3px solid transparent;
                border-top-color: #38bdf8;
                border-right-color: #34d399;
                border-radius: 50%;
                content: "";
                animation: stulib-spin 1.65s linear infinite;
                filter: drop-shadow(0 0 9px #38bdf8aa);
            }
            .stulib-loader-logo-wrap::after {
                position: absolute;
                inset: -5px;
                border: 1px solid #38bdf84d;
                border-radius: 50%;
                content: "";
                animation: stulib-spin 3.4s linear infinite reverse;
            }
            .stulib-loader-logo {
                width: 100%;
                height: 100%;
                border: 6px solid #fff;
                border-radius: 26%;
                object-fit: cover;
                box-shadow: 0 0 28px #38bdf866;
            }
            .stulib-loader-bars {
                display: flex;
                align-items: end;
                justify-content: center;
                gap: 7px;
                height: 44px;
            }
            .stulib-loader-bars span {
                display: block;
                width: 10px;
                height: 18px;
                border-radius: 5px 5px 2px 2px;
                background: linear-gradient(180deg, #38bdf8, #34d399);
                box-shadow: 0 0 12px #38bdf855;
                animation: stulib-bar 1.15s ease-in-out infinite;
            }
            .stulib-loader-bars span:nth-child(2) { animation-delay: .16s; }
            .stulib-loader-bars span:nth-child(3) { animation-delay: .32s; }
            .stulib-loader-bars span:nth-child(4) { animation-delay: .48s; }
            .stulib-loader-bars span:nth-child(5) { animation-delay: .64s; }
            .stulib-loader-text {
                margin: 0;
                color: #fff !important;
                font: 700 clamp(.9rem, 2.5vw, 1.05rem)/1.4 'DM Sans', sans-serif;
                letter-spacing: .04em;
                animation: stulib-pulse 1.8s ease-in-out infinite;
            }
            .stulib-loader-dots::after {
                content: "...";
                display: inline-block;
                width: 1.2em;
                text-align: left;
                animation: stulib-dots 1.2s steps(4, end) infinite;
            }
            @keyframes stulib-float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
            @keyframes stulib-spin { to { transform: rotate(360deg); } }
            @keyframes stulib-breathe { 0%, 100% { transform: scale(.88); opacity: .65; } 50% { transform: scale(1.08); opacity: 1; } }
            @keyframes stulib-bar { 0%, 100% { height: 18px; opacity: .65; } 50% { height: 42px; opacity: 1; } }
            @keyframes stulib-pulse { 0%, 100% { opacity: .55; } 50% { opacity: 1; } }
            @keyframes stulib-dots { 0% { width: 0; } 50% { width: 1.2em; } 100% { width: 0; } }
            @keyframes stulib-loader-out { to { opacity: 0; visibility: hidden; transform: scale(1.06); } }
            @media (max-width: 520px) {
                .stulib-loader-content { gap: .9rem; }
                .stulib-loader-logo-wrap::before { inset: -10px; }
                .stulib-loader-bars { transform: scale(.9); }
            }
            @media (prefers-reduced-motion: reduce) {
                .stulib-loader-logo-wrap,
                .stulib-loader-logo-wrap::before,
                .stulib-loader-logo-wrap::after,
                .stulib-loader::before,
                .stulib-loader-bars span,
                .stulib-loader-text,
                .stulib-loader-dots::after { animation: none !important; }
                .stulib-loader { animation-delay: .2s; }
            }
            /* Visual treatment adapted from the provided StuLib loading animation. */
            .stulib-loader {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                background: #081428;
            }
            .stulib-loader-glow {
                position: absolute;
                width: 220px;
                height: 220px;
                border-radius: 50%;
                background: #2563eb;
                filter: blur(90px);
                opacity: .3;
                animation: stulib-source-glow 3s ease-in-out infinite alternate;
            }
            .stulib-loader-logo-wrap {
                width: 92px;
                height: 92px;
                display: grid;
                place-items: center;
                animation: stulib-source-float 2.4s ease-in-out infinite;
            }
            .stulib-loader-logo-wrap::before,
            .stulib-loader-logo-wrap::after { display: none; }
            .stulib-loader-ring {
                position: absolute;
                inset: 0;
                border: 2px solid #1d3558;
                border-top-color: #38bdf8;
                border-right-color: #34d399;
                border-radius: 50%;
                animation: stulib-source-spin 2s linear infinite;
            }
            .stulib-loader-logo {
                width: 66px;
                height: 66px;
                border: 0;
                border-radius: 18px;
                object-fit: cover;
                box-shadow: 0 8px 30px #2563eb55;
            }
            .stulib-loader-name {
                z-index: 1;
                margin-top: 13px;
                color: #fff !important;
                font: 750 23px/1.2 system-ui, sans-serif;
                letter-spacing: .3px;
            }
            .stulib-loader-name span { color: #38bdf8 !important; }
            .stulib-loader-bars {
                height: 36px;
                display: flex;
                align-items: end;
                gap: 6px;
                margin-top: 18px;
            }
            .stulib-loader-bars span {
                width: 8px;
                height: 12px;
                border-radius: 4px;
                background: linear-gradient(#34d399, #2563eb);
                animation: stulib-source-bars 1s ease-in-out infinite alternate;
            }
            .stulib-loader-bars span:nth-child(2) { animation-delay: .15s; }
            .stulib-loader-bars span:nth-child(3) { animation-delay: .3s; }
            .stulib-loader-bars span:nth-child(4) { animation-delay: .45s; }
            .stulib-loader-bars span:nth-child(5) { animation-delay: .6s; }
            .stulib-loader-subtitle {
                z-index: 1;
                margin-top: 5px;
                color: #94a3b8 !important;
                font: 400 12px/1.4 system-ui, sans-serif;
                animation: stulib-source-pulse 1.7s ease-in-out infinite;
            }
            @keyframes stulib-source-float { 50% { transform: translateY(-10px); } }
            @keyframes stulib-source-spin { to { transform: rotate(360deg); } }
            @keyframes stulib-source-bars { to { height: 34px; } }
            @keyframes stulib-source-glow { to { transform: scale(1.3); opacity: .5; } }
            @keyframes stulib-source-pulse { 50% { opacity: .45; } }
            @media (prefers-reduced-motion: reduce) {
                .stulib-loader-glow,
                .stulib-loader-logo-wrap,
                .stulib-loader-ring,
                .stulib-loader-bars span,
                .stulib-loader-subtitle { animation: none !important; }
            }
            .hero { padding: 1.25rem 1.4rem; border-radius: 22px; background: linear-gradient(115deg, #dbeafe, #dcfce7); color: var(--ink); box-shadow: 0 12px 30px #1e3a5f20; margin-bottom: 1.25rem; }
            .hero h1 { color: var(--ink) !important; margin: 0; font-size: clamp(2rem, 5vw, 3.2rem); letter-spacing: -0.05em; }
            .hero p { color: var(--ink) !important; margin: 0.45rem 0 0; font-size: 1.05rem; }
            .kpi { background: rgba(255,255,255,.92); border: 1px solid var(--border); border-radius: 16px; padding: 1rem 1.1rem; min-height: 108px; box-shadow: 0 8px 20px #1e3a5f0c; }
            .kpi-label, .kpi-value, .kpi-note { color: var(--ink); font-weight: 700; }
            .kpi-label { font-size: .8rem; text-transform: uppercase; letter-spacing: .08em; }
            .kpi-value { font: 700 1.9rem 'Space Grotesk', sans-serif; margin-top: .3rem; }
            .kpi-note { font-size: .8rem; margin-top: .2rem; }
            div[data-testid="stForm"] { background: rgba(255,255,255,.92); border: 1px solid var(--border); border-radius: 18px; padding: 1.1rem; color: var(--ink) !important; }
            div[data-testid="stForm"] [data-testid="stMarkdownContainer"] *,
            div[data-testid="stForm"] [data-testid="stWidgetLabel"] * { color: var(--ink) !important; }
            div[data-testid="stFormSubmitButton"] button,
            div[data-testid="stFormSubmitButton"] button p {
                background: var(--box-blue) !important;
                color: var(--box-text-white) !important;
                border: 2px solid var(--box-blue-hover) !important;
                font-weight: 700 !important;
            }
            div[data-testid="stFormSubmitButton"] button:hover,
            div[data-testid="stFormSubmitButton"] button:focus {
                background: var(--box-blue-hover) !important;
                color: var(--box-text-white) !important;
                box-shadow: 0 0 0 2px #93c5fd !important;
            }
            /* Keep interactive dataframe/chart toolbar icons visible and readable. */
            [data-testid="stElementToolbar"] {
                opacity: 1 !important;
                visibility: visible !important;
                background: var(--calendar-black) !important;
                border-radius: 8px;
            }
            [data-testid="stElementToolbar"] button,
            [data-testid="stElementToolbar"] button p,
            [data-testid="stElementToolbar"] button span {
                color: var(--box-text-white) !important;
                background: transparent !important;
                font-weight: 700 !important;
                cursor: pointer !important;
            }
            [data-testid="stElementToolbar"] svg,
            [data-testid="stElementToolbar"] [data-testid="stIconMaterial"],
            [data-testid="stElementToolbar"] [class*="material-symbols"] {
                color: var(--box-text-white) !important;
                opacity: 1 !important;
                visibility: visible !important;
                font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons", sans-serif !important;
                font-style: normal !important;
                font-weight: 400 !important;
                font-size: 1.25rem !important;
                line-height: 1 !important;
                font-variation-settings: "FILL" 1, "wght" 400, "GRAD" 0, "opsz" 24;
            }
            [data-testid="stElementToolbar"] button:hover,
            [data-testid="stElementToolbar"] button:focus-visible {
                color: var(--box-text-white) !important;
                background: var(--box-blue-hover) !important;
            }
            [data-testid="stElementToolbar"] button *,
            [data-testid="stElementToolbar"] button *::before,
            [data-testid="stElementToolbar"] button *::after {
                background: transparent !important;
            }
            [data-testid="stElementToolbar"] svg {
                color: var(--box-text-white) !important;
                fill: none !important;
                stroke: var(--box-text-white) !important;
            }
            [data-testid="stElementToolbar"] svg path {
                fill: var(--box-text-white) !important;
                stroke: none !important;
            }
            [data-testid="stElementToolbar"] svg line,
            [data-testid="stElementToolbar"] svg polyline,
            [data-testid="stElementToolbar"] svg circle {
                fill: none !important;
                stroke: var(--box-text-white) !important;
            }
            [data-testid="stElementToolbar"] svg rect {
                fill: none !important;
                stroke: var(--box-text-white) !important;
            }
            [data-testid="stElementToolbar"] svg use {
                color: var(--box-text-white) !important;
                fill: var(--box-text-white) !important;
            }
            /* Stable fallback glyphs keep every toolbar action visible if an icon font is unavailable. */
            [data-testid="stElementToolbar"] button[aria-label],
            [data-testid="stElementToolbar"] button[title] {
                position: relative;
                font-size: 0 !important;
            }
            [data-testid="stElementToolbar"] button[aria-label]::before,
            [data-testid="stElementToolbar"] button[title]::before {
                color: var(--box-text-white) !important;
                font-size: 1.25rem !important;
                line-height: 1 !important;
                font-family: 'Segoe UI Symbol', 'Noto Sans Symbols', sans-serif !important;
            }
            [data-testid="stElementToolbar"] button[aria-label*="Show/hide columns"]::before,
            [data-testid="stElementToolbar"] button[title*="Show/hide columns"]::before { content: '▦'; }
            [data-testid="stElementToolbar"] button[aria-label*="Download"]::before,
            [data-testid="stElementToolbar"] button[title*="Download"]::before { content: '⇩'; }
            [data-testid="stElementToolbar"] button[aria-label="Search"]::before,
            [data-testid="stElementToolbar"] button[title="Search"]::before { content: '⌕'; }
            [data-testid="stElementToolbar"] button[aria-label="Fullscreen"]::before,
            [data-testid="stElementToolbar"] button[title="Fullscreen"]::before { content: '⛶'; }
            [data-testid="stElementToolbar"] button[aria-label="Show data"]::before,
            [data-testid="stElementToolbar"] button[title="Show data"]::before { content: '▤'; }
            [data-testid="stElementToolbar"] button[aria-label*="Copy"]::before,
            [data-testid="stElementToolbar"] button[title*="Copy"]::before { content: '⧉'; }
            [data-testid="stElementToolbar"] button svg,
            [data-testid="stElementToolbar"] button [data-testid="stIconMaterial"],
            [data-testid="stElementToolbar"] button [class*="material-symbols"] {
                display: none !important;
            }
            [data-testid="stElementToolbar"] button[aria-label]::after,
            [data-testid="stElementToolbar"] button[title]::after {
                content: attr(aria-label);
                position: absolute;
                z-index: 20;
                left: 50%;
                top: calc(100% + 8px);
                transform: translateX(-50%);
                width: max-content;
                max-width: 220px;
                padding: 0.35rem 0.55rem;
                border-radius: 6px;
                background: var(--calendar-black);
                color: var(--box-text-white) !important;
                font: 700 0.75rem/1.2 'DM Sans', sans-serif !important;
                pointer-events: none;
                opacity: 0;
                visibility: hidden;
                transition: opacity 120ms ease;
            }
            [data-testid="stElementToolbar"] button[aria-label]:hover::after,
            [data-testid="stElementToolbar"] button[aria-label]:focus-visible::after,
            [data-testid="stElementToolbar"] button[title]:hover::after,
            [data-testid="stElementToolbar"] button[title]:focus-visible::after {
                opacity: 1;
                visibility: visible;
            }
            /* Keep normal controls readable, while reserving white text for blue interactive surfaces. */
            .stApp button,
            .stApp button p,
            .stApp button span { color: var(--ink) !important; font-weight: 700 !important; }
            .stApp [data-testid="stFormSubmitButton"] button,
            .stApp [data-testid="stFormSubmitButton"] button p,
            .stApp [data-testid="stFormSubmitButton"] button span,
            .stApp [data-testid="stDownloadButton"] button,
            .stApp [data-testid="stDownloadButton"] button p,
            .stApp [data-testid="stDownloadButton"] button span { color: var(--box-text-white) !important; }
            /* Quick date actions use the shared blue interactive-box treatment. */
            .stApp .st-key-quick_today button,
            .stApp .st-key-quick_today button *,
            .stApp .st-key-quick_yesterday button,
            .stApp .st-key-quick_yesterday button *,
            .stApp .st-key-quick_tomorrow button,
            .stApp .st-key-quick_tomorrow button *,
            .stApp [data-testid="stSidebar"] .st-key-refresh_data button,
            .stApp [data-testid="stSidebar"] .st-key-refresh_data button * {
                color: var(--box-text-white) !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def _kpi(label: str, value: str, note: str = "") -> None:
        st.markdown(
            f'<div class="kpi"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>',
            unsafe_allow_html=True,
        )

    @staticmethod
    def _render_loader(logo_path: Path) -> None:
        """Render one lightweight, self-dismissed loader for each app render."""
        if not logo_path.exists():
            return

        logo_data = base64.b64encode(logo_path.read_bytes()).decode("ascii")
        st.markdown(
            f"""
            <div class="stulib-loader" id="stulib-loader" role="status" aria-live="polite">
                <div class="stulib-loader-glow" aria-hidden="true"></div>
                <div class="stulib-loader-logo-wrap">
                    <div class="stulib-loader-ring" aria-hidden="true"></div>
                    <img class="stulib-loader-logo" src="data:image/png;base64,{logo_data}" alt="StuLib">
                </div>
                <div class="stulib-loader-name">Stu<span>Lib</span></div>
                <div class="stulib-loader-bars" aria-hidden="true">
                    <span></span><span></span><span></span><span></span><span></span>
                </div>
                <div class="stulib-loader-subtitle">Preparing your dashboard...</div>
            </div>
            <script>
            (() => {{
                const loader = document.getElementById("stulib-loader");
                if (!loader) return;
                const finish = () => {{
                    loader.classList.add("is-done");
                    window.setTimeout(() => loader.remove(), 900);
                }};
                window.addEventListener("beforeunload", () => {{
                    loader.classList.remove("is-done");
                    loader.style.opacity = "1";
                    loader.style.visibility = "visible";
                }}, {{ once: true }});
                window.setTimeout(finish, 1050);
                window.setTimeout(finish, 8000);
            }})();
            </script>
            """,
            unsafe_allow_html=True,
        )

    def render_add_student_tab(self) -> None:
        st.subheader("Add a student")
        with st.form("add_student_form", clear_on_submit=True):
            roll_no = st.text_input("Roll number", placeholder="CS101")
            name = st.text_input("Student name", placeholder="Riya Sharma")
            class_name = st.text_input("Class", placeholder="AIDS-2A")
            add_submitted = st.form_submit_button("Add student")

        if add_submitted:
            try:
                add_student(roll_no, name, class_name)
            except ValueError as exc:
                st.error(str(exc))
            except DuplicateKeyError:
                st.error("That roll number is already in the student list.")
            except (PyMongoError, RuntimeError) as exc:
                st.error(
                    "Could not save the student. Check the MongoDB connection and try again "
                    f"({type(exc).__name__})."
                )
            else:
                st.success(f"Added {name.strip()} to the student list.")

    def render_attendance_tab(self) -> None:
        st.subheader("Record attendance")
        try:
            students = get_all_students()
        except (PyMongoError, RuntimeError) as exc:
            st.error(
                "Could not load students. Check MONGO_URI, Atlas network access, and "
                f"database credentials ({type(exc).__name__})."
            )
            return

        if not students:
            st.info("Add students before recording attendance.")
            return

        def set_attendance_date(selected_date: date) -> None:
            st.session_state["attendance_date"] = selected_date

        st.markdown("### Choose a class date")
        quick_today, quick_yesterday, quick_tomorrow = st.columns(3)
        with quick_today:
            st.button(
                "Today",
                key="quick_today",
                use_container_width=True,
                on_click=set_attendance_date,
                args=(date.today(),),
            )
        with quick_yesterday:
            st.button(
                "Yesterday",
                key="quick_yesterday",
                use_container_width=True,
                on_click=set_attendance_date,
                args=(date.today() - timedelta(days=1),),
            )
        with quick_tomorrow:
            st.button(
                "Tomorrow",
                key="quick_tomorrow",
                use_container_width=True,
                on_click=set_attendance_date,
                args=(date.today() + timedelta(days=1),),
            )

        selected_date = st.date_input(
            "Attendance date",
            value=st.session_state.get("attendance_date", date.today()),
            key="attendance_date",
            help="Pick any date from the calendar or use a quick date button.",
        )
        weekday = selected_date.strftime("%A, %d %B %Y")
        if selected_date.weekday() >= 5:
            st.warning(f"{weekday} is a weekend. Double-check that a class was held.")
        else:
            st.caption(f"Selected session: {weekday}")

        with st.form("mark_attendance_form"):
            st.caption("Students are marked present by default. Uncheck anyone absent.")
            present_by_id: dict[str, bool] = {}
            for student in students:
                left, right = st.columns([2, 1])
                left.write(f"**{student['roll_no']}** — {student['name']}")
                present_by_id[str(student["_id"])] = right.checkbox(
                    "Present",
                    value=True,
                    key=f"present_{student['_id']}_{selected_date.isoformat()}",
                )
            attendance_submitted = st.form_submit_button("Save attendance")

        if attendance_submitted:
            saved_count = 0
            try:
                for student in students:
                    student_id = str(student["_id"])
                    status = "present" if present_by_id[student_id] else "absent"
                    mark_attendance(student["_id"], selected_date, status)
                    saved_count += 1
            except (PyMongoError, RuntimeError, ValueError) as exc:
                if saved_count:
                    st.warning(
                        f"Attendance was saved for {saved_count} of {len(students)} "
                        "students. Submit again to safely update the whole class."
                    )
                st.error(
                    "Could not save all attendance records. Check the MongoDB "
                    f"connection and try again ({type(exc).__name__})."
                )
            else:
                st.success(
                    f"Saved attendance for {len(students)} students on "
                    f"{selected_date.isoformat()}."
                )

    def render_reports_tab(self) -> None:
        st.subheader("Attendance report")
        try:
            report_students = get_all_students()
            attendance_records = get_attendance_records()
        except (PyMongoError, RuntimeError) as exc:
            st.error(
                "Could not load the report. Check MONGO_URI, Atlas network access, and "
                f"database credentials ({type(exc).__name__})."
            )
            return

        if not report_students:
            st.info("Add students to start building your attendance report.")
            return

        summary, total_sessions = build_attendance_summary(
            report_students, attendance_records
        )
        average_attendance = summary["attendance_pct"].mean() if not summary.empty else 0
        defaulter_count = int((summary["attendance_pct"] < 75).sum()) if total_sessions else 0
        kpi_1, kpi_2, kpi_3, kpi_4 = st.columns(4)
        with kpi_1:
            self._kpi("Students", str(len(summary)), "Active roster")
        with kpi_2:
            self._kpi("Class sessions", str(total_sessions), "Recorded dates")
        with kpi_3:
            self._kpi("Average attendance", f"{average_attendance:.1f}%", "Across the roster")
        with kpi_4:
            self._kpi("Needs attention", str(defaulter_count), "Below 75%" if total_sessions else "After first session")

        if not total_sessions:
            st.info("No attendance sessions have been recorded yet.")

        display_summary = summary.rename(
            columns={
                "roll_no": "Roll number",
                "name": "Student",
                "class": "Class",
                "sessions_present": "Present",
                "sessions_total": "Sessions",
                "attendance_pct": "Attendance %",
            }
        )

        col_filter, search = st.columns([1, 2])
        with col_filter:
            class_filter = st.selectbox("Filter by class", ["All classes"] + sorted(display_summary["Class"].unique()))
        with search:
            search_term = st.text_input("Search roster", placeholder="Search by name or roll number")
        filtered_summary = display_summary.copy()
        if class_filter != "All classes":
            filtered_summary = filtered_summary[filtered_summary["Class"] == class_filter]
        if search_term.strip():
            query = search_term.strip().lower()
            filtered_summary = filtered_summary[
                filtered_summary["Student"].str.lower().str.contains(query, regex=False)
                | filtered_summary["Roll number"].str.lower().str.contains(query, regex=False)
            ]

        st.caption(f"Showing {len(filtered_summary)} of {len(display_summary)} students")
        st.dataframe(
            filtered_summary.style.apply(
                lambda row: self._highlight_defaulters(row, total_sessions),
                axis=1,
            ),
            use_container_width=True,
            hide_index=True,
        )

        if total_sessions:
            chart_data = summary.set_index("roll_no")["attendance_pct"]
            chart_data.name = "Attendance %"
            st.bar_chart(chart_data)

            defaulters = filtered_summary.loc[filtered_summary["Attendance %"] < 75]
            if not defaulters.empty:
                st.warning("Students below 75% attendance")
                st.dataframe(defaulters, use_container_width=True, hide_index=True)

        csv_buffer = StringIO()
        display_summary.to_csv(csv_buffer, index=False)
        st.download_button(
            "Download full report",
            csv_buffer.getvalue(),
            file_name=f"attendance-report-{date.today().isoformat()}.csv",
            mime="text/csv",
        )

    def run(self) -> None:
        logo_path = Path(__file__).parent / "static" / "images" / "stulib_logo.png"
        st.set_page_config(page_title="StuLib | Attendance", page_icon="📚", layout="wide", initial_sidebar_state="expanded")
        self._inject_styles()
        self._render_loader(logo_path)
        with st.sidebar:
            if logo_path.exists():
                logo_data = base64.b64encode(logo_path.read_bytes()).decode("ascii")
                st.markdown(
                    f'<img class="stulib-logo" src="data:image/png;base64,{logo_data}" '
                    'alt="StuLib logo">',
                    unsafe_allow_html=True,
                )
            st.markdown("### StuLib")
            st.caption("Student attendance, made simple.")
            st.divider()
            if st.button("↻ Refresh data", key="refresh_data", use_container_width=True):
                st.rerun()
            st.caption(f"Today · {date.today().strftime('%d %b %Y')}")

        st.markdown(
            '<section class="hero"><h1>Attendance, at a glance.</h1>'
            '<p>Keep your roster current, record sessions quickly, and spot support needs early.</p></section>',
            unsafe_allow_html=True,
        )

        add_tab, attendance_tab, reports_tab = st.tabs(
            ["Add Student", "Mark Attendance", "Reports"]
        )

        with add_tab:
            self.render_add_student_tab()

        with attendance_tab:
            self.render_attendance_tab()

        with reports_tab:
            self.render_reports_tab()


if __name__ == "__main__":
    Main().run()

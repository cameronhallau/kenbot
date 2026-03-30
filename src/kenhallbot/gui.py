from __future__ import annotations

import json

from flask import Flask, render_template_string, request

from .config import load_settings, save_settings_values
from .models import FactPack, PricePerformance, ResearchBrief, StandardStats
from .pipeline import Pipeline


BRIEF_SECTION_DEFS = (
    {
        "key": "story_angle",
        "title": "Story angle",
        "note": "Shape the opening hook, thesis, or headline direction.",
        "placeholder": "Add the main angle or hook",
    },
    {
        "key": "evidence_context",
        "title": "Evidence and context",
        "note": "Keep the most useful proof points and recent context together.",
        "placeholder": "Add a supporting fact or context point",
    },
    {
        "key": "company_profile",
        "title": "Company profile stats",
        "note": "Only keep the company stats that really sharpen the article.",
        "placeholder": "Add a company profile stat or context point",
    },
    {
        "key": "price_context",
        "title": "3-day context",
        "note": "Keep only the immediate price context that helps the story.",
        "placeholder": "Add a recent price-context point",
    },
    {
        "key": "company_developments",
        "title": "Company developments",
        "note": "Track the business-specific updates worth carrying into the piece.",
        "placeholder": "Add a company-specific development",
    },
    {
        "key": "watch_next",
        "title": "What investors should watch next",
        "note": "Use this for caveats, uncertainty, and the next things that matter.",
        "placeholder": "Add a risk or next watch item",
    },
)


APP_TEMPLATE = r"""
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>KenHallBot</title>
    <style>
      @import url("https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;700&family=Space+Grotesk:wght@400;500;700&display=swap");
      :root {
        --bg: #dde5ee;
        --bg-deep: #cad5e0;
        --panel: #e7eef5;
        --panel-strong: #eff4f9;
        --panel-soft: #d7e1eb;
        --panel-tint: rgba(236, 243, 248, 0.72);
        --ink: #20303f;
        --muted: #627385;
        --accent: #2d5e77;
        --accent-strong: #21475b;
        --accent-soft: #d9e9f2;
        --accent-fog: rgba(111, 157, 184, 0.2);
        --line: rgba(86, 111, 133, 0.14);
        --line-strong: rgba(70, 91, 109, 0.28);
        --good: #2d7554;
        --bad: #a34c4a;
        --warn: #9a6a38;
        --raised-shadow-xl:
          24px 24px 44px rgba(155, 171, 190, 0.46),
          -24px -24px 42px rgba(255, 255, 255, 0.95);
        --raised-shadow:
          16px 16px 30px rgba(154, 170, 189, 0.46),
          -16px -16px 30px rgba(255, 255, 255, 0.9);
        --raised-shadow-tight:
          10px 10px 18px rgba(154, 170, 189, 0.34),
          -10px -10px 18px rgba(255, 255, 255, 0.86);
        --inset-shadow:
          inset 8px 8px 16px rgba(168, 183, 199, 0.42),
          inset -8px -8px 16px rgba(255, 255, 255, 0.88);
        --focus-ring: 0 0 0 3px rgba(46, 91, 114, 0.16);
      }
      * {
        box-sizing: border-box;
      }
      html {
        background: var(--bg);
      }
      body {
        position: relative;
        margin: 0;
        color: var(--ink);
        font-family: "Avenir Next", "Segoe UI", "Helvetica Neue", sans-serif;
        background:
          radial-gradient(circle at top left, rgba(255, 255, 255, 0.85) 0%, rgba(237, 243, 248, 0) 38%),
          radial-gradient(circle at 90% 10%, rgba(193, 214, 228, 0.62) 0%, rgba(193, 214, 228, 0) 30%),
          linear-gradient(160deg, #dbe4ec 0%, #d4dee8 48%, #ced8e3 100%);
      }
      body::before,
      body::after {
        content: "";
        position: fixed;
        z-index: 0;
        width: 32rem;
        height: 32rem;
        border-radius: 50%;
        opacity: 0.55;
        pointer-events: none;
        filter: blur(28px);
      }
      body::before {
        top: -9rem;
        left: -8rem;
        background: radial-gradient(circle, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0) 70%);
      }
      body::after {
        right: -10rem;
        bottom: -10rem;
        background: radial-gradient(circle, rgba(192, 212, 227, 0.75) 0%, rgba(192, 212, 227, 0) 70%);
      }
      h1, h2, h3, h4, p {
        margin: 0;
      }
      a {
        color: var(--accent);
      }
      .page {
        position: relative;
        z-index: 1;
        max-width: 1500px;
        margin: 0 auto;
        padding: 28px 24px 56px;
      }
      .page::before {
        content: "";
        position: absolute;
        inset: 10.5rem 3rem auto;
        height: 18rem;
        border-radius: 48px;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.45) 0%, rgba(255, 255, 255, 0.04) 100%);
        filter: blur(16px);
        pointer-events: none;
      }
      .masthead {
        position: relative;
        overflow: hidden;
        display: grid;
        grid-template-columns: minmax(0, 1.2fr) minmax(360px, 0.9fr);
        gap: 28px;
        align-items: stretch;
        padding: 28px;
        border-radius: 34px;
        background: linear-gradient(145deg, rgba(238, 244, 249, 0.95) 0%, rgba(222, 231, 239, 0.92) 100%);
        box-shadow: var(--raised-shadow-xl);
        border: 1px solid rgba(255, 255, 255, 0.55);
      }
      .masthead::before {
        content: "";
        position: absolute;
        inset: -20% auto auto -8%;
        width: 18rem;
        height: 18rem;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(255, 255, 255, 0.72) 0%, rgba(255, 255, 255, 0) 72%);
        pointer-events: none;
      }
      .masthead::after {
        content: "";
        position: absolute;
        right: -4rem;
        bottom: -4rem;
        width: 14rem;
        height: 14rem;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(111, 157, 184, 0.2) 0%, rgba(111, 157, 184, 0) 70%);
        pointer-events: none;
      }
      .hero-copy {
        position: relative;
        z-index: 1;
        display: grid;
        gap: 18px;
      }
      .eyebrow {
        width: fit-content;
        padding: 8px 14px;
        border-radius: 999px;
        background: var(--panel);
        box-shadow: var(--raised-shadow-tight);
        color: var(--muted);
        font-size: 12px;
        letter-spacing: 0.18em;
        text-transform: uppercase;
      }
      .masthead h1 {
        max-width: 13ch;
        font-family: "Iowan Old Style", "Palatino Linotype", serif;
        font-size: clamp(2.7rem, 5vw, 4.9rem);
        line-height: 0.96;
        font-weight: 600;
        letter-spacing: -0.03em;
      }
      .lead {
        max-width: 56rem;
        color: var(--muted);
        font-size: 1.05rem;
        line-height: 1.7;
      }
      .hero-strip {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
      }
      .hero-pill {
        padding: 10px 14px;
        border-radius: 999px;
        background: var(--panel);
        box-shadow: var(--raised-shadow-tight);
        color: var(--muted);
        font-size: 0.9rem;
        line-height: 1.2;
      }
      .hero-pill strong {
        color: var(--ink);
      }
      .meta-grid {
        position: relative;
        z-index: 1;
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 16px;
        align-content: stretch;
        min-width: 0;
      }
      .meta-block {
        display: grid;
        gap: 10px;
        padding: 20px 18px;
        border-radius: 26px;
        background: linear-gradient(145deg, var(--panel-strong) 0%, var(--panel-soft) 100%);
        box-shadow: var(--raised-shadow-tight);
        border: 1px solid rgba(255, 255, 255, 0.46);
      }
      .meta-label {
        color: var(--muted);
        font-size: 12px;
        letter-spacing: 0.14em;
        text-transform: uppercase;
      }
      .meta-value {
        font-size: 0.98rem;
        line-height: 1.5;
        word-break: break-word;
      }
      .workspace {
        margin-top: 28px;
        display: grid;
        gap: 24px;
      }
      .tabs-shell {
        position: relative;
        padding: 16px;
        border-radius: 28px;
        background: linear-gradient(145deg, rgba(237, 243, 248, 0.95) 0%, rgba(218, 226, 234, 0.94) 100%);
        box-shadow: var(--raised-shadow-xl);
        border: 1px solid rgba(255, 255, 255, 0.5);
      }
      .tabs-shell::after {
        content: "";
        position: absolute;
        inset: 10px;
        border-radius: 22px;
        box-shadow: inset 1px 1px 0 rgba(255, 255, 255, 0.72), inset -1px -1px 0 rgba(125, 144, 163, 0.08);
        pointer-events: none;
      }
      .tabs {
        display: flex;
        gap: 14px;
        padding: 4px;
      }
      .tab-link {
        flex: 1 1 0;
        min-width: 0;
        padding: 16px 18px;
        border: none;
        border-radius: 22px;
        background: linear-gradient(145deg, var(--panel-strong) 0%, var(--panel-soft) 100%);
        box-shadow: var(--raised-shadow-tight);
        color: var(--muted);
        font: inherit;
        font-weight: 700;
        letter-spacing: 0.01em;
        cursor: pointer;
        transition: transform 120ms ease, color 120ms ease, box-shadow 120ms ease;
      }
      .tab-link:hover {
        color: var(--ink);
        transform: translateY(-1px);
      }
      .tab-link.is-active {
        color: var(--accent);
        box-shadow: var(--inset-shadow);
        background: linear-gradient(145deg, rgba(217, 233, 242, 0.95) 0%, rgba(231, 239, 246, 0.92) 100%);
      }
      .tab-panel {
        padding-top: 4px;
      }
      .tab-panel[hidden] {
        display: none;
      }
      .research-shell {
        display: grid;
        grid-template-columns: minmax(320px, 0.76fr) minmax(0, 1.6fr);
        gap: 24px;
        align-items: start;
      }
      .write-shell {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 24px;
        align-items: start;
      }
      .content-stack {
        display: grid;
        gap: 24px;
      }
      .rail {
        display: grid;
        gap: 24px;
      }
      .section {
        position: relative;
        overflow: hidden;
        padding: 24px;
        border-radius: 30px;
        background: linear-gradient(145deg, rgba(236, 243, 248, 0.96) 0%, rgba(219, 228, 237, 0.95) 100%);
        box-shadow: var(--raised-shadow);
        border: 1px solid rgba(255, 255, 255, 0.5);
      }
      .section::before {
        content: "";
        position: absolute;
        inset: 10px;
        border-radius: 22px;
        box-shadow: inset 1px 1px 0 rgba(255, 255, 255, 0.7), inset -1px -1px 0 rgba(123, 143, 164, 0.08);
        pointer-events: none;
      }
      .section::after {
        content: "";
        position: absolute;
        inset: auto -5rem -6rem auto;
        width: 12rem;
        height: 12rem;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(111, 157, 184, 0.13) 0%, rgba(111, 157, 184, 0) 72%);
        pointer-events: none;
      }
      .section-rail {
        background: linear-gradient(145deg, rgba(232, 240, 247, 0.98) 0%, rgba(217, 227, 237, 0.96) 100%);
      }
      .section-featured {
        background: linear-gradient(145deg, rgba(234, 243, 249, 0.98) 0%, rgba(214, 225, 236, 0.98) 100%);
        box-shadow: var(--raised-shadow-xl);
      }
      .section-head {
        display: flex;
        justify-content: space-between;
        align-items: start;
        gap: 18px;
        margin-bottom: 18px;
      }
      .section-label {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 10px;
        padding: 8px 12px;
        border-radius: 999px;
        background: linear-gradient(145deg, rgba(234, 241, 247, 0.98) 0%, rgba(220, 229, 237, 0.98) 100%);
        box-shadow: var(--raised-shadow-tight);
        color: var(--muted);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-transform: uppercase;
      }
      .section-label::before {
        content: "";
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: linear-gradient(145deg, var(--accent) 0%, #76a8c3 100%);
        box-shadow: 0 0 0 5px var(--accent-fog);
      }
      .section-head h2,
      .section-head h3 {
        font-size: 1.18rem;
        line-height: 1.25;
      }
      .section-head p,
      .hint {
        color: var(--muted);
        font-size: 0.95rem;
        line-height: 1.6;
      }
      .actions {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        justify-content: flex-end;
      }
      .button-row {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 10px;
        margin-top: 14px;
      }
      .field-grid,
      .metric-grid,
      .brief-editor-grid,
      .review-grid {
        display: grid;
        gap: 18px;
      }
      .field-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
        margin-bottom: 16px;
      }
      .metric-grid,
      .brief-editor-grid,
      .review-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .field label,
      .table-wrap label,
      .editor-label {
        display: block;
        margin-bottom: 9px;
        color: var(--muted);
        font-size: 12px;
        letter-spacing: 0.14em;
        text-transform: uppercase;
      }
      input,
      textarea,
      button {
        font: inherit;
      }
      input,
      textarea {
        width: 100%;
        padding: 15px 16px;
        border: 1px solid transparent;
        border-radius: 18px;
        background: linear-gradient(145deg, rgba(229, 238, 245, 0.95) 0%, rgba(239, 245, 249, 0.96) 100%);
        box-shadow: var(--inset-shadow);
        color: var(--ink);
      }
      input::placeholder,
      textarea::placeholder {
        color: rgba(98, 115, 133, 0.82);
      }
      input:focus,
      textarea:focus {
        outline: none;
        border-color: rgba(46, 91, 114, 0.18);
        box-shadow: var(--inset-shadow), var(--focus-ring);
      }
      textarea {
        min-height: 140px;
        resize: vertical;
        line-height: 1.62;
      }
      textarea.auto-grow {
        min-height: 56px;
        resize: none;
        overflow-y: hidden;
      }
      textarea.prompt-editor,
      textarea.article-editor,
      .rich-editor {
        min-height: 580px;
      }
      textarea.article-editor,
      .rich-editor {
        font-family: "Iowan Old Style", "Palatino Linotype", serif;
        font-size: 1.06rem;
      }
      textarea.markdown-store {
        display: none;
      }
      .rich-editor-shell {
        display: grid;
        gap: 14px;
      }
      .rich-toolbar {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        padding: 12px;
        border-radius: 22px;
        background: linear-gradient(145deg, rgba(230, 239, 246, 0.95) 0%, rgba(218, 227, 236, 0.96) 100%);
        box-shadow: var(--inset-shadow);
      }
      .toolbar-button,
      button {
        padding: 12px 18px;
        border: none;
        border-radius: 18px;
        background: linear-gradient(145deg, #386c84 0%, var(--accent-strong) 100%);
        box-shadow:
          8px 8px 16px rgba(149, 168, 186, 0.34),
          -8px -8px 16px rgba(255, 255, 255, 0.6);
        color: #f8fbfd;
        cursor: pointer;
        transition: transform 120ms ease, box-shadow 120ms ease, filter 120ms ease;
      }
      .toolbar-button:hover,
      button:hover {
        transform: translateY(-1px);
        filter: brightness(1.02);
      }
      .toolbar-button:active,
      button:active {
        transform: translateY(0);
        box-shadow: var(--inset-shadow);
      }
      button.secondary,
      .toolbar-button {
        background: linear-gradient(145deg, var(--panel-strong) 0%, var(--panel-soft) 100%);
        color: var(--ink);
      }
      button.secondary {
        box-shadow: var(--raised-shadow-tight);
      }
      button.compact {
        padding: 10px 12px;
        border-radius: 16px;
      }
      .rich-editor {
        padding: 22px 24px;
        border: 1px solid transparent;
        border-radius: 24px;
        background: linear-gradient(145deg, rgba(228, 237, 244, 0.95) 0%, rgba(241, 246, 250, 0.96) 100%);
        box-shadow: var(--inset-shadow);
        color: var(--ink);
        line-height: 1.72;
        overflow-wrap: anywhere;
      }
      .rich-editor:focus {
        outline: none;
        border-color: rgba(46, 91, 114, 0.18);
        box-shadow: var(--inset-shadow), var(--focus-ring);
      }
      .rich-editor.is-empty::before {
        content: attr(data-placeholder);
        color: var(--muted);
        pointer-events: none;
      }
      .rich-editor h1,
      .rich-editor h2,
      .rich-editor h3 {
        margin: 1.1em 0 0.45em;
        line-height: 1.15;
      }
      .rich-editor h1:first-child,
      .rich-editor h2:first-child,
      .rich-editor h3:first-child,
      .rich-editor p:first-child {
        margin-top: 0;
      }
      .rich-editor p,
      .rich-editor ul,
      .rich-editor ol,
      .rich-editor blockquote {
        margin: 0 0 1em;
      }
      .rich-editor ul,
      .rich-editor ol {
        padding-left: 1.5em;
      }
      .rich-editor blockquote {
        padding-left: 1em;
        border-left: 3px solid var(--line-strong);
        color: var(--muted);
      }
      .rich-editor a {
        text-decoration: underline;
      }
      .rich-editor code {
        padding: 0.08em 0.38em;
        border-radius: 8px;
        background: var(--accent-soft);
        font-size: 0.92em;
      }
      .error-banner {
        margin-top: 24px;
        padding: 18px 22px;
        border-radius: 24px;
        background: linear-gradient(145deg, #f2dddd 0%, #ecd2d2 100%);
        box-shadow: var(--raised-shadow-tight);
        color: #7a2b2b;
      }
      .status-banner {
        margin-top: 24px;
        padding: 18px 22px;
        border-radius: 24px;
        background: linear-gradient(145deg, #deeee4 0%, #d0e6d9 100%);
        box-shadow: var(--raised-shadow-tight);
        color: #27563d;
      }
      .subtle-box {
        padding: 16px 18px;
        border-radius: 20px;
        background: linear-gradient(145deg, rgba(231, 239, 245, 0.96) 0%, rgba(219, 227, 235, 0.98) 100%);
        box-shadow: var(--inset-shadow);
        color: var(--muted);
        line-height: 1.6;
      }
      .selected-line {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        color: var(--muted);
        font-size: 0.95rem;
      }
      .selected-line > div {
        padding: 12px 14px;
        border-radius: 18px;
        background: linear-gradient(145deg, rgba(235, 242, 247, 0.95) 0%, rgba(220, 229, 237, 0.96) 100%);
        box-shadow: var(--raised-shadow-tight);
      }
      .selected-line strong {
        color: var(--ink);
      }
      .table-wrap {
        overflow-x: auto;
      }
      table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0 10px;
      }
      th,
      td {
        padding: 14px 12px;
        text-align: left;
        vertical-align: top;
        font-size: 0.95rem;
      }
      th {
        color: var(--muted);
        font-size: 12px;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        font-weight: 700;
      }
      .movers-table tbody tr {
        transition: transform 120ms ease, box-shadow 120ms ease, background 120ms ease;
      }
      .movers-table tbody td {
        background: linear-gradient(145deg, rgba(236, 243, 248, 0.96) 0%, rgba(222, 231, 239, 0.96) 100%);
        box-shadow: var(--raised-shadow-tight);
      }
      .movers-table tbody td:first-child {
        border-radius: 18px 0 0 18px;
      }
      .movers-table tbody td:last-child {
        border-radius: 0 18px 18px 0;
      }
      .movers-table tbody tr:hover td {
        transform: translateY(-1px);
      }
      .movers-table tbody tr:has(input[type="radio"]:checked) td {
        background: linear-gradient(145deg, rgba(217, 233, 242, 0.98) 0%, rgba(231, 239, 246, 0.98) 100%);
        box-shadow: var(--inset-shadow);
      }
      .move-up {
        color: var(--good);
        font-weight: 700;
      }
      .move-down {
        color: var(--bad);
        font-weight: 700;
      }
      .radio-cell {
        width: 42px;
      }
      .radio-cell input {
        width: 18px;
        height: 18px;
        margin: 0;
        accent-color: var(--accent);
      }
      .clean-list {
        list-style: none;
        padding: 0;
        margin: 0;
        display: grid;
        gap: 10px;
      }
      .clean-list li {
        padding: 14px 16px;
        border-radius: 18px;
        background: linear-gradient(145deg, rgba(232, 240, 246, 0.96) 0%, rgba(220, 228, 236, 0.96) 100%);
        box-shadow: var(--raised-shadow-tight);
        line-height: 1.55;
      }
      .clean-list.tight li {
        padding: 12px 14px;
      }
      .metric {
        padding: 14px 16px;
        border-radius: 18px;
        background: linear-gradient(145deg, rgba(233, 241, 246, 0.96) 0%, rgba(219, 228, 236, 0.96) 100%);
        box-shadow: var(--raised-shadow-tight);
      }
      .metric-label {
        color: var(--muted);
        font-size: 12px;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }
      .metric-value {
        margin-top: 8px;
        font-size: 1.05rem;
      }
      .brief-editor {
        padding: 18px;
        border-radius: 24px;
        background: linear-gradient(145deg, rgba(231, 239, 246, 0.96) 0%, rgba(219, 228, 236, 0.96) 100%);
        box-shadow: var(--inset-shadow);
      }
      .brief-editor h4,
      .review-grid h4,
      .source-card h4 {
        margin-bottom: 10px;
        font-size: 0.98rem;
      }
      .brief-note {
        margin-bottom: 14px;
        color: var(--muted);
        font-size: 0.92rem;
        line-height: 1.55;
      }
      .brief-items,
      .source-grid {
        display: grid;
        gap: 12px;
      }
      .brief-item {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 10px;
        align-items: start;
      }
      .brief-item textarea {
        padding: 12px 13px;
        min-height: 56px;
        overflow-wrap: anywhere;
        white-space: pre-wrap;
      }
      .source-card {
        padding: 18px;
        border-radius: 22px;
        background: linear-gradient(145deg, rgba(231, 239, 246, 0.96) 0%, rgba(220, 228, 236, 0.96) 100%);
        box-shadow: var(--raised-shadow-tight);
      }
      .source-card p {
        line-height: 1.65;
      }
      .source-meta {
        margin-top: 10px;
        color: var(--muted);
        font-size: 0.9rem;
      }
      .empty {
        color: var(--muted);
        line-height: 1.65;
      }
      .review-header {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 14px;
        margin-bottom: 16px;
      }
      .verdict {
        padding: 10px 14px;
        border-radius: 999px;
        background: linear-gradient(145deg, rgba(233, 241, 246, 0.96) 0%, rgba(219, 228, 236, 0.96) 100%);
        box-shadow: var(--raised-shadow-tight);
        font-size: 1.02rem;
        font-weight: 700;
        text-transform: capitalize;
      }
      .verdict.pass {
        color: var(--good);
      }
      .verdict.warn {
        color: var(--warn);
      }
      .verdict.fail {
        color: var(--bad);
      }
      .note {
        color: var(--muted);
        font-size: 0.93rem;
      }
      .state-store {
        display: none;
      }
      @media (max-width: 1180px) {
        .masthead,
        .research-shell,
        .write-shell,
        .meta-grid,
        .field-grid,
        .metric-grid,
        .brief-editor-grid,
        .review-grid {
          grid-template-columns: 1fr;
        }
      }
      @media (max-width: 720px) {
        .page {
          padding: 18px 14px 40px;
        }
        .masthead,
        .section {
          padding: 20px;
          border-radius: 26px;
        }
        .section-label {
          letter-spacing: 0.12em;
        }
        .tabs {
          flex-direction: column;
        }
        .tab-link {
          width: 100%;
        }
        .brief-item {
          grid-template-columns: 1fr;
        }
      }
      :root {
        --paper: #f4f0e6;
        --paper-deep: #e2dccf;
        --paper-strong: #d8d0bf;
        --ink: #111111;
        --muted: #4d473e;
        --accent: #f45d2d;
        --accent-soft: #ffd44d;
        --accent-cool: #8cb7ff;
        --good: #0d8b46;
        --bad: #ba2d0b;
        --warn: #8a5b00;
        --line: #111111;
        --line-soft: rgba(17, 17, 17, 0.24);
        --focus-ring: 0 0 0 4px rgba(244, 93, 45, 0.28);
      }
      body::before,
      body::after,
      .page::before,
      .masthead::before,
      .masthead::after,
      .section::before,
      .section::after {
        display: none;
      }
      html {
        background: var(--line);
      }
      body {
        color: var(--ink);
        font-family: "Space Grotesk", "Arial Narrow", sans-serif;
        background: linear-gradient(180deg, var(--paper) 0%, #efe8da 100%);
      }
      a {
        color: inherit;
        text-decoration-thickness: 2px;
        text-underline-offset: 0.16em;
      }
      .page {
        max-width: 1560px;
        padding: 12px 12px 40px;
      }
      .masthead {
        gap: 0;
        padding: 0;
        border: 4px solid var(--line);
        border-radius: 0;
        background: linear-gradient(135deg, var(--paper) 0 76%, var(--accent-soft) 76% 100%);
        box-shadow: 10px 10px 0 var(--line);
      }
      .hero-copy {
        gap: 18px;
        padding: 28px;
      }
      .eyebrow {
        display: inline-block;
        padding: 0 0 8px;
        border-bottom: 3px solid var(--line);
        border-radius: 0;
        background: none;
        box-shadow: none;
        color: var(--ink);
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.22em;
      }
      .masthead h1 {
        max-width: 11ch;
        font-family: "Space Grotesk", "Arial Narrow", sans-serif;
        font-size: clamp(3rem, 6vw, 6rem);
        line-height: 0.92;
        font-weight: 700;
        letter-spacing: -0.05em;
        text-transform: uppercase;
      }
      .lead {
        color: var(--muted);
        font-size: 1rem;
        line-height: 1.6;
      }
      .hero-strip {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0;
        border-top: 2px solid var(--line);
        border-bottom: 2px solid var(--line);
      }
      .hero-pill {
        min-height: 100%;
        padding: 12px 14px;
        border-right: 2px solid var(--line);
        border-radius: 0;
        background: none;
        box-shadow: none;
        color: var(--muted);
        font-size: 0.9rem;
        line-height: 1.35;
        text-transform: uppercase;
      }
      .hero-pill:last-child {
        border-right: 0;
      }
      .hero-pill strong {
        display: block;
        margin-bottom: 4px;
        color: var(--ink);
        font-size: 0.72rem;
        letter-spacing: 0.12em;
      }
      .meta-grid {
        grid-template-columns: 1fr;
        gap: 0;
        border-left: 4px solid var(--line);
        background: linear-gradient(180deg, #fff1a8 0%, var(--paper-strong) 100%);
      }
      .meta-block {
        gap: 8px;
        padding: 24px;
        border: 0;
        border-bottom: 2px solid var(--line);
        border-radius: 0;
        background: none;
        box-shadow: none;
      }
      .meta-block:last-child {
        border-bottom: 0;
      }
      .meta-label,
      .field label,
      .table-wrap label,
      .editor-label,
      .metric-label,
      .section-label {
        font-family: "IBM Plex Mono", monospace;
        color: var(--muted);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-transform: uppercase;
      }
      .meta-value {
        color: var(--ink);
      }
      .workspace {
        margin-top: 0;
        gap: 0;
        border: 4px solid var(--line);
        background: rgba(255, 255, 255, 0.2);
      }
      .tabs-shell {
        padding: 0;
        border: 0;
        border-radius: 0;
        border-bottom: 4px solid var(--line);
        background: var(--paper-deep);
        box-shadow: none;
      }
      .tabs-shell::after {
        display: none;
      }
      .tabs {
        gap: 0;
        padding: 0;
      }
      .tab-link {
        padding: 18px 20px;
        border: 0;
        border-right: 2px solid var(--line);
        border-radius: 0;
        background: transparent;
        box-shadow: none;
        color: var(--muted);
        font-size: 1rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
      }
      .tab-link:last-child {
        border-right: 0;
      }
      .tab-link:hover {
        color: var(--ink);
        transform: none;
        background: rgba(255, 255, 255, 0.35);
      }
      .tab-link.is-active {
        color: #fff8ec;
        background: var(--accent);
        box-shadow: none;
      }
      .tab-panel {
        padding-top: 0;
      }
      .research-shell,
      .write-shell,
      .content-stack,
      .rail {
        gap: 0;
      }
      .research-shell {
        grid-template-columns: minmax(320px, 0.72fr) minmax(0, 1.7fr);
      }
      .research-shell > .rail {
        border-right: 4px solid var(--line);
      }
      .write-shell > .section + .section {
        border-left: 4px solid var(--line);
      }
      .section {
        overflow: visible;
        padding: 24px;
        border: 0;
        border-top: 2px solid var(--line);
        border-radius: 0;
        background: rgba(255, 255, 255, 0.18);
        box-shadow: none;
      }
      .section:first-child,
      .research-shell > .content-stack .section:first-child {
        border-top: 0;
      }
      .section-rail {
        background:
          linear-gradient(90deg, rgba(255, 212, 77, 0.3) 0 12px, transparent 12px 100%),
          rgba(255, 255, 255, 0.1);
      }
      .section-featured {
        background:
          linear-gradient(90deg, rgba(244, 93, 45, 0.18) 0 12px, transparent 12px 100%),
          rgba(255, 255, 255, 0.24);
      }
      .section-label {
        display: inline-block;
        margin-bottom: 12px;
        padding: 0 0 8px;
        border-bottom: 3px solid var(--line);
        border-radius: 0;
        background: none;
        box-shadow: none;
      }
      .section-label::before {
        display: none;
      }
      .section-head h2,
      .section-head h3 {
        font-size: 1.28rem;
        line-height: 1.15;
        text-transform: uppercase;
      }
      .section-head p,
      .hint,
      .brief-note,
      .source-meta,
      .empty,
      .note {
        color: var(--muted);
      }
      input,
      textarea {
        border: 2px solid var(--line);
        border-radius: 0;
        background: #fffdf8;
        box-shadow: none;
        color: var(--ink);
      }
      input:focus,
      textarea:focus {
        border-color: var(--line);
        box-shadow: var(--focus-ring);
      }
      textarea.article-editor,
      .rich-editor {
        font-family: "Space Grotesk", "Arial Narrow", sans-serif;
        font-size: 1.03rem;
      }
      .rich-editor-shell {
        gap: 0;
        border: 2px solid var(--line);
      }
      .rich-toolbar {
        gap: 0;
        padding: 0;
        border-radius: 0;
        border-bottom: 2px solid var(--line);
        background: var(--paper-deep);
        box-shadow: none;
      }
      button,
      .toolbar-button {
        border: 2px solid var(--line);
        border-radius: 0;
        background: var(--ink);
        box-shadow: 4px 4px 0 var(--accent-soft);
        color: #fff8ec;
        transition: transform 120ms ease, box-shadow 120ms ease, background 120ms ease;
      }
      button:hover,
      .toolbar-button:hover {
        transform: translate(-2px, -2px);
        filter: none;
        box-shadow: 8px 8px 0 var(--accent-soft);
      }
      button:active,
      .toolbar-button:active {
        transform: translate(0, 0);
        box-shadow: 2px 2px 0 var(--accent-soft);
      }
      button.secondary,
      .toolbar-button {
        background: #fffdf8;
        color: var(--ink);
      }
      button.compact {
        border-radius: 0;
      }
      .rich-editor {
        border: 0;
        border-radius: 0;
        background: #fffdf8;
        box-shadow: none;
      }
      .rich-editor:focus {
        border-color: transparent;
        box-shadow: inset 0 0 0 3px rgba(244, 93, 45, 0.2);
      }
      .rich-editor h1,
      .rich-editor h2,
      .rich-editor h3 {
        line-height: 1.05;
        text-transform: uppercase;
      }
      .rich-editor blockquote {
        border-left: 4px solid var(--accent);
      }
      .rich-editor code {
        border-radius: 0;
        background: var(--accent-soft);
        font-family: "IBM Plex Mono", monospace;
      }
      .error-banner {
        margin-top: 0;
        margin-bottom: 12px;
        border: 4px solid var(--line);
        border-radius: 0;
        background: #f8b8aa;
        box-shadow: 8px 8px 0 var(--line);
        color: var(--ink);
        font-weight: 700;
      }
      .status-banner {
        margin-top: 0;
        margin-bottom: 12px;
        border: 4px solid var(--line);
        border-radius: 0;
        background: #badcc0;
        box-shadow: 8px 8px 0 var(--line);
        color: var(--ink);
        font-weight: 700;
      }
      .subtle-box {
        border-left: 4px solid var(--accent);
        border-radius: 0;
        background: rgba(255, 255, 255, 0.36);
        box-shadow: none;
      }
      .selected-line {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0;
        border: 2px solid var(--line);
      }
      .selected-line > div {
        padding: 14px 16px;
        border-right: 2px solid var(--line);
        border-radius: 0;
        background: none;
        box-shadow: none;
        color: var(--muted);
        text-transform: uppercase;
      }
      .selected-line > div:last-child {
        border-right: 0;
      }
      .selected-line strong {
        display: block;
        margin-bottom: 4px;
        font-size: 0.72rem;
        letter-spacing: 0.14em;
      }
      .table-wrap {
        border: 2px solid var(--line);
        background: #fffdf8;
      }
      table {
        border-collapse: collapse;
        border-spacing: 0;
      }
      th,
      td {
        border-bottom: 2px solid var(--line);
      }
      th {
        background: var(--paper-deep);
      }
      .movers-table tbody td {
        background: transparent;
        box-shadow: none;
      }
      .movers-table tbody td:first-child,
      .movers-table tbody td:last-child {
        border-radius: 0;
      }
      .movers-table tbody tr:hover td {
        transform: none;
        background: rgba(140, 183, 255, 0.12);
      }
      .movers-table tbody tr:has(input[type="radio"]:checked) td {
        background: rgba(255, 212, 77, 0.38);
        box-shadow: none;
      }
      .clean-list {
        gap: 0;
        border-top: 2px solid var(--line);
      }
      .clean-list li {
        padding: 14px 0;
        border-bottom: 2px solid var(--line);
        border-radius: 0;
        background: none;
        box-shadow: none;
      }
      .metric,
      .brief-editor,
      .source-card {
        padding: 18px 0 0;
        border-top: 2px solid var(--line);
        border-radius: 0;
        background: none;
        box-shadow: none;
      }
      .brief-editor h4,
      .review-grid h4,
      .source-card h4 {
        text-transform: uppercase;
      }
      .verdict {
        border: 2px solid var(--line);
        border-radius: 0;
        background: #fffdf8;
        box-shadow: none;
        text-transform: uppercase;
      }
      @media (max-width: 1180px) {
        .masthead,
        .research-shell,
        .write-shell,
        .field-grid,
        .metric-grid,
        .brief-editor-grid,
        .review-grid,
        .hero-strip,
        .selected-line {
          grid-template-columns: 1fr;
        }
        .meta-grid {
          border-top: 4px solid var(--line);
          border-left: 0;
        }
        .research-shell > .rail {
          border-right: 0;
          border-bottom: 4px solid var(--line);
        }
        .write-shell > .section + .section {
          border-top: 4px solid var(--line);
          border-left: 0;
        }
        .hero-pill,
        .selected-line > div {
          border-right: 0;
          border-bottom: 2px solid var(--line);
        }
        .hero-pill:last-child,
        .selected-line > div:last-child {
          border-bottom: 0;
        }
      }
      @media (max-width: 720px) {
        .page {
          padding: 12px 12px 40px;
        }
        .hero-copy,
        .section {
          padding: 18px;
        }
        .tab-link {
          border-right: 0;
          border-bottom: 2px solid var(--line);
        }
        .tab-link:last-child {
          border-bottom: 0;
        }
      }
    </style>
  </head>
  <body>
    <div class="page">
      {% if error %}
      <div class="error-banner">{{ error }}</div>
      {% endif %}
      {% if status_message %}
      <div class="status-banner">{{ status_message }}</div>
      {% endif %}

      <form method="post" class="workspace">
        <input type="hidden" name="active_tab" id="active_tab" value="{{ active_tab }}">

        <div class="state-store" aria-hidden="true">
          <textarea name="movers_json">{{ movers_json }}</textarea>
          <textarea name="fact_pack_json">{{ fact_pack_json }}</textarea>
          <textarea name="research_json">{{ research_json }}</textarea>
        </div>

        <div class="tabs-shell">
          <nav class="tabs" aria-label="Workflow tabs">
            <button type="button" class="tab-link {{ 'is-active' if active_tab == 'research' else '' }}" data-tab="research">Research setup</button>
            <button type="button" class="tab-link {{ 'is-active' if active_tab == 'write' else '' }}" data-tab="write">Write and review</button>
            <button type="button" class="tab-link {{ 'is-active' if active_tab == 'complete' else '' }}" data-tab="complete">Complete</button>
            <button type="button" class="tab-link {{ 'is-active' if active_tab == 'settings' else '' }}" data-tab="settings">Settings</button>
          </nav>
        </div>

        <section class="tab-panel" data-panel="research" {% if active_tab != 'research' %}hidden{% endif %}>
          <div class="research-shell">
            <aside class="rail">
              <section class="section section-rail">
                <div class="section-head">
                  <div>
                    <div class="section-label">Discovery</div>
                    <h2>Top movers</h2>
                  </div>
                  <button type="submit" name="action" value="find_movers">Refresh movers</button>
                </div>

                <div class="field-grid">
                  <div class="field">
                    <label for="limit">Rows to scan</label>
                    <input id="limit" name="limit" type="number" min="1" step="1" value="{{ limit }}">
                  </div>
                </div>

                <div class="table-wrap">
                  {% if movers %}
                  <table class="movers-table">
                    <thead>
                      <tr>
                        <th></th>
                        <th>Ticker</th>
                        <th>Company</th>
                        <th>Move</th>
                      </tr>
                    </thead>
                    <tbody>
                      {% for mover in movers %}
                      <tr>
                        <td class="radio-cell">
                          <input
                            type="radio"
                            name="selected_ticker_choice"
                            value="{{ mover.ticker }}"
                            {% if mover.ticker == selected_ticker %}checked{% endif %}
                            aria-label="Select {{ mover.ticker }}"
                          >
                        </td>
                        <td>{{ mover.ticker }}</td>
                        <td>{{ mover.company_name or 'Unknown company' }}</td>
                        <td class="{{ 'move-up' if mover.day_change_pct and mover.day_change_pct > 0 else 'move-down' }}">
                          {{ "%.2f"|format(mover.day_change_pct or 0) }}%
                        </td>
                      </tr>
                      {% endfor %}
                    </tbody>
                  </table>
                  {% else %}
                  <p class="empty">No movers loaded yet. Start here to build the shortlist for the day.</p>
                  {% endif %}
                </div>
              </section>
            </aside>

            <main class="content-stack">
              <section class="section section-featured">
                <div class="section-head">
                  <div>
                    <div class="section-label">Selection</div>
                    <h2>{{ selected_company_name }}</h2>
                    <p>Set the company, add research context, and build the material that will feed the writing tab.</p>
                  </div>
                </div>

                <div class="selected-line">
                  <div>
                    <label for="selected_ticker_input"><strong>Ticker:</strong></label>
                    <input id="selected_ticker_input" name="selected_ticker" value="{{ selected_company_ticker or '' }}" placeholder="SHEL.L">
                  </div>
                  <div><strong>Latest move:</strong> {{ selected_company_move or 'n/a' }}</div>
                </div>

                <div class="button-row">
                  <button type="submit" name="action" value="research">Build research</button>
                  <div class="hint">Build the working brief for the selected company.</div>
                </div>
              </section>

              <section class="section">
                <div class="section-head">
                  <div>
                    <div class="section-label">Brief</div>
                    <h3>Working brief</h3>
                  </div>
                </div>

                <div class="brief-editor-grid">
                  {% for section in brief_sections %}
                  {% if section.key not in ['company_profile', 'price_context'] %}
                  <div class="brief-editor">
                    <h4>{{ section.title }}</h4>
                    <div class="brief-items" data-brief-list="{{ section.key }}">
                      {% for item in section.entries %}
                      <div class="brief-item">
                        <textarea name="brief_{{ section.key }}[]" class="auto-grow" rows="1" placeholder="{{ section.placeholder }}">{{ item }}</textarea>
                        <button type="button" class="secondary compact" data-remove-brief-item>Remove</button>
                      </div>
                      {% endfor %}
                    </div>
                    <div class="button-row">
                      <button
                        type="button"
                        class="secondary compact"
                        data-add-brief-item
                        data-brief-key="{{ section.key }}"
                        data-placeholder="{{ section.placeholder }}"
                      >
                        Add item
                      </button>
                    </div>
                  </div>
                  {% endif %}
                  {% endfor %}
                </div>
              </section>

              <section class="section">
                <div class="section-head">
                  <div>
                    <div class="section-label">Snapshot</div>
                    <h3>Company snapshot</h3>
                  </div>
                </div>

                <div class="brief-editor">
                  <h4>{{ company_profile_section.title }}</h4>
                  <div class="brief-items" data-brief-list="{{ company_profile_section.key }}">
                    {% for item in company_profile_section.entries %}
                    <div class="brief-item">
                      <textarea name="brief_{{ company_profile_section.key }}[]" class="auto-grow" rows="1" placeholder="{{ company_profile_section.placeholder }}">{{ item }}</textarea>
                      <button type="button" class="secondary compact" data-remove-brief-item>Remove stat</button>
                    </div>
                    {% endfor %}
                  </div>
                  <div class="button-row">
                    <button
                      type="button"
                      class="secondary compact"
                      data-add-brief-item
                      data-brief-key="{{ company_profile_section.key }}"
                      data-placeholder="{{ company_profile_section.placeholder }}"
                    >
                      Add stat
                    </button>
                  </div>
                </div>
              </section>

              <section class="section">
                <div class="section-head">
                  <div>
                    <div class="section-label">Coverage</div>
                    <h3>Recent coverage</h3>
                    <p>Readable source summaries instead of raw payloads.</p>
                  </div>
                </div>

                {% if article_sources %}
                <div class="source-grid">
                  {% for source in article_sources %}
                  <div class="source-card">
                    <h4>{{ source.title }}</h4>
                    <p>{{ source.summary }}</p>
                    <div class="source-meta">
                      {% if source.date %}{{ source.date }}{% endif %}
                      {% if source.date and source.url %} · {% endif %}
                      {% if source.url %}<a href="{{ source.url }}" target="_blank" rel="noreferrer">Open source</a>{% endif %}
                    </div>
                  </div>
                  {% endfor %}
                </div>
                {% else %}
                <p class="empty">Source summaries will appear here when the research step finds relevant recent material.</p>
                {% endif %}
              </section>

              <section class="section">
                <div class="section-head">
                  <div>
                    <div class="section-label">Context</div>
                    <h3>3-day price context</h3>
                  </div>
                </div>

                <div class="brief-editor">
                  <h4>{{ price_context_section.title }}</h4>
                  <div class="brief-items" data-brief-list="{{ price_context_section.key }}">
                    {% for item in price_context_section.entries %}
                    <div class="brief-item">
                      <textarea name="brief_{{ price_context_section.key }}[]" class="auto-grow" rows="1" placeholder="{{ price_context_section.placeholder }}">{{ item }}</textarea>
                      <button type="button" class="secondary compact" data-remove-brief-item>Remove row</button>
                    </div>
                    {% endfor %}
                  </div>
                  <div class="button-row">
                    <button
                      type="button"
                      class="secondary compact"
                      data-add-brief-item
                      data-brief-key="{{ price_context_section.key }}"
                      data-placeholder="{{ price_context_section.placeholder }}"
                    >
                      Add row
                    </button>
                  </div>
                </div>
              </section>
            </main>
          </div>
        </section>

        <section class="tab-panel" data-panel="write" {% if active_tab != 'write' %}hidden{% endif %}>
          <div class="write-shell">
            <section class="section section-featured">
              <div class="section-head">
                <div>
                  <div class="section-label">Prompting</div>
                  <h2>Article-generation prompt</h2>
                  <div class="actions">
                    <button type="submit" name="action" value="refresh_prompt" class="secondary">Rebuild prompt</button>
                    <button type="submit" name="action" value="generate_article">Generate draft</button>
                  </div>
                </div>
              </div>

              <label class="editor-label" for="draft_prompt">Prompt</label>
              <textarea id="draft_prompt" name="draft_prompt" class="prompt-editor" placeholder="Run research first, then refine the company-specific prompt content here.">{{ draft_prompt }}</textarea>
            </section>

            <section class="section section-featured">
              <div class="section-head">
                <div>
                  <div class="section-label">Draft</div>
                  <h2>Final output</h2>
                  <div class="actions">
                    <button type="submit" name="action" value="final_details_pass" class="secondary">Final details pass</button>
                  </div>
                </div>
              </div>

              <label class="editor-label" for="article_text">Article draft</label>
              <textarea id="article_text" name="article_text" class="article-editor" placeholder="The generated article will appear here, and you can keep editing it in place.">{{ article_text }}</textarea>
            </section>
          </div>
        </section>

        <section class="tab-panel" data-panel="complete" {% if active_tab != 'complete' %}hidden{% endif %}>
          <section class="section section-featured">
            <div class="section-head">
              <div>
                <div class="section-label">Finish</div>
                <h2>Complete</h2>
              </div>
              <div class="actions">
                <button type="submit" name="action" value="save_complete_article" class="secondary">Save completed article</button>
              </div>
            </div>

            <label class="editor-label" for="complete_article_editor">Completed article</label>
            <div class="rich-editor-shell">
              <div class="rich-toolbar" data-rich-toolbar="complete">
                <button type="button" class="toolbar-button" data-command="bold">Bold</button>
                <button type="button" class="toolbar-button" data-command="italic">Italic</button>
                <button type="button" class="toolbar-button" data-block="h2">H2</button>
                <button type="button" class="toolbar-button" data-block="h3">H3</button>
                <button type="button" class="toolbar-button" data-block="p">Paragraph</button>
                <button type="button" class="toolbar-button" data-command="insertUnorderedList">Bullets</button>
                <button type="button" class="toolbar-button" data-command="insertOrderedList">Numbers</button>
                <button type="button" class="toolbar-button" data-command="createLink">Link</button>
              </div>
              <div
                id="complete_article_editor"
                class="rich-editor"
                contenteditable="true"
                spellcheck="true"
                data-placeholder="Run the final details pass from the Write and review tab to populate the completed article here."
              ></div>
            </div>
            <textarea
              id="complete_article_text"
              name="complete_article_text"
              class="markdown-store"
            >{{ complete_article_text }}</textarea>
          </section>
        </section>

        <section class="tab-panel" data-panel="settings" {% if active_tab != 'settings' %}hidden{% endif %}>
          <section class="section section-featured">
            <div class="section-head">
              <div>
                <div class="section-label">Settings</div>
                <h2>Models and keys</h2>
              </div>
            </div>

            <div class="field-grid">
              <div class="field">
                <label for="openrouter_api_key">OpenRouter API key</label>
                <input
                  id="openrouter_api_key"
                  name="openrouter_api_key"
                  type="password"
                  value="{{ openrouter_api_key }}"
                  placeholder="sk-or-v1-..."
                  autocomplete="off"
                >
              </div>
              <div class="field">
                <label for="research_openrouter_model">Research model</label>
                <input
                  id="research_openrouter_model"
                  name="research_openrouter_model"
                  value="{{ research_openrouter_model }}"
                  placeholder="openai/gpt-4.1-mini"
                >
              </div>
              <div class="field">
                <label for="article_openrouter_model">Article generation model</label>
                <input
                  id="article_openrouter_model"
                  name="article_openrouter_model"
                  value="{{ article_openrouter_model }}"
                  placeholder="anthropic/claude-sonnet-4.6"
                >
              </div>
              <div class="field">
                <label for="final_details_openrouter_model">Final details model</label>
                <input
                  id="final_details_openrouter_model"
                  name="final_details_openrouter_model"
                  value="{{ final_details_openrouter_model }}"
                  placeholder="openai/gpt-4.1-mini"
                >
              </div>
            </div>

            <div class="button-row">
              <button type="submit" name="action" value="save_settings">Save settings</button>
            </div>
          </section>
        </section>
      </form>
    </div>

    <script>
      const activeTabInput = document.getElementById("active_tab");
      const tabButtons = document.querySelectorAll(".tab-link");
      const tabPanels = document.querySelectorAll(".tab-panel");
      const workspaceForm = document.querySelector(".workspace");
      const selectedTickerInput = document.getElementById("selected_ticker_input");
      const selectedTickerRadios = document.querySelectorAll('input[name="selected_ticker_choice"]');
      const completeMarkdownField = document.getElementById("complete_article_text");
      const completeRichEditor = document.getElementById("complete_article_editor");
      const completeToolbar = document.querySelector('[data-rich-toolbar="complete"]');

      function syncTickerInputFromSelection(value) {
        if (!selectedTickerInput) {
          return;
        }
        selectedTickerInput.value = value || "";
      }

      function setActiveTab(tabName) {
        activeTabInput.value = tabName;
        tabButtons.forEach((button) => {
          button.classList.toggle("is-active", button.dataset.tab === tabName);
        });
        tabPanels.forEach((panel) => {
          panel.hidden = panel.dataset.panel !== tabName;
        });
        requestAnimationFrame(refreshAutoGrowTextareas);
      }

      tabButtons.forEach((button) => {
        button.addEventListener("click", () => setActiveTab(button.dataset.tab));
      });

      function buildBriefRow(name, placeholder, value = "") {
        const row = document.createElement("div");
        row.className = "brief-item";

        const input = document.createElement("textarea");
        input.name = name;
        input.placeholder = placeholder;
        input.value = value;
        input.rows = 1;
        input.className = "auto-grow";

        const button = document.createElement("button");
        button.type = "button";
        button.className = "secondary compact";
        button.setAttribute("data-remove-brief-item", "");
        button.textContent = "Remove";

        row.appendChild(input);
        row.appendChild(button);
        requestAnimationFrame(() => autoSizeTextarea(input));
        return row;
      }

      function autoSizeTextarea(textarea) {
        const borderHeight = textarea.offsetHeight - textarea.clientHeight;
        textarea.style.height = "auto";
        textarea.style.height = `${textarea.scrollHeight + borderHeight}px`;
      }

      function refreshAutoGrowTextareas() {
        document.querySelectorAll(".auto-grow").forEach((textarea) => {
          autoSizeTextarea(textarea);
        });
      }

      function escapeHtml(text) {
        return text
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/"/g, "&quot;")
          .replace(/'/g, "&#39;");
      }

      function renderInlineMarkdown(text) {
        let rendered = escapeHtml(text);
        rendered = rendered.replace(/`([^`]+)`/g, (_, code) => `<code>${code}</code>`);
        rendered = rendered.replace(
          /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
          (_, label, href) => `<a href="${href}" target="_blank" rel="noopener noreferrer">${label}</a>`,
        );
        rendered = rendered.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
        rendered = rendered.replace(/__([^_]+)__/g, "<strong>$1</strong>");
        rendered = rendered.replace(/(^|[\s(])\*([^*]+)\*(?=$|[\s.,!?:;)])/g, "$1<em>$2</em>");
        rendered = rendered.replace(/(^|[\s(])_([^_]+)_(?=$|[\s.,!?:;)])/g, "$1<em>$2</em>");
        return rendered;
      }

      function markdownToHtml(markdown) {
        const lines = markdown.replace(/\r\n?/g, "\n").split("\n");
        const blocks = [];
        let paragraphLines = [];
        let listType = null;
        let listItems = [];

        function flushParagraph() {
          if (!paragraphLines.length) {
            return;
          }
          blocks.push(`<p>${renderInlineMarkdown(paragraphLines.join(" "))}</p>`);
          paragraphLines = [];
        }

        function flushList() {
          if (!listType || !listItems.length) {
            listType = null;
            listItems = [];
            return;
          }
          const items = listItems.map((item) => `<li>${renderInlineMarkdown(item)}</li>`).join("");
          blocks.push(`<${listType}>${items}</${listType}>`);
          listType = null;
          listItems = [];
        }

        lines.forEach((line) => {
          const trimmed = line.trim();
          if (!trimmed) {
            flushParagraph();
            flushList();
            return;
          }

          const headingMatch = trimmed.match(/^(#{1,6})\s+(.*)$/);
          if (headingMatch) {
            flushParagraph();
            flushList();
            const level = Math.min(headingMatch[1].length, 6);
            blocks.push(`<h${level}>${renderInlineMarkdown(headingMatch[2])}</h${level}>`);
            return;
          }

          if (/^---+$/.test(trimmed)) {
            flushParagraph();
            flushList();
            blocks.push("<hr>");
            return;
          }

          const blockquoteMatch = trimmed.match(/^>\s?(.*)$/);
          if (blockquoteMatch) {
            flushParagraph();
            flushList();
            blocks.push(`<blockquote><p>${renderInlineMarkdown(blockquoteMatch[1])}</p></blockquote>`);
            return;
          }

          const unorderedMatch = trimmed.match(/^[-*]\s+(.*)$/);
          if (unorderedMatch) {
            flushParagraph();
            if (listType && listType !== "ul") {
              flushList();
            }
            listType = "ul";
            listItems.push(unorderedMatch[1]);
            return;
          }

          const orderedMatch = trimmed.match(/^\d+\.\s+(.*)$/);
          if (orderedMatch) {
            flushParagraph();
            if (listType && listType !== "ol") {
              flushList();
            }
            listType = "ol";
            listItems.push(orderedMatch[1]);
            return;
          }

          flushList();
          paragraphLines.push(trimmed);
        });

        flushParagraph();
        flushList();
        return blocks.join("");
      }

      function normaliseMarkdownSpacing(markdown) {
        return markdown
          .replace(/\u00a0/g, " ")
          .replace(/[ \t]+\n/g, "\n")
          .replace(/\n{3,}/g, "\n\n")
          .trim();
      }

      function inlineNodesToMarkdown(nodes) {
        let text = "";
        nodes.forEach((node) => {
          if (node.nodeType === Node.TEXT_NODE) {
            text += node.textContent || "";
            return;
          }

          if (node.nodeType !== Node.ELEMENT_NODE) {
            return;
          }

          const tag = node.tagName.toLowerCase();
          if (tag === "br") {
            text += "\n";
            return;
          }
          if (tag === "strong" || tag === "b") {
            text += `**${inlineNodesToMarkdown(Array.from(node.childNodes)).trim()}**`;
            return;
          }
          if (tag === "em" || tag === "i") {
            text += `*${inlineNodesToMarkdown(Array.from(node.childNodes)).trim()}*`;
            return;
          }
          if (tag === "code") {
            text += `\`${(node.textContent || "").trim()}\``;
            return;
          }
          if (tag === "a") {
            const label = inlineNodesToMarkdown(Array.from(node.childNodes)).trim() || (node.textContent || "").trim();
            const href = node.getAttribute("href") || "";
            text += href ? `[${label}](${href})` : label;
            return;
          }
          text += inlineNodesToMarkdown(Array.from(node.childNodes));
        });
        return text.replace(/\u00a0/g, " ");
      }

      function blockToMarkdown(node) {
        if (node.nodeType === Node.TEXT_NODE) {
          const text = (node.textContent || "").trim();
          return text ? `${text}\n\n` : "";
        }

        if (node.nodeType !== Node.ELEMENT_NODE) {
          return "";
        }

        const tag = node.tagName.toLowerCase();

        if (tag === "h1" || tag === "h2" || tag === "h3" || tag === "h4" || tag === "h5" || tag === "h6") {
          const level = Number.parseInt(tag.slice(1), 10);
          const text = inlineNodesToMarkdown(Array.from(node.childNodes)).trim();
          return text ? `${"#".repeat(level)} ${text}\n\n` : "";
        }

        if (tag === "p") {
          const text = inlineNodesToMarkdown(Array.from(node.childNodes)).trim();
          return text ? `${text}\n\n` : "";
        }

        if (tag === "div") {
          const nestedBlocks = Array.from(node.children).filter((child) =>
            ["p", "div", "ul", "ol", "blockquote", "h1", "h2", "h3", "h4", "h5", "h6", "hr"].includes(child.tagName.toLowerCase()),
          );
          if (nestedBlocks.length) {
            return Array.from(node.childNodes).map(blockToMarkdown).join("");
          }
          const text = inlineNodesToMarkdown(Array.from(node.childNodes)).trim();
          return text ? `${text}\n\n` : "";
        }

        if (tag === "ul" || tag === "ol") {
          const items = Array.from(node.children)
            .filter((child) => child.tagName && child.tagName.toLowerCase() === "li")
            .map((child, index) => {
              const prefix = tag === "ol" ? `${index + 1}. ` : "- ";
              const line = inlineNodesToMarkdown(Array.from(child.childNodes)).trim();
              return `${prefix}${line}`;
            })
            .join("\n");
          return items ? `${items}\n\n` : "";
        }

        if (tag === "blockquote") {
          const content = Array.from(node.childNodes)
            .map(blockToMarkdown)
            .join("")
            .trim()
            .split("\n")
            .filter((line) => line.trim())
            .map((line) => `> ${line}`)
            .join("\n");
          return content ? `${content}\n\n` : "";
        }

        if (tag === "hr") {
          return "---\n\n";
        }

        return Array.from(node.childNodes).map(blockToMarkdown).join("");
      }

      function richEditorToMarkdown(editor) {
        return normaliseMarkdownSpacing(
          Array.from(editor.childNodes)
            .map(blockToMarkdown)
            .join(""),
        );
      }

      function updateRichEditorEmptyState(editor) {
        const hasText = (editor.textContent || "").replace(/\u00a0/g, " ").trim().length > 0;
        const hasStructuredContent = editor.querySelector("img, hr, ul, ol, blockquote");
        editor.classList.toggle("is-empty", !hasText && !hasStructuredContent);
      }

      function syncCompleteEditorToMarkdown() {
        if (!completeMarkdownField || !completeRichEditor) {
          return;
        }
        completeMarkdownField.value = richEditorToMarkdown(completeRichEditor);
        updateRichEditorEmptyState(completeRichEditor);
      }

      function applyBlockFormat(tagName) {
        if (!completeRichEditor) {
          return;
        }
        completeRichEditor.focus();
        document.execCommand("formatBlock", false, `<${tagName}>`);
        syncCompleteEditorToMarkdown();
      }

      function applyToolbarCommand(command) {
        if (!completeRichEditor) {
          return;
        }
        completeRichEditor.focus();
        if (command === "createLink") {
          const url = window.prompt("Enter a URL", "https://");
          if (!url) {
            return;
          }
          document.execCommand(command, false, url);
        } else {
          document.execCommand(command, false);
        }
        syncCompleteEditorToMarkdown();
      }

      document.querySelectorAll(".auto-grow").forEach((textarea) => {
        textarea.addEventListener("input", () => autoSizeTextarea(textarea));
      });

      selectedTickerRadios.forEach((radio) => {
        radio.addEventListener("change", () => {
          if (radio.checked) {
            syncTickerInputFromSelection(radio.value);
          }
        });
      });

      document.querySelectorAll("[data-add-brief-item]").forEach((button) => {
        button.addEventListener("click", () => {
          const key = button.dataset.briefKey;
          const placeholder = button.dataset.placeholder || "";
          const list = document.querySelector(`[data-brief-list="${key}"]`);
          if (!list) {
            return;
          }
          list.appendChild(buildBriefRow(`brief_${key}[]`, placeholder));
          requestAnimationFrame(refreshAutoGrowTextareas);
        });
      });

      document.addEventListener("click", (event) => {
        const target = event.target;
        if (!(target instanceof HTMLElement) || !target.hasAttribute("data-remove-brief-item")) {
          return;
        }
        const row = target.closest(".brief-item");
        const list = target.closest(".brief-items");
        if (!row || !list) {
          return;
        }
        const rows = list.querySelectorAll(".brief-item");
        if (rows.length === 1) {
          const input = row.querySelector("textarea");
          if (input) {
            input.value = "";
            autoSizeTextarea(input);
          }
          return;
        }
        row.remove();
        requestAnimationFrame(refreshAutoGrowTextareas);
      });

      if (completeMarkdownField && completeRichEditor) {
        completeRichEditor.innerHTML = markdownToHtml(completeMarkdownField.value || "");
        updateRichEditorEmptyState(completeRichEditor);
        completeRichEditor.addEventListener("input", syncCompleteEditorToMarkdown);
        completeRichEditor.addEventListener("blur", syncCompleteEditorToMarkdown);
      }

      if (completeToolbar) {
        completeToolbar.addEventListener("click", (event) => {
          const target = event.target;
          if (!(target instanceof HTMLElement)) {
            return;
          }
          if (target.dataset.command) {
            applyToolbarCommand(target.dataset.command);
            return;
          }
          if (target.dataset.block) {
            applyBlockFormat(target.dataset.block);
          }
        });
      }

      if (workspaceForm) {
        workspaceForm.addEventListener("submit", () => {
          syncCompleteEditorToMarkdown();
        });
      }

      window.addEventListener("load", refreshAutoGrowTextareas);
      window.addEventListener("resize", refreshAutoGrowTextareas);
      if (document.fonts && document.fonts.ready) {
        document.fonts.ready.then(() => {
          refreshAutoGrowTextareas();
        });
      }

      setActiveTab(activeTabInput.value || "research");
      requestAnimationFrame(refreshAutoGrowTextareas);
      syncCompleteEditorToMarkdown();
    </script>
  </body>
</html>
"""


def _blank_context(settings) -> dict[str, object]:
    return {
        "movers": [],
        "movers_json": "",
        "selected_ticker": "",
        "selected_company_name": "Choose a company",
        "selected_company_ticker": "",
        "selected_company_move": "",
        "fact_pack_json": "",
        "research_json": "",
        "research_notes": "",
        "brief_sections": _brief_sections_for_view(_empty_brief_sections()),
        "company_profile_section": _brief_section_view(_empty_brief_sections(), "company_profile"),
        "price_context_section": _brief_section_view(_empty_brief_sections(), "price_context"),
        "draft_prompt": "",
        "article_text": "",
        "complete_article_text": "",
        "article_sources": [],
        "error": "",
        "status_message": "",
        "limit": "3",
        "active_tab": "research",
        "openrouter_api_key": settings.openrouter_api_key,
        "research_openrouter_model": settings.openrouter_model,
        "article_openrouter_model": settings.article_openrouter_model,
        "final_details_openrouter_model": settings.final_details_openrouter_model,
        "output_dir": str(settings.output_dir.resolve()),
        "llm_provider": settings.llm_provider,
        "article_generation_model": f"openrouter · {settings.article_openrouter_model}",
    }


def _parse_json(text: str) -> dict | list | None:
    if not text:
        return None
    return json.loads(text)


def _normalise_items(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _fact_pack_from_dict(data: dict[str, object]) -> FactPack:
    performance = PricePerformance(**data["performance"])
    stats = StandardStats(**data["stats"])
    return FactPack(
        ticker=data["ticker"],
        performance=performance,
        stats=stats,
        source_notes=data.get("source_notes", []),
    )


def _research_brief_from_dict(data: dict[str, object]) -> ResearchBrief:
    return ResearchBrief(
        ticker=data["ticker"],
        likely_reason=data.get("likely_reason", ""),
        confidence=data.get("confidence", ""),
        evidence=data.get("evidence", []),
        recent_history=data.get("recent_history", []),
        caveats=data.get("caveats", []),
        article_angles=data.get("article_angles", []),
        raw_context=data.get("raw_context", {}),
        sector_backdrop=data.get("sector_backdrop", []),
        company_developments=data.get("company_developments", []),
        watch_items=data.get("watch_items", []),
    )


def _empty_brief_sections() -> dict[str, list[str]]:
    return {section["key"]: [] for section in BRIEF_SECTION_DEFS}


def _brief_sections_for_view(values: dict[str, list[str]]) -> list[dict[str, object]]:
    sections = []
    for section_def in BRIEF_SECTION_DEFS:
        key = section_def["key"]
        entries = values.get(key, [])
        sections.append(
            {
                "key": key,
                "title": section_def["title"],
                "note": section_def["note"],
                "placeholder": section_def["placeholder"],
                "entries": entries or [""],
            }
        )
    return sections


def _brief_section_view(values: dict[str, list[str]] | list[dict[str, object]], key: str) -> dict[str, object]:
    if isinstance(values, list):
        sections = values
    else:
        sections = _brief_sections_for_view(values)
    for section in sections:
        if section["key"] == key:
            return section
    for section_def in BRIEF_SECTION_DEFS:
        if section_def["key"] == key:
            return {
                "key": key,
                "title": section_def["title"],
                "note": section_def["note"],
                "placeholder": section_def["placeholder"],
                "entries": [""],
            }
    raise KeyError(key)


def _brief_sections_from_request(form) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    for section_def in BRIEF_SECTION_DEFS:
        field_name = f"brief_{section_def['key']}[]"
        values[section_def["key"]] = [
            item.strip()
            for item in form.getlist(field_name)
            if item.strip()
        ]
    return values


def _company_profile_items(fact_pack: FactPack) -> list[str]:
    stats = fact_pack.stats
    perf = fact_pack.performance
    items = []
    if stats.sector:
        items.append(f"Sector: {stats.sector}")
    if stats.industry:
        items.append(f"Industry: {stats.industry}")
    if stats.price is not None:
        items.append(f"Current price: {_format_number(stats.price)}")
    if perf.day_change_pct is not None:
        items.append(f"1-day move: {_format_percent(perf.day_change_pct)}")
    if perf.one_year_change_pct is not None:
        items.append(f"1-year move: {_format_percent(perf.one_year_change_pct)}")
    if stats.market_cap is not None:
        items.append(f"Market cap: {_format_large_number(stats.market_cap)}")
    if stats.dividend_yield is not None:
        items.append(f"Dividend yield: {_format_percent(stats.dividend_yield)}")
    if stats.pe_ratio is not None:
        items.append(f"P/E ratio: {_format_number(stats.pe_ratio)}")
    return items


def _price_context_items(brief: ResearchBrief) -> list[str]:
    items = []
    for item in brief.raw_context.get("price_context", [])[:5]:
        date = item.get("date")
        close = item.get("close")
        if date or close is not None:
            items.append(f"{date}: close {close}")
    return items


def _brief_sections_from_brief(fact_pack: FactPack, brief: ResearchBrief) -> dict[str, list[str]]:
    return {
        "story_angle": _normalise_items(brief.article_angles) or _normalise_items(brief.likely_reason),
        "evidence_context": (
            _normalise_items(brief.evidence)
            + _normalise_items(brief.recent_history)
            + _normalise_items(brief.sector_backdrop)
        ),
        "company_profile": _company_profile_items(fact_pack),
        "price_context": _price_context_items(brief),
        "company_developments": _normalise_items(brief.company_developments),
        "watch_next": _normalise_items(brief.caveats) + _normalise_items(brief.watch_items),
    }


def _primary_story_angle(brief_sections: dict[str, list[str]]) -> str:
    story_angles = brief_sections.get("story_angle", [])
    return story_angles[0] if story_angles else ""


def _render_research_notes_from_sections(
    brief_sections: dict[str, list[str]],
) -> str:
    lines: list[str] = []

    evidence_items = brief_sections.get("evidence_context", []) + brief_sections.get("price_context", [])
    if evidence_items:
        lines.append("Evidence and context")
        lines.extend(f"- {item}" for item in evidence_items)
        lines.append("")

    company_profile_items = brief_sections.get("company_profile", [])
    if company_profile_items:
        lines.append("Company profile")
        lines.extend(f"- {item}" for item in company_profile_items)
        lines.append("")

    company_development_items = brief_sections.get("company_developments", [])
    if company_development_items:
        lines.append("Company developments")
        lines.extend(f"- {item}" for item in company_development_items)
        lines.append("")

    watch_next_items = brief_sections.get("watch_next", [])
    if watch_next_items:
        lines.append("What investors should watch next")
        lines.extend(f"- {item}" for item in watch_next_items)
        lines.append("")

    if lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines).strip()


def _format_number(value: float | int | None, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    return f"{value:,.{digits}f}"


def _format_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:,.2f}%"


def _format_large_number(value: float | None) -> str:
    if value is None:
        return "n/a"
    abs_value = abs(value)
    if abs_value >= 1_000_000_000:
        return f"{value / 1_000_000_000:,.2f}bn"
    if abs_value >= 1_000_000:
        return f"{value / 1_000_000:,.2f}m"
    return f"{value:,.0f}"


def _build_fact_rows(fact_pack: FactPack) -> list[dict[str, str]]:
    stats = fact_pack.stats
    perf = fact_pack.performance
    rows = [
        {"label": "Company", "value": stats.company_name or fact_pack.ticker},
        {"label": "Sector", "value": stats.sector or "n/a"},
        {"label": "Industry", "value": stats.industry or "n/a"},
        {"label": "Current price", "value": _format_number(stats.price)},
        {"label": "1-day move", "value": _format_percent(perf.day_change_pct)},
        {"label": "1-year move", "value": _format_percent(perf.one_year_change_pct)},
        {"label": "Market cap", "value": _format_large_number(stats.market_cap)},
        {"label": "Dividend yield", "value": _format_percent(stats.dividend_yield)},
        {"label": "P/E ratio", "value": _format_number(stats.pe_ratio)},
    ]
    return [row for row in rows if row["value"] != "n/a" or row["label"] in {"Company", "Sector", "Industry"}]


def _build_price_context_rows(brief: ResearchBrief) -> list[dict[str, str]]:
    rows = []
    for item in brief.raw_context.get("price_context", [])[:5]:
        rows.append(
            {
                "date": str(item.get("date", "n/a")),
                "close": str(item.get("close", "n/a")),
            }
        )
    return rows


def _build_article_sources(brief: ResearchBrief) -> list[dict[str, str]]:
    sources = []
    for item in brief.raw_context.get("article_summaries", [])[:3]:
        sources.append(
            {
                "title": str(item.get("title") or "Untitled source"),
                "summary": str(item.get("summary") or "No summary available."),
                "date": str(item.get("publishedDate") or ""),
                "url": str(item.get("url") or ""),
            }
        )
    return sources


def _normalise_ticker(value: str) -> str:
    ticker = value.strip().upper()
    if ticker and not ticker.endswith(".L"):
        ticker = f"{ticker}.L"
    return ticker


def _pick_ticker(context: dict[str, object]) -> str:
    selected_ticker = _normalise_ticker(str(context.get("selected_ticker", "")))
    return selected_ticker


def _selected_company_from_movers(movers: list[dict[str, object]], ticker: str) -> tuple[str, str]:
    for mover in movers:
        if str(mover.get("ticker", "")).upper() == ticker.upper():
            move = mover.get("day_change_pct")
            move_text = _format_percent(float(move)) if move is not None else "n/a"
            return str(mover.get("company_name") or ticker), move_text
    return ticker or "Choose a company", ""


def _hydrate_context(settings, context: dict[str, object]) -> dict[str, object]:
    hydrated = dict(context)
    brief_sections_view = hydrated.get("brief_sections", _brief_sections_for_view(_empty_brief_sections()))
    hydrated.update(
        {
            "movers": [],
            "brief_sections": brief_sections_view,
            "company_profile_section": _brief_section_view(_empty_brief_sections(), "company_profile"),
            "price_context_section": _brief_section_view(_empty_brief_sections(), "price_context"),
            "article_sources": [],
            "selected_company_name": "Choose a company",
            "selected_company_ticker": "",
            "selected_company_move": "",
        }
    )

    movers_data = _parse_json(str(hydrated.get("movers_json", ""))) or []
    if isinstance(movers_data, list):
        hydrated["movers"] = movers_data

    selected_ticker = _pick_ticker(hydrated)
    hydrated["selected_company_ticker"] = selected_ticker

    fact_pack_json = str(hydrated.get("fact_pack_json", ""))
    if fact_pack_json:
        fact_pack_dict = _parse_json(fact_pack_json)
        if isinstance(fact_pack_dict, dict):
            fact_pack = _fact_pack_from_dict(fact_pack_dict)
            hydrated["selected_company_name"] = fact_pack.stats.company_name or fact_pack.ticker
            hydrated["selected_company_ticker"] = fact_pack.ticker
            hydrated["selected_company_move"] = _format_percent(fact_pack.performance.day_change_pct)

    research_json = str(hydrated.get("research_json", ""))
    if research_json:
        research_dict = _parse_json(research_json)
        if isinstance(research_dict, dict):
            brief = _research_brief_from_dict(research_dict)
            hydrated["article_sources"] = _build_article_sources(brief)

    if hydrated["selected_company_name"] == "Choose a company":
        company_name, move_text = _selected_company_from_movers(hydrated["movers"], selected_ticker)
        hydrated["selected_company_name"] = company_name
        hydrated["selected_company_move"] = move_text
    elif not hydrated["selected_company_move"]:
        _, move_text = _selected_company_from_movers(hydrated["movers"], selected_ticker)
        hydrated["selected_company_move"] = move_text

    hydrated["output_dir"] = str(settings.output_dir.resolve())
    hydrated["llm_provider"] = settings.llm_provider
    hydrated["article_generation_model"] = f"openrouter · {settings.article_openrouter_model}"
    hydrated["openrouter_api_key"] = str(hydrated.get("openrouter_api_key", settings.openrouter_api_key))
    hydrated["research_openrouter_model"] = str(hydrated.get("research_openrouter_model", settings.openrouter_model))
    hydrated["article_openrouter_model"] = str(hydrated.get("article_openrouter_model", settings.article_openrouter_model))
    hydrated["final_details_openrouter_model"] = str(
        hydrated.get("final_details_openrouter_model", settings.final_details_openrouter_model)
    )
    hydrated["status_message"] = str(hydrated.get("status_message", ""))
    hydrated["company_profile_section"] = _brief_section_view(
        hydrated["brief_sections"],
        "company_profile",
    )
    hydrated["price_context_section"] = _brief_section_view(
        hydrated["brief_sections"],
        "price_context",
    )
    return hydrated


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index() -> str:
        settings = load_settings()
        return render_template_string(APP_TEMPLATE, **_blank_context(settings))

    @app.post("/")
    def run_action() -> str:
        settings = load_settings()
        context = _blank_context(settings)
        brief_section_values = _brief_sections_from_request(request.form)
        context.update(
            {
                "movers_json": request.form.get("movers_json", ""),
                "selected_ticker": request.form.get("selected_ticker", "") or request.form.get("selected_ticker_choice", ""),
                "fact_pack_json": request.form.get("fact_pack_json", ""),
                "research_json": request.form.get("research_json", ""),
                "draft_prompt": request.form.get("draft_prompt", ""),
                "article_text": request.form.get("article_text", ""),
                "complete_article_text": request.form.get("complete_article_text", ""),
                "limit": request.form.get("limit", "3"),
                "active_tab": request.form.get("active_tab", "research"),
                "openrouter_api_key": request.form.get("openrouter_api_key", settings.openrouter_api_key),
                "research_openrouter_model": request.form.get("research_openrouter_model", settings.openrouter_model),
                "article_openrouter_model": request.form.get("article_openrouter_model", settings.article_openrouter_model),
                "final_details_openrouter_model": request.form.get(
                    "final_details_openrouter_model",
                    settings.final_details_openrouter_model,
                ),
            }
        )
        context["brief_sections"] = _brief_sections_for_view(brief_section_values)
        context["research_notes"] = _render_research_notes_from_sections(brief_section_values)

        try:
            action = request.form.get("action", "find_movers")
            pipeline = Pipeline(settings)

            if action == "save_settings":
                openrouter_api_key = str(context["openrouter_api_key"]).strip()
                research_model = str(context["research_openrouter_model"]).strip()
                article_model = str(context["article_openrouter_model"]).strip()
                final_details_model = str(context["final_details_openrouter_model"]).strip()
                if not research_model or not article_model or not final_details_model:
                    raise ValueError("Enter a model for research, article generation, and final details.")
                save_settings_values(
                    {
                        "LLM_PROVIDER": "openrouter",
                        "OPENROUTER_API_KEY": openrouter_api_key,
                        "OPENROUTER_MODEL": research_model,
                        "ARTICLE_OPENROUTER_MODEL": article_model,
                        "FINAL_DETAILS_OPENROUTER_MODEL": final_details_model,
                    }
                )
                settings = load_settings()
                context.update(
                    {
                        "openrouter_api_key": settings.openrouter_api_key,
                        "research_openrouter_model": settings.openrouter_model,
                        "article_openrouter_model": settings.article_openrouter_model,
                        "final_details_openrouter_model": settings.final_details_openrouter_model,
                        "status_message": "Settings saved.",
                        "active_tab": "settings",
                    }
                )

            elif action == "find_movers":
                movers = pipeline.scan_uk_market(
                    min_abs_day_move=0.0,
                    limit=int(str(context["limit"])),
                )
                context["movers_json"] = json.dumps([item.to_dict() for item in movers])
                mover_tickers = {item.ticker for item in movers}
                if movers and (not _pick_ticker(context) or str(context["selected_ticker"]) not in mover_tickers):
                    context["selected_ticker"] = movers[0].ticker
                context["active_tab"] = "research"

            elif action == "research":
                ticker = _pick_ticker(context)
                if not ticker:
                    raise ValueError("Choose a ticker from the movers list or enter a ticker.")
                fact_pack = pipeline.fact_pack(ticker)
                brief = pipeline.research(
                    ticker,
                    fact_pack,
                )
                brief_section_values = _brief_sections_from_brief(fact_pack, brief)
                context["selected_ticker"] = ticker
                context["fact_pack_json"] = json.dumps(fact_pack.to_dict())
                context["research_json"] = json.dumps(brief.to_dict())
                context["brief_sections"] = _brief_sections_for_view(brief_section_values)
                context["research_notes"] = _render_research_notes_from_sections(brief_section_values)
                context["draft_prompt"] = pipeline.build_article_prompt(
                    fact_pack=fact_pack,
                    research=brief,
                    story_angle=_primary_story_angle(brief_section_values),
                    research_notes=context["research_notes"],
                )
                context["article_text"] = ""
                context["complete_article_text"] = ""
                context["active_tab"] = "research"

            elif action == "refresh_prompt":
                fact_pack_dict = _parse_json(str(context["fact_pack_json"]))
                if not fact_pack_dict or not isinstance(fact_pack_dict, dict):
                    raise ValueError("Run research first so there is material to build the prompt from.")
                fact_pack = _fact_pack_from_dict(fact_pack_dict)
                research_dict = _parse_json(str(context["research_json"]))
                brief = _research_brief_from_dict(research_dict) if isinstance(research_dict, dict) else None
                context["draft_prompt"] = pipeline.build_article_prompt(
                    fact_pack=fact_pack,
                    research=brief,
                    story_angle=_primary_story_angle(brief_section_values),
                    research_notes=str(context["research_notes"]),
                )
                context["active_tab"] = "write"

            elif action == "generate_article":
                ticker = _pick_ticker(context)
                if not ticker:
                    fact_pack_dict = _parse_json(str(context["fact_pack_json"]))
                    if isinstance(fact_pack_dict, dict):
                        ticker = str(fact_pack_dict.get("ticker", "")).strip().upper()
                if not ticker:
                    raise ValueError("Choose a company and build research before generating a draft.")
                prompt_text = str(context["draft_prompt"]).strip()
                if not prompt_text:
                    raise ValueError("The article-generation prompt is empty.")
                context["article_text"] = pipeline.draft_from_prompt(ticker, prompt_text)
                context["complete_article_text"] = ""
                context["active_tab"] = "write"

            elif action == "final_details_pass":
                ticker = _pick_ticker(context)
                if not ticker:
                    fact_pack_dict = _parse_json(str(context["fact_pack_json"]))
                    if isinstance(fact_pack_dict, dict):
                        ticker = str(fact_pack_dict.get("ticker", "")).strip().upper()
                if not ticker:
                    raise ValueError("Choose a company and build research before running the final details pass.")
                article_text = str(context["article_text"]).strip()
                if not article_text:
                    raise ValueError("There is no article text to refine yet.")
                context["complete_article_text"] = pipeline.final_details_pass(ticker, article_text)
                context["active_tab"] = "complete"

            elif action == "save_complete_article":
                ticker = _pick_ticker(context)
                if not ticker:
                    fact_pack_dict = _parse_json(str(context["fact_pack_json"]))
                    if isinstance(fact_pack_dict, dict):
                        ticker = str(fact_pack_dict.get("ticker", "")).strip().upper()
                if not ticker:
                    raise ValueError("Choose a company before saving the completed article.")
                complete_article_text = str(context["complete_article_text"])
                if not complete_article_text.strip():
                    raise ValueError("There is no completed article text to save yet.")
                pipeline.save_complete_article(ticker, complete_article_text)
                context["active_tab"] = "complete"

        except Exception as exc:
            context["error"] = str(exc)

        hydrated = _hydrate_context(settings, context)
        return render_template_string(APP_TEMPLATE, **hydrated)

    return app


def main() -> int:
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

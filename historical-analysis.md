---
layout: default
title: "Historical Analysis"
description: "Historical residential timeline analysis with estimated PM2.5 exposure"
permalink: historical-analysis/
---

# Historical Analysis

[← Back to Home]({{ '/' | relative_url }})

---

## Move History as a Timeline

This tab focuses on storytelling over time: where someone lived, when they moved, and how estimated PM2.5 exposure changed between moves.

Use CSV or JSON history input to:
- Plot addresses in chronological order on a map
- Connect moves as a timeline path
- Color markers by era or by estimated PM2.5
- See a stepped PM2.5 time series with move-by-move change summaries

{% include move_history_map.html %}

---

## ZIP Code PM2.5 Exposure Tool

{% include zip_exposure_tool.html default_source="purpleair" %}

---

[← Back to Home]({{ '/' | relative_url }}) | [View PurpleAir Analysis →]({{ '/purpleair-analysis' | relative_url }}) | [View EPA Analysis →]({{ '/epa-analysis' | relative_url }})

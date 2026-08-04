---
permalink: /
title: "Brian W. Locke, MD, MSCI"
description: "Pulmonary and critical care physician-scientist studying respiratory failure, diagnostic evidence, and reproducible research systems."
---
{% assign person = site.data.person %}
{% assign work = site.data.generated.work %}

<section class="home-hero site-container section">
  <div class="home-hero__text">
    <h1>{{ person.name }}</h1>
    {% include affiliations.html %}
    <p class="hero-statement">{{ person.research_statement }}</p>
    <p class="clinical-context">Clinical practice: {{ person.clinical_context | join: " and " }}.</p>
    {% include profile-links.html %}
  </div>
  <picture class="home-hero__portrait">
    <source srcset="{{ person.image.webp }}" type="image/webp">
    <img src="{{ person.image.jpeg }}" width="{{ person.image.width }}" height="{{ person.image.height }}" alt="{{ person.image.alt }}">
  </picture>
</section>

<section class="section section--surface">
  <div class="site-container">
    <h2>Research themes</h2>
    <div class="theme-grid">
      <article><h3>Respiratory failure</h3><p>Measurement, hypercapnia, and care after hospitalization.</p></article>
      <article><h3>Evidence and prediction</h3><p>Diagnostic reasoning, clinical prediction, and causal methods.</p></article>
      <article><h3>Research infrastructure</h3><p>Reproducible analysis, linked clinical data, and pragmatic trials.</p></article>
    </div>
  </div>
</section>

<section class="site-container section" id="selected-work">
  <header class="section-heading prose"><h2>Selected work</h2><p>Recent publications that represent the breadth of the current research program.</p></header>
  <div class="featured-grid">
    {% assign homepage_items = work.items | where_exp: "item", "item.selected.homepage == true" %}
    {% for item in homepage_items %}{% include work-card.html item=item %}{% endfor %}
  </div>
  <p class="closing-link">View <a href="/work/">all selected work</a> or the <a href="/cv/">full curriculum vitae</a>.</p>
</section>

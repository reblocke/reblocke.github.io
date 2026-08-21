---
permalink: /
title: "Brian W. Locke, MD, MSCI"
seo_title: "Brian W. Locke, MD, MSCI | Pulmonary & Critical Care Research"
description: "Brian W. Locke is a pulmonary and critical care physician-scientist studying respiratory failure, clinical data, prediction, causal inference, and pragmatic trials."
schema_type: "WebPage"
schema_main_entity: true
---
{% assign person = site.data.person %}
{% assign work = site.data.generated.work %}
{% assign respiratory_topic = work.topics | where: "id", "hypercapnic-respiratory-failure" | first %}

<section class="home-hero site-container section">
  <div class="home-hero__text">
    <h1>{{ person.name }}</h1>
    {% include affiliations.html %}
    <p class="hero-statement">{{ person.research_statement }}</p>
    {% include profile-links.html %}
  </div>
  <picture class="home-hero__portrait">
    <source srcset="{{ person.image.webp }}" type="image/webp">
    <img src="{{ person.image.jpeg }}" width="{{ person.image.width }}" height="{{ person.image.height }}" alt="{{ person.image.alt }}">
  </picture>
</section>

<section class="site-container section prose" aria-labelledby="about-heading">
  <h2 id="about-heading">About</h2>
  <p>{{ person.summary }}</p>
  <p><a href="/bio/">Full biography</a></p>
</section>

<section class="section section--surface">
  <div class="site-container">
    <h2>Research themes</h2>
    <div class="theme-grid">
      {% for theme in person.research_themes %}
        <article><h3>{{ theme.title }}</h3><p>{{ theme.description }}</p></article>
      {% endfor %}
    </div>
    {% if respiratory_topic %}<p class="closing-link">Explore research on <a href="{{ respiratory_topic.permalink }}">{{ respiratory_topic.title }}</a>.</p>{% endif %}
  </div>
</section>

<section class="site-container section" id="selected-work">
  <header class="section-heading prose"><h2>Selected work</h2><p>Recent publications that represent the breadth of the current research program.</p></header>
  <div class="featured-grid">
    {% assign homepage_items = work.items | where_exp: "item", "item.selected.homepage == true" %}
    {% for item in homepage_items %}{% include work-card.html item=item %}{% endfor %}
  </div>
  <p class="closing-link">View <a href="/work/">selected work</a>, browse <a href="/publications/">all publications</a>, or read the <a href="/cv/">public curriculum vitae</a>.</p>
</section>

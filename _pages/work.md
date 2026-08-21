---
permalink: /work/
title: "Work"
seo_title: "Respiratory Failure Research & Software | Brian W. Locke"
description: "Research, publications, software, and teaching by Brian W. Locke on hypercapnic respiratory failure, respiratory measurement, clinical data, and prediction."
schema_type: "CollectionPage"
---
{% assign work = site.data.generated.work %}
{% assign respiratory_topic = work.topics | where: "id", "hypercapnic-respiratory-failure" | first %}
<article class="site-container page page--work">
  <header class="page-header prose">
    <h1>Work</h1>
    <p>Selected research, software, and teaching resources. Projects are grouped by the clinical or methodological question they address, with papers, code, and supporting materials linked together.</p>
    <p>Browse the <a href="/publications/">complete publication list</a>{% if respiratory_topic %}, or explore research on <a href="{{ respiratory_topic.permalink }}">{{ respiratory_topic.title }}</a>{% endif %}.</p>
    <nav class="anchor-index" aria-label="Work sections">
      {% for section in work.sections %}<a href="#{{ section.key }}">{{ section.title }}</a>{% endfor %}
    </nav>
  </header>

  {% for section in work.sections %}
    <section class="work-section" id="{{ section.key }}">
      <h2>{{ section.title }}</h2>
      {% assign section_items = work.items | where: "section", section.key %}
      {% for item in section_items %}
        {% if item.selected.work %}
          {% include work-list-item.html item=item %}
        {% endif %}
      {% endfor %}
      {% assign section_repositories = work.repositories | where: "section", section.key %}
      {% for repo in section_repositories %}
        {% if repo.selected_work and repo.display_with == nil %}
          <article class="work-item">
            <p class="item-meta">{{ repo.artifact_type }}{% if repo.analysis_language %} · {{ repo.analysis_language }}{% endif %}</p>
            <h3>{{ repo.title }}</h3>
            <p class="prose">{{ repo.data_availability }}</p>
            <p class="item-links">
              <a href="https://github.com/{{ repo.repository }}">Repository</a>
              {% if repo.live_url %}<a href="{{ repo.live_url }}">{{ repo.live_label }}</a>{% endif %}
            </p>
          </article>
        {% endif %}
      {% endfor %}
    </section>
  {% endfor %}
  <p class="catalog-link">For the complete machine-readable catalog, see <a href="/research-repositories/">all public research repositories</a>.</p>
</article>

---
permalink: /work/
title: "Work"
description: "Selected research, software, and teaching resources grouped by the questions they address."
---
{% assign work = site.data.generated.work %}
<article class="site-container page page--work">
  <header class="page-header prose">
    <h1>Work</h1>
    <p>Selected research, software, and teaching resources. Projects are grouped by the clinical or methodological question they address, with papers, code, and supporting materials linked together.</p>
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
          <article class="work-item">
            <p class="item-meta">{{ item.year }} · {{ item.type | replace: '-', ' ' | capitalize }}</p>
            <h3>{{ item.title }}</h3>
            {% if item.summary %}<p class="prose">{{ item.summary }}</p>{% endif %}
            <p class="item-links">
              {% if item.doi %}<a href="https://doi.org/{{ item.doi }}">DOI</a>{% endif %}
              {% if item.pmid %}<a href="https://pubmed.ncbi.nlm.nih.gov/{{ item.pmid }}/">PubMed</a>{% endif %}
              {% for related_id in item.related_ids %}
                {% assign repo = work.repositories | where: "id", related_id | first %}
                {% if repo %}<a href="https://github.com/{{ repo.repository }}">Repository</a>{% endif %}
              {% endfor %}
            </p>
          </article>
        {% endif %}
      {% endfor %}
      {% assign section_repositories = work.repositories | where: "section", section.key %}
      {% for repo in section_repositories %}
        {% if repo.selected_work and repo.display_with == nil %}
          <article class="work-item">
            <p class="item-meta">{{ repo.artifact_type }}{% if repo.analysis_language %} · {{ repo.analysis_language }}{% endif %}</p>
            <h3>{{ repo.title }}</h3>
            <p class="prose">{{ repo.data_availability }}</p>
            <p class="item-links"><a href="https://github.com/{{ repo.repository }}">Repository</a></p>
          </article>
        {% endif %}
      {% endfor %}
    </section>
  {% endfor %}
  <p class="catalog-link">For the complete machine-readable catalog, see <a href="/research-repositories/">all public research repositories</a>.</p>
</article>

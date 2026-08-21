---
permalink: /research-repositories/
title: "Public Research Repositories"
seo_title: "Open Research Code & Repositories | Brian W. Locke"
description: "Public research and teaching repositories associated with Brian W. Locke, with methods, analysis languages, data-availability notes, and durable source links."
schema_type: "CollectionPage"
---
<article class="site-container page page--catalog">
  <header class="page-header prose"><h1>Public research repositories</h1><p>This secondary catalog lists durable public repository metadata. Scholarly selection and interpretation appear on the <a href="/work/">Work page</a>.</p></header>
  <div class="repository-list">
    {% for repo in site.data.generated.research_repositories %}
      <article class="repository-item">
        <h2><a href="{{ repo.public_url }}">{{ repo.title }}</a></h2>
        <p>{{ repo.artifact_type }}{% if repo.analysis_language %} · {{ repo.analysis_language }}{% endif %}</p>
        <p class="muted">{{ repo.data_availability }}</p>
        {% if repo.live_url %}<p class="item-links"><a href="{{ repo.live_url }}">{{ repo.live_label }}</a></p>{% endif %}
      </article>
    {% endfor %}
  </div>
  <p>Download as <a href="/research-repositories.json">JSON</a> or <a href="/research-repositories.csv">CSV</a>.</p>
</article>

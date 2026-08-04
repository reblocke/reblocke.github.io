---
permalink: /research-repositories/
title: "Public Research Repositories"
description: "A stable machine-readable catalog of public research and teaching repositories."
---
<article class="site-container page page--catalog">
  <header class="page-header prose"><h1>Public research repositories</h1><p>This secondary catalog lists durable public repository metadata. Scholarly selection and interpretation appear on the <a href="/work/">Work page</a>.</p></header>
  <div class="repository-list">
    {% for repo in site.data.generated.research_repositories %}
      <article class="repository-item"><h2><a href="{{ repo.public_url }}">{{ repo.title }}</a></h2><p>{{ repo.artifact_type }}{% if repo.analysis_language %} · {{ repo.analysis_language }}{% endif %}</p><p class="muted">{{ repo.data_availability }}</p></article>
    {% endfor %}
  </div>
  <p>Download as <a href="/research-repositories.json">JSON</a> or <a href="/research-repositories.csv">CSV</a>.</p>
</article>

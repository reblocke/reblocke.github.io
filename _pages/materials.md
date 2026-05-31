---
layout: splash
title: "Materials"
permalink: /materials/
excerpt: "GitHub-accessible code, teaching materials, and project artifacts."
author_profile: false
redirect_from:
  - /projects/
---

{% include base_path %}

<section class="materials-page">
  <header class="section-header">
    <h1>Materials</h1>
    <p>
      Selected public code, teaching materials, reproducible analyses, and project
      artifacts. The curated list below is static; the live GitHub index appears
      afterward when JavaScript is available.
    </p>
  </header>

  {% for group in site.data.selected_materials.groups %}
    <section class="content-section">
      <h2>{{ group.title }}</h2>
      <div class="materials-list materials-list--curated">
        {% for material in site.data.selected_materials.materials %}
          {% if material.category == group.key %}
            <article class="materials-item">
              <h3><a href="{{ material.repository_url }}">{{ material.title }}</a></h3>
              <p class="materials-item__description">{{ material.description }}</p>
              <p class="materials-item__meta">
                {{ material.type | capitalize }}{% if material.language %} / {{ material.language }}{% endif %}{% if material.related_publication %}{% unless material.related_publication == "" %} / Related work: {{ material.related_publication }}{% endunless %}{% endif %}
              </p>
            </article>
          {% endif %}
        {% endfor %}
      </div>
    </section>
  {% endfor %}

  <section class="content-section">
    <h2>Live GitHub Index</h2>
    <p>
      The live index loads public repositories from GitHub, sorted by recent
      updates. Forks are excluded by default.
    </p>

    <div class="materials-controls" aria-label="Materials filters">
      <div class="materials-search">
        <label for="materials-search">Search materials</label>
        <input id="materials-search" type="search" placeholder="Search by name, description, or language">
      </div>
      <label class="materials-toggle" for="materials-show-forks">
        <input id="materials-show-forks" type="checkbox">
        Include forks
      </label>
    </div>

    <p id="materials-status" class="materials-status" role="status">Loading public GitHub materials...</p>

    <div
      id="github-materials"
      class="materials-list"
      data-owner="{{ site.author.github | default: 'reblocke' }}"
      data-profile-url="https://github.com/{{ site.author.github | default: 'reblocke' }}"
    ></div>

    <noscript>
      <p class="notice--info">
        JavaScript is required for the live GitHub index. Browse the public repositories
        directly at <a href="https://github.com/reblocke">github.com/reblocke</a>.
      </p>
    </noscript>
  </section>
</section>

<script src="{{ "/assets/js/github-materials.js" | prepend: base_path }}" defer></script>

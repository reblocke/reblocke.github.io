---
layout: splash
title: "Selected Publications"
permalink: /publications/
excerpt: "Selected peer-reviewed publications and scholarly products."
author_profile: false
---

{% include base_path %}
{% assign publications = site.data.selected_publications.publications %}

<section class="content-page">
  <header class="section-header">
    <h1>Selected Publications</h1>
    <p>
      A curated list of peer-reviewed publications, reviews, editorials, and
      scholarly products. Full publication records are available through
      <a href="https://scholar.google.com/citations?hl=en&amp;user=O1nydc8AAAAJ">Google Scholar</a>
      and <a href="https://orcid.org/0000-0002-3588-5238">ORCID</a>.
    </p>
  </header>

  {% for group in site.data.selected_publications.groups %}
    <section class="content-section">
      <h2>{{ group.title }}</h2>
      <div class="publication-list">
        {% for publication in publications %}
          {% if publication.group == group.key %}
            <article class="publication-item">
              <h3>{{ publication.title }}</h3>
              <p class="publication-item__meta">
                {{ publication.authors }}. <em>{{ publication.venue }}</em>. {{ publication.year }}.
              </p>
              {% if publication.doi %}
                <p class="publication-item__links">
                  DOI: <a href="{{ publication.url }}">{{ publication.doi }}</a>
                </p>
              {% endif %}
            </article>
          {% endif %}
        {% endfor %}
      </div>
    </section>
  {% endfor %}
</section>

---
permalink: /publications/
title: "Publications"
seo_title: "Publications | Brian W. Locke, MD, MSCI"
description: "Peer-reviewed publications, reviews, editorials, preprints, and scholarly products by Brian W. Locke, with DOI and PubMed links."
schema_type: "CollectionPage"
---
{% assign person = site.data.person %}
{% assign work = site.data.generated.work %}
<article class="site-container page page--cv">
  <header class="page-header prose">
    <h1>Publications</h1>
    <p>Journal articles, conference papers, preprints, commentaries, and letters from the public publication record. For a curated view, see <a href="/work/">selected work</a>; additional records are available through <a href="{{ person.profiles.google_scholar }}">Google Scholar</a> and <a href="{{ person.profiles.orcid }}">ORCID</a>.</p>
  </header>

  <section class="cv-section" aria-labelledby="publication-list-heading">
    <h2 id="publication-list-heading">Publication list</h2>
    <ol class="citation-list">
      {% for item in work.items %}
        {% if item.type != "abstract" %}{% include publication-citation.html item=item %}{% endif %}
      {% endfor %}
    </ol>
  </section>
</article>

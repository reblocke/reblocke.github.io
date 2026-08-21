---
permalink: /bio/
title: "Biography"
seo_title: "Brian W. Locke, MD, MSCI | Physician-Scientist Biography"
description: "Biography of Brian W. Locke, MD, MSCI, an Intermountain Health pulmonary and critical care physician-scientist and University of Utah fellowship faculty member."
schema_type: "ProfilePage"
---
{% assign person = site.data.person %}
<article class="site-container page">
  <header class="page-header prose">
    <h1>Biography</h1>
    <p class="cv-name">{{ person.name }}</p>
  </header>

  <div class="prose">
    {% for paragraph in person.biography %}
      <p>{{ paragraph }}</p>
    {% endfor %}
    <p>Explore <a href="/work/">selected work</a> or the <a href="/cv/">curriculum vitae</a>.</p>
  </div>
</article>

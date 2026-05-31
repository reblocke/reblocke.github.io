---
layout: splash
title: "Sitemap"
permalink: /sitemap/
author_profile: false
---

{% include base_path %}

<section class="content-page">
  <header class="section-header">
    <h1>Sitemap</h1>
    <p>
      Intentional public pages on this academic website. An XML version is
      available at <a href="{{ "/sitemap.xml" | prepend: base_path }}">sitemap.xml</a>.
    </p>
  </header>

  <ul class="cv-list">
    <li><a href="{{ "/" | prepend: base_path }}">About</a></li>
    <li><a href="{{ "/materials/" | prepend: base_path }}">Materials</a></li>
    <li><a href="{{ "/cv/" | prepend: base_path }}">CV</a></li>
    <li><a href="{{ "/publications/" | prepend: base_path }}">Selected Publications</a></li>
    <li><a href="{{ "/talks/" | prepend: base_path }}">National Abstracts and Presentations</a></li>
    <li><a href="{{ "/teaching/" | prepend: base_path }}">Teaching</a></li>
  </ul>
</section>

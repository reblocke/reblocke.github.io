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
      Public GitHub-accessible code, teaching materials, reproducible analyses, and
      project artifacts. This index refreshes from GitHub when the page loads.
    </p>
  </header>

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

<script src="{{ "/assets/js/github-materials.js" | prepend: base_path }}" defer></script>

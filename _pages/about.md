---
layout: splash
permalink: /
title: "Brian W Locke, MD, MSCI"
excerpt: "Pulmonary and critical care physician-scientist focused on respiratory failure, diagnostic evidence, clinical prediction, and reproducible research informatics."
author_profile: false
redirect_from:
  - /about/
  - /about.html
---

{% assign profile = site.data.profile %}
{% include base_path %}

<section class="home-hero">
  <div class="home-hero__text">
    <h1>{{ profile.name }}</h1>
    <p class="home-hero__purpose">{{ profile.career_purpose }}</p>
    <p class="home-hero__title">{{ profile.primary_title }}</p>
    <p class="home-hero__summary">{{ profile.summary }}</p>
    <ul class="profile-links" aria-label="Profile links">
      {% for link in profile.links %}
        <li>
          <a href="{{ link.url }}">
            <i class="{{ link.icon }}" aria-hidden="true"></i>
            <span>{{ link.label }}</span>
          </a>
        </li>
      {% endfor %}
    </ul>
  </div>
  <div class="home-hero__image">
    <img src="{{ "/images/profile.JPG" | prepend: base_path }}" alt="{{ profile.name }}">
  </div>
</section>

<section class="home-section">
  <h2>About</h2>
  <p>
    I work in the {{ profile.clinical_context }} and serve as core faculty in the
    University of Utah Pulmonary and Critical Care Fellowship. I trained in computer
    science, medicine, medical education, and clinical investigation. My career
    purpose centers on respiratory failure, diagnostic evidence, clinical prediction,
    and reproducible research informatics.
  </p>
  <p>{{ profile.focus_intro }}</p>
  <ul class="focus-list">
    {% for area in profile.focus_areas %}
      <li>{{ area }}</li>
    {% endfor %}
  </ul>
</section>

<section class="home-section">
  <h2>Research Approach</h2>
  <p>{{ profile.approach_intro }}</p>
  <ul class="approach-list">
    {% for area in profile.approach_areas %}
      <li>
        <h3>{{ area.title }}</h3>
        <p>{{ area.summary }}</p>
      </li>
    {% endfor %}
  </ul>
</section>

<section class="home-section">
  <h2>Selected Current Work</h2>
  <div class="content-card-list">
    <article class="content-card">
      <h3>Hypercapnic Respiratory Failure</h3>
      <p>
        Measuring disease burden, care variation, and post-discharge needs after
        hospitalization with hypercapnic respiratory failure.
      </p>
      <p><a href="{{ "/publications/" | prepend: base_path }}">Selected publications</a></p>
    </article>
    <article class="content-card">
      <h3>Diagnostic Evidence and Prediction</h3>
      <p>
        Developing EHR-derived phenotypes and prediction models that make
        respiratory measurement more interpretable and reproducible.
      </p>
      <p><a href="{{ "/cv/" | prepend: base_path }}">Academic CV</a></p>
    </article>
    <article class="content-card">
      <h3>Reproducible Research Workflows</h3>
      <p>
        Maintaining open statistical code, teaching materials, and research
        artifacts that support transparent clinical investigation.
      </p>
      <p><a href="{{ "/materials/" | prepend: base_path }}">Materials index</a></p>
    </article>
    <article class="content-card">
      <h3>National Abstracts and Presentations</h3>
      <p>
        Sharing recent work on respiratory failure, clinical prediction,
        pulmonary vascular imaging, and medical education.
      </p>
      <p><a href="{{ "/talks/" | prepend: base_path }}">Selected abstracts and presentations</a></p>
    </article>
    <article class="content-card">
      <h3>Teaching and Curriculum</h3>
      <p>
        Developing teaching around evidence-based reasoning, pulmonary and
        critical care medicine, and clinical research methods.
      </p>
      <p><a href="{{ "/teaching/" | prepend: base_path }}">Selected teaching activities</a></p>
    </article>
  </div>
</section>

<section class="home-section home-section--split">
  <div>
    <h2>Materials</h2>
    <p>
      Public code, teaching materials, reproducible analyses, and project artifacts
      are available in the materials index.
    </p>
  </div>
  <p><a class="btn btn--primary" href="{{ "/materials/" | prepend: base_path }}">Browse GitHub-accessible materials</a></p>
</section>

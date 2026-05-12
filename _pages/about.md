---
layout: splash
permalink: /
title: "Brian W Locke, MD MSCI"
excerpt: "Pulmonary and critical care physician and clinical investigator."
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
    science, medicine, medical education, and clinical investigation.
  </p>
  <p>{{ profile.focus_intro }}</p>
  <ul class="focus-list">
    {% for area in profile.focus_areas %}
      <li>{{ area }}</li>
    {% endfor %}
  </ul>
</section>

<section class="home-section home-section--split">
  <div>
    <h2>Materials</h2>
    <p>
      Public code, teaching materials, reproducible analyses, and project artifacts
      are collected from GitHub in one automatically refreshed index.
    </p>
  </div>
  <p><a class="btn btn--primary" href="{{ "/materials/" | prepend: base_path }}">Browse GitHub-accessible materials</a></p>
</section>

---
layout: splash
title: "Curriculum Vitae"
permalink: /cv/
author_profile: false
redirect_from:
  - /resume
---

{% include base_path %}
{% assign profile = site.data.profile %}
{% assign cv = site.data.cv %}

<section class="cv-page">
  <header class="section-header">
    <h1>Curriculum Vitae</h1>
    <p>
      A compact public CV. Publication and repository lists are maintained through
      external profiles rather than duplicated here.
    </p>
    <ul class="profile-links profile-links--compact" aria-label="External academic profiles">
      {% for link in profile.links %}
        {% unless link.label == "Email" %}
          <li>
            <a href="{{ link.url }}">
              <i class="{{ link.icon }}" aria-hidden="true"></i>
              <span>{{ link.label }}</span>
            </a>
          </li>
        {% endunless %}
      {% endfor %}
    </ul>
  </header>

  <section class="cv-section">
    <h2>Current Positions</h2>
    {% for item in cv.positions %}
      <article class="cv-entry">
        <p class="cv-entry__dates">{{ item.dates }}</p>
        <div>
          <h3>{{ item.title }}</h3>
          <p>{{ item.organization }}</p>
        </div>
      </article>
    {% endfor %}
  </section>

  <section class="cv-section">
    <h2>Education</h2>
    {% for item in cv.education %}
      <article class="cv-entry">
        <p class="cv-entry__dates">{{ item.year }}</p>
        <div>
          <h3>{{ item.degree }}</h3>
          <p>{{ item.institution }}</p>
          {% if item.note %}
            <p class="cv-entry__note">
              {% if item.url %}<a href="{{ item.url }}">{{ item.note }}</a>{% else %}{{ item.note }}{% endif %}
            </p>
          {% endif %}
        </div>
      </article>
    {% endfor %}
  </section>

  <section class="cv-section">
    <h2>Training</h2>
    {% for item in cv.training %}
      <article class="cv-entry">
        <p class="cv-entry__dates">{{ item.dates }}</p>
        <div>
          <h3>{{ item.role }}</h3>
          <p>{{ item.institution }}</p>
        </div>
      </article>
    {% endfor %}
  </section>

  <section class="cv-section">
    <h2>Selected Research Support</h2>
    {% for item in cv.selected_support %}
      <article class="cv-entry">
        <p class="cv-entry__dates">{{ item.dates }}</p>
        <div>
          <h3>{% if item.url %}<a href="{{ item.url }}">{{ item.title }}</a>{% else %}{{ item.title }}{% endif %}</h3>
          <p>{{ item.sponsor }}{% if item.role %}; {{ item.role }}{% endif %}</p>
        </div>
      </article>
    {% endfor %}
  </section>

  <section class="cv-section">
    <h2>Professional Context</h2>
    <ul class="cv-list">
      {% for item in cv.professional_context %}
        <li>{{ item }}</li>
      {% endfor %}
    </ul>
  </section>
</section>

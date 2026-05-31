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
      A compact public academic CV. Publication, abstract, and repository details
      are linked to public profiles where they can stay current.
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
    <h2>Education and Training</h2>
    {% for item in cv.education %}
      <article class="cv-entry">
        <p class="cv-entry__dates">{{ item.dates }}</p>
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
    <h2>Positions and Employment</h2>
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
    <h2>Certifications</h2>
    <ul class="cv-list">
      {% for item in cv.certifications %}
        <li>{{ item }}</li>
      {% endfor %}
    </ul>
  </section>

  <section class="cv-section">
    <h2>Research Support</h2>
    {% for item in cv.research_support %}
      <article class="cv-entry">
        <p class="cv-entry__dates">{{ item.dates }}</p>
        <div>
          <h3>{{ item.title }}</h3>
          <p>{{ item.sponsor }}{% if item.award %}, {{ item.award }}{% endif %}; {{ item.role }}</p>
          <p class="cv-entry__note">{{ item.summary }}</p>
        </div>
      </article>
    {% endfor %}
  </section>

  <section class="cv-section">
    <h2>Academic Publications and Scholarly Products</h2>
    <p>
      Full publication details are maintained through
      <a href="https://scholar.google.com/citations?hl=en&amp;user=O1nydc8AAAAJ">Google Scholar</a>
      and <a href="https://orcid.org/0000-0002-3588-5238">ORCID</a>. Selected
      publications are listed below so that the public CV remains useful if
      external services fail to load.
    </p>
    <div class="publication-list publication-list--compact">
      {% for publication in site.data.selected_publications.publications %}
        {% if publication.selected_cv %}
          <article class="publication-item">
            <h3>{{ publication.title }}</h3>
            <p class="publication-item__meta">
              {{ publication.authors }}. <em>{{ publication.venue }}</em>. {{ publication.year }}.
              {% if publication.doi %}<a href="{{ publication.url }}">doi:{{ publication.doi }}</a>{% endif %}
            </p>
          </article>
        {% endif %}
      {% endfor %}
    </div>
    <div
      class="orcid-works"
      data-orcid="0000-0002-3588-5238"
      data-limit="12"
      data-default-filter="all"
      data-controls="true"
      data-scholar-url="https://scholar.google.com/citations?hl=en&amp;user=O1nydc8AAAAJ"
      data-orcid-url="https://orcid.org/0000-0002-3588-5238"
    >
      <p class="orcid-works__status" role="status">Loading ORCID works...</p>
      <div class="orcid-works__controls" aria-label="Filter scholarly products"></div>
      <div class="orcid-works__list"></div>
    </div>
  </section>

  <section class="cv-section">
    <h2>National Abstracts and Presentations</h2>
    <p>
      Selected recent national abstracts are listed below. Additional conference
      outputs are maintained through ORCID and Google Scholar.
    </p>
    <p><a href="{{ "/talks/" | prepend: base_path }}">View selected national abstracts and presentations</a>.</p>
    <div class="content-card-list content-card-list--compact">
      {% for talk in site.data.selected_talks.talks limit:6 %}
        <article class="content-card">
          <p class="content-card__eyebrow">{{ talk.year }} / {{ talk.venue }}</p>
          <h3>{{ talk.title }}</h3>
          <p class="content-card__meta">{{ talk.type }}{% if talk.location %} / {{ talk.location }}{% endif %}</p>
        </article>
      {% endfor %}
    </div>
    <div
      class="orcid-works"
      data-orcid="0000-0002-3588-5238"
      data-limit="8"
      data-default-filter="conference"
      data-controls="false"
      data-scholar-url="https://scholar.google.com/citations?hl=en&amp;user=O1nydc8AAAAJ"
      data-orcid-url="https://orcid.org/0000-0002-3588-5238"
    >
      <p class="orcid-works__status" role="status">Loading ORCID conference outputs...</p>
      <div class="orcid-works__list"></div>
    </div>
  </section>

  <section class="cv-section">
    <h2>Teaching Experience and Committees</h2>
    <p><a href="{{ "/teaching/" | prepend: base_path }}">View selected teaching and curriculum activities</a>.</p>
    <h3>Lectures and Seminars</h3>
    <ul class="cv-list">
      {% for item in cv.teaching.lectures %}
        <li>{{ item }}</li>
      {% endfor %}
    </ul>
    <h3>Curricular Design</h3>
    <ul class="cv-list">
      {% for item in cv.teaching.curricular_design %}
        <li>{{ item }}</li>
      {% endfor %}
    </ul>
    <h3>Research Group, Committee, and Administrative Service</h3>
    <ul class="cv-list">
      {% for item in cv.committees %}
        <li>{{ item }}</li>
      {% endfor %}
    </ul>
  </section>

  <section class="cv-section">
    <h2>Appointments, Honors, and Awards</h2>
    {% for item in cv.honors %}
      <article class="cv-entry">
        <p class="cv-entry__dates">{{ item.dates }}</p>
        <div>
          <h3>{{ item.title }}</h3>
        </div>
      </article>
    {% endfor %}
  </section>

  <section class="cv-section">
    <h2>Peer Review and Professional Service</h2>
    <ul class="cv-list">
      {% for item in cv.peer_review %}
        <li>{{ item }}</li>
      {% endfor %}
    </ul>
  </section>

  <section class="cv-section">
    <h2>Professional Context / Disclosures</h2>
    <ul class="cv-list">
      {% for item in cv.professional_context %}
        <li>{{ item }}</li>
      {% endfor %}
    </ul>
  </section>
</section>

<script src="{{ "/assets/js/orcid-works.js" | prepend: base_path }}" defer></script>

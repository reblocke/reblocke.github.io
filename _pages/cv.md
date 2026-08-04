---
permalink: /cv/
title: "Curriculum Vitae"
description: "A compact public academic CV for Brian W. Locke."
---
{% assign person = site.data.person %}
{% assign cv = site.data.cv %}
{% assign work = site.data.generated.work %}
<article class="site-container page page--cv">
  <header class="page-header">
    <h1>Curriculum Vitae</h1>
    <p class="cv-name">{{ person.name }}</p>
    {% include affiliations.html %}
    <p class="prose">A compact public academic CV. Complete publication records are available through <a href="{{ person.profiles.google_scholar }}">Google Scholar</a> and <a href="{{ person.profiles.orcid }}">ORCID</a>.</p>
    <nav class="anchor-index" aria-label="CV sections">
      <a href="#appointments">Appointments</a><a href="#training">Training</a><a href="#support">Support</a><a href="#publications">Publications</a><a href="#presentations">Presentations</a><a href="#teaching-and-curriculum">Teaching</a><a href="#service">Service</a>
    </nav>
  </header>

  <section class="cv-section" id="appointments"><h2>Appointments and employment</h2>{% for item in cv.positions %}{% include cv-entry.html item=item %}{% endfor %}</section>
  <section class="cv-section" id="training"><h2>Education and training</h2>{% for item in cv.education %}{% include cv-entry.html item=item %}{% endfor %}{% for item in cv.training %}{% include cv-entry.html item=item %}{% endfor %}</section>
  <section class="cv-section" id="certifications"><h2>Certifications</h2><ul class="plain-list">{% for item in cv.certifications %}<li>{{ item.title }}</li>{% endfor %}</ul></section>
  <section class="cv-section" id="support"><h2>Research support</h2><h3>Current</h3>{% for item in cv.research_support.current %}{% include cv-entry.html item=item %}{% endfor %}<h3>Completed</h3>{% for item in cv.research_support.completed %}{% include cv-entry.html item=item %}{% endfor %}</section>
  <section class="cv-section" id="publications"><h2>Selected scholarly outputs</h2><ol class="citation-list">{% for item in work.items %}{% if item.selected.cv and item.type != "abstract" %}<li><span class="citation-title">{{ item.title }}</span>. {{ item.authors }}. <em>{{ item.venue }}</em>. {{ item.year }}. {% if item.doi %}<a href="https://doi.org/{{ item.doi }}">doi:{{ item.doi }}</a>{% endif %}</li>{% endif %}{% endfor %}</ol></section>
  <section class="cv-section" id="presentations"><h2>Selected presentations</h2>{% for item in work.items %}{% if item.selected.cv and item.type == "abstract" %}<article class="cv-entry"><p class="cv-entry__dates">{{ item.year }}</p><div><h3>{{ item.title }}</h3><p>{{ item.venue }}{% if item.location %}, {{ item.location }}{% endif %}</p></div></article>{% endif %}{% endfor %}</section>
  <section class="cv-section" id="teaching-and-curriculum"><h2>Teaching and curriculum</h2>{% for item in cv.teaching %}<article class="cv-entry"><p class="cv-entry__dates">{{ item.dates }}</p><div><h3>{{ item.title }}</h3><p>{{ item.kind }} · {{ item.organization }}</p></div></article>{% endfor %}</section>
  <section class="cv-section" id="service"><h2>Service, honors, and peer review</h2><h3>Service</h3><ul class="plain-list">{% for item in cv.service %}<li>{{ item.title }}</li>{% endfor %}</ul><h3>Honors</h3>{% for item in cv.honors %}{% include cv-entry.html item=item %}{% endfor %}<h3>Peer review</h3><ul class="plain-list columns-list">{% for item in cv.peer_review %}<li>{{ item }}</li>{% endfor %}</ul></section>
  <section class="cv-section" id="disclosure"><h2>Professional disclosure</h2><p>{{ person.disclosure }}</p></section>
</article>

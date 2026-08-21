---
permalink: /topics/hypercapnic-respiratory-failure/
title: "Hypercapnic Respiratory Failure and Respiratory Measurement"
seo_title: "Hypercapnic Respiratory Failure Research | Brian W. Locke"
description: "Research by Brian W. Locke on recognizing, measuring, and managing hypercapnic respiratory failure using clinical data, physiologic measurement, and reproducible methods."
schema_type: "CollectionPage"
---
{% assign work = site.data.generated.work %}
{% assign topic = work.topics | where: "id", "hypercapnic-respiratory-failure" | first %}
<article class="site-container page page--work">
  <header class="page-header prose">
    <h1>Hypercapnic Respiratory Failure and Respiratory Measurement</h1>
    <p>{{ topic.description | default: page.description }}</p>
    <p>This collection brings together the related papers, abstracts, code, and supporting resources in their canonical publication order. Browse <a href="/publications/">all publications</a> or return to <a href="/work/">selected work</a>.</p>
  </header>

  <section class="work-section" aria-labelledby="topic-publications-heading">
    <h2 id="topic-publications-heading">Publications and commentaries</h2>
    {% for item in work.items %}
      {% if topic.item_ids contains item.id and item.type != "abstract" %}{% include work-list-item.html item=item %}{% endif %}
    {% endfor %}
  </section>

  <section class="work-section" aria-labelledby="topic-abstracts-heading">
    <h2 id="topic-abstracts-heading">Conference abstracts</h2>
    {% for item in work.items %}
      {% if topic.item_ids contains item.id and item.type == "abstract" %}{% include work-list-item.html item=item %}{% endif %}
    {% endfor %}
  </section>
</article>

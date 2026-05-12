(function () {
  var widgets = Array.prototype.slice.call(document.querySelectorAll(".orcid-works"));
  var worksCache = {};

  if (!widgets.length) {
    return;
  }

  function textValue(value) {
    return value && value.value ? value.value : "";
  }

  function normalizeType(type) {
    return (type || "other").replace(/-/g, " ");
  }

  function getYear(summary) {
    var publicationDate = summary["publication-date"];
    return textValue(publicationDate && publicationDate.year);
  }

  function getLink(summary) {
    var externalIds = summary["external-ids"];
    var ids = externalIds && externalIds["external-id"];
    var doiId;

    if (summary.url && summary.url.value) {
      return summary.url.value;
    }

    if (ids && ids.length) {
      doiId = ids.filter(function (item) {
        return item["external-id-type"] === "doi" && item["external-id-url"];
      })[0];
      if (doiId) {
        return doiId["external-id-url"].value;
      }
    }

    return "https://orcid.org" + summary.path;
  }

  function typeGroup(summary) {
    var type = summary.type || "";
    if (type === "journal-article" || type === "preprint") {
      return "publication";
    }
    if (type.indexOf("conference") === 0) {
      return "conference";
    }
    return "other";
  }

  function normalizeWorks(data) {
    return (data.group || [])
      .map(function (group) {
        return (group["work-summary"] || [])[0];
      })
      .filter(function (summary) {
        return summary && summary.title && summary.title.title;
      })
      .map(function (summary) {
        return {
          title: textValue(summary.title.title),
          type: summary.type || "other",
          group: typeGroup(summary),
          year: getYear(summary),
          venue: textValue(summary["journal-title"]),
          href: getLink(summary),
          displayIndex: summary["display-index"] || "0"
        };
      })
      .sort(function (a, b) {
        var yearDiff = (parseInt(b.year, 10) || 0) - (parseInt(a.year, 10) || 0);
        if (yearDiff) {
          return yearDiff;
        }
        return (parseInt(b.displayIndex, 10) || 0) - (parseInt(a.displayIndex, 10) || 0);
      });
  }

  function fetchWorks(orcid) {
    if (!worksCache[orcid]) {
      worksCache[orcid] = fetch("https://pub.orcid.org/v3.0/" + encodeURIComponent(orcid) + "/works", {
        headers: {
          Accept: "application/json"
        }
      })
        .then(function (response) {
          if (!response.ok) {
            throw new Error("ORCID returned " + response.status);
          }
          return response.json();
        })
        .then(normalizeWorks);
    }
    return worksCache[orcid];
  }

  function matchesFilter(work, filter) {
    if (filter === "all") {
      return true;
    }
    return work.group === filter;
  }

  function fallback(widget, message) {
    var status = widget.querySelector(".orcid-works__status");
    var list = widget.querySelector(".orcid-works__list");
    var scholarUrl = widget.getAttribute("data-scholar-url");
    var orcidUrl = widget.getAttribute("data-orcid-url");

    if (status) {
      status.textContent = "ORCID works could not be loaded.";
      status.classList.add("orcid-works__status--error");
    }
    if (list) {
      list.innerHTML = [
        '<p class="notice--warning">',
        message,
        ' View current outputs at <a href="',
        orcidUrl,
        '">ORCID</a> or <a href="',
        scholarUrl,
        '">Google Scholar</a>.',
        "</p>"
      ].join("");
    }
  }

  function render(widget, works, filter) {
    var list = widget.querySelector(".orcid-works__list");
    var status = widget.querySelector(".orcid-works__status");
    var limit = parseInt(widget.getAttribute("data-limit"), 10) || 12;
    var visibleWorks = works.filter(function (work) {
      return matchesFilter(work, filter);
    }).slice(0, limit);

    if (!list) {
      return;
    }

    list.innerHTML = "";

    if (!visibleWorks.length) {
      list.innerHTML = '<p class="orcid-works__empty">No ORCID works match this filter.</p>';
      if (status) {
        status.textContent = "No matching ORCID works found.";
      }
      return;
    }

    visibleWorks.forEach(function (work) {
      var item = document.createElement("article");
      var title = document.createElement("h3");
      var link = document.createElement("a");
      var meta = document.createElement("p");
      var metaParts = [];

      item.className = "orcid-work";
      link.href = work.href;
      link.textContent = work.title;
      title.appendChild(link);

      if (work.year) {
        metaParts.push(work.year);
      }
      if (work.venue) {
        metaParts.push(work.venue);
      }
      metaParts.push(normalizeType(work.type));
      meta.className = "orcid-work__meta";
      meta.textContent = metaParts.join(" | ");

      item.appendChild(title);
      item.appendChild(meta);
      list.appendChild(item);
    });

    if (status) {
      status.textContent = "Showing " + visibleWorks.length + " of " + works.length + " public ORCID works.";
      status.classList.remove("orcid-works__status--error");
    }
  }

  function buildControls(widget, works) {
    var controls = widget.querySelector(".orcid-works__controls");
    var currentFilter = widget.getAttribute("data-default-filter") || "all";
    var showControls = widget.getAttribute("data-controls") !== "false";
    var filters = [
      ["all", "All"],
      ["publication", "Publications"],
      ["conference", "Conference Outputs"],
      ["other", "Other Products"]
    ];

    if (!controls || !showControls) {
      render(widget, works, currentFilter);
      return;
    }

    controls.innerHTML = "";
    filters.forEach(function (filter) {
      var button = document.createElement("button");
      button.type = "button";
      button.className = "orcid-works__filter";
      button.textContent = filter[1];
      button.setAttribute("aria-pressed", filter[0] === currentFilter ? "true" : "false");
      button.addEventListener("click", function () {
        currentFilter = filter[0];
        Array.prototype.slice.call(controls.querySelectorAll("button")).forEach(function (item) {
          item.setAttribute("aria-pressed", item === button ? "true" : "false");
        });
        render(widget, works, currentFilter);
      });
      controls.appendChild(button);
    });
    render(widget, works, currentFilter);
  }

  widgets.forEach(function (widget) {
    var orcid = widget.getAttribute("data-orcid");
    if (!orcid) {
      return;
    }
    fetchWorks(orcid)
      .then(function (works) {
        buildControls(widget, works);
      })
      .catch(function () {
        fallback(widget, "The live ORCID works list is unavailable right now.");
      });
  });
})();

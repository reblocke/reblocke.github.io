(function () {
  var container = document.getElementById("github-materials");
  if (!container) {
    return;
  }

  var owner = container.getAttribute("data-owner") || "reblocke";
  var profileUrl = container.getAttribute("data-profile-url") || "https://github.com/" + owner;
  var status = document.getElementById("materials-status");
  var searchInput = document.getElementById("materials-search");
  var showForksInput = document.getElementById("materials-show-forks");
  var repos = [];

  function setStatus(message, isError) {
    if (!status) {
      return;
    }
    status.textContent = message;
    status.classList.toggle("materials-status--error", !!isError);
  }

  function formatDate(value) {
    if (!value) {
      return "";
    }
    var date = new Date(value);
    if (isNaN(date.getTime())) {
      return "";
    }
    return date.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric"
    });
  }

  function textMatches(repo, query) {
    if (!query) {
      return true;
    }
    var haystack = [
      repo.name,
      repo.description,
      repo.language
    ].join(" ").toLowerCase();
    return haystack.indexOf(query) !== -1;
  }

  function render() {
    var query = searchInput ? searchInput.value.trim().toLowerCase() : "";
    var includeForks = showForksInput ? showForksInput.checked : false;
    var visibleRepos = repos.filter(function (repo) {
      return (includeForks || !repo.fork) && textMatches(repo, query);
    });

    container.innerHTML = "";

    if (!visibleRepos.length) {
      container.innerHTML = '<p class="materials-empty">No repositories match the current filters.</p>';
      setStatus("No matching materials found.", false);
      return;
    }

    visibleRepos.forEach(function (repo) {
      var item = document.createElement("article");
      item.className = "materials-item";

      var title = document.createElement("h2");
      var link = document.createElement("a");
      link.href = repo.html_url;
      link.textContent = repo.name;
      title.appendChild(link);

      var description = document.createElement("p");
      description.className = "materials-item__description";
      description.textContent = repo.description || "Public GitHub repository.";

      var meta = document.createElement("p");
      meta.className = "materials-item__meta";
      var parts = [];
      if (repo.language) {
        parts.push(repo.language);
      }
      if (repo.fork) {
        parts.push("Fork");
      }
      if (repo.updated_at) {
        parts.push("Updated " + formatDate(repo.updated_at));
      }
      meta.textContent = parts.join(" | ");

      item.appendChild(title);
      item.appendChild(description);
      item.appendChild(meta);
      container.appendChild(item);
    });

    setStatus(
      "Showing " + visibleRepos.length + " of " + repos.length + " public repositories.",
      false
    );
  }

  function fallback(message) {
    container.innerHTML = [
      '<p class="notice--warning">',
      message,
      ' Browse public repositories directly at <a href="',
      profileUrl,
      '">github.com/',
      owner,
      "</a>.",
      "</p>"
    ].join("");
    setStatus("GitHub materials could not be loaded.", true);
  }

  function fetchRepoPage(page, collectedRepos) {
    return fetch(
      "https://api.github.com/users/" + encodeURIComponent(owner) +
      "/repos?per_page=100&sort=updated&type=owner&page=" + page
    )
      .then(function (response) {
        if (!response.ok) {
          throw new Error("GitHub API returned " + response.status);
        }
        return response.json();
      })
      .then(function (data) {
        if (!Array.isArray(data)) {
          throw new Error("GitHub API returned an unexpected response");
        }
        var nextRepos = collectedRepos.concat(data);
        if (data.length === 100) {
          return fetchRepoPage(page + 1, nextRepos);
        }
        return nextRepos;
      });
  }

  fetchRepoPage(1, [])
    .then(function (data) {
      repos = data
        .filter(function (repo) {
          return !repo.archived;
        })
        .sort(function (a, b) {
          return new Date(b.updated_at) - new Date(a.updated_at);
        });
      render();
    })
    .catch(function () {
      fallback("The live GitHub index is unavailable right now.");
    });

  if (searchInput) {
    searchInput.addEventListener("input", render);
  }
  if (showForksInput) {
    showForksInput.addEventListener("change", render);
  }
})();

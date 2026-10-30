// @ts-check
/**
 * Frontend controller for Personal News Aggregator, Weather & Myanmar Market Hub.
 * Zero-build Vanilla JS with strict state handling and keyboard navigation.
 */

/**
 * @typedef {Object} Article
 * @property {string} id
 * @property {string} category
 * @property {string} source
 * @property {string} title
 * @property {string} url
 * @property {string} brief
 * @property {string} published_at
 * @property {number} published_ts
 * @property {boolean} dismissed
 * @property {boolean} [saved]
 */

/**
 * @typedef {Object} ArticlesPayload
 * @property {Article[]} articles
 * @property {Record<string, number>} counts
 * @property {number} total_unread
 */

const CATEGORY_ORDER = [
  "Myanmar",
  "World Crises & Geopolitics",
  "Military, Weapons & Defense Tech",
  "Technology & Computer Science",
  "AI",
  "Business & Economy",
  "Science",
  "Health & Wellness",
  "Environment",
  "Opinion, Editorial & Feature Stories",
];

/** @type {Record<string, string>} */
const CATEGORY_DOT_COLORS = {
  "Myanmar": "bg-rose-500",
  "World Crises & Geopolitics": "bg-amber-400",
  "Military, Weapons & Defense Tech": "bg-orange-500",
  "Technology & Computer Science": "bg-sky-400",
  "AI": "bg-violet-400",
  "Business & Economy": "bg-emerald-400",
  "Science": "bg-cyan-400",
  "Health & Wellness": "bg-teal-400",
  "Environment": "bg-lime-400",
  "Opinion, Editorial & Feature Stories": "bg-fuchsia-400",
};

const state = {
  activeCategory: "All",
  /** @type {Article[]} */
  articles: [],
  /** @type {Record<string, number>} */
  counts: {},
  totalUnread: 0,
  focusedArticleId: /** @type {string | null} */ (null),
  isRefreshing: false,
};

/**
 * Escape text safely before inserting into HTML templates.
 * @param {string} str
 * @returns {string}
 */
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

/**
 * Format publication timestamp into a concise human-readable time string.
 * @param {number} publishedTs
 * @param {string} isoFallback
 * @returns {string}
 */
function formatPubTime(publishedTs, isoFallback) {
  const nowSec = Math.floor(Date.now() / 1000);
  const diffSec = Math.max(0, nowSec - publishedTs);

  if (diffSec < 60) return "Just now";
  const mins = Math.floor(diffSec / 60);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;

  try {
    const dt = new Date(publishedTs * 1000);
    return dt.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  } catch {
    return isoFallback.slice(0, 10);
  }
}

/**
 * Format integer with commas.
 * @param {number} num
 * @returns {string}
 */
function formatNumber(num) {
  return Number(num).toLocaleString("en-US");
}

let statusPillTimer = null;
/**
 * Show a temporary status message in the top header pill.
 * @param {string} message
 */
function showStatusPill(message) {
  const pill = document.getElementById("status-pill");
  if (!pill) return;
  pill.textContent = message;
  pill.classList.remove("hidden");
  if (statusPillTimer) clearTimeout(statusPillTimer);
  statusPillTimer = setTimeout(() => {
    pill.classList.add("hidden");
  }, 3500);
}

/**
 * Fetch and render Yangon weather from /api/weather.
 */
async function loadWeather() {
  try {
    const res = await fetch("/api/weather");
    if (!res.ok) return;
    const data = await res.json();

    const locEl = document.getElementById("weather-location");
    const condEl = document.getElementById("weather-condition");
    const tempEl = document.getElementById("weather-temp");
    const hiloEl = document.getElementById("weather-hilo");
    const rainEl = document.getElementById("weather-rain");

    if (locEl) {
      locEl.innerHTML = `<span class="h-1.5 w-1.5 rounded-full bg-sky-400"></span>${escapeHtml(data.location)}`;
    }
    if (condEl) {
      condEl.textContent = data.condition_label;
    }
    if (tempEl) {
      tempEl.textContent = `${data.temperature_c}°C`;
    }
    if (hiloEl) {
      hiloEl.textContent = `H: ${data.temp_max_c}° · L: ${data.temp_min_c}°`;
    }
    if (rainEl) {
      rainEl.textContent = `Rain Prob: ${data.rain_prob_pct}%`;
    }
  } catch {
    // Silent fallback kept in DOM
  }
}

/**
 * Render MarketResponse payload into the top-bar FX & Gold widgets.
 * @param {any} data
 */
function renderMarketData(data) {
  const fxUpdated = document.getElementById("fx-updated");
  if (fxUpdated) {
    if (data.is_calibrated) {
      fxUpdated.textContent = `Calibrated · ${data.updated_at}`;
    } else if (data.is_fallback) {
      fxUpdated.textContent = `Offline Ref · ${data.updated_at}`;
    } else {
      fxUpdated.textContent = `Live Street · ${data.updated_at}`;
    }
  }

  const fxGrid = document.getElementById("fx-grid");
  if (fxGrid && Array.isArray(data.currencies)) {
    fxGrid.innerHTML = data.currencies
      .map(
        (c) => `
        <div class="rounded bg-white dark:bg-[#20242d] px-2.5 py-1.5 border border-slate-200 dark:border-[#2e3442] shadow-sm">
          <div class="flex items-center justify-between font-mono text-[10px] text-slate-500 dark:text-slate-400">
            <span class="font-bold text-slate-900 dark:text-slate-200">${escapeHtml(c.code)}/MMK</span>
            <span class="text-slate-400 dark:text-slate-500" title="Buy / Sell Street Range">${formatNumber(c.buy_mmk || c.market_est_mmk)}–${formatNumber(c.sell_mmk || c.market_est_mmk)}</span>
          </div>
          <div class="font-mono text-xs font-bold text-emerald-700 dark:text-emerald-400 mt-0.5">
            ${formatNumber(c.market_est_mmk)} <span class="text-[9px] font-normal text-slate-400">Ks</span>
          </div>
        </div>
      `
      )
      .join("");
  }

  const goldBadge = document.getElementById("gold-spot-badge");
  if (goldBadge && data.gold) {
    goldBadge.textContent = `Spot $${formatNumber(data.gold.world_spot_usd_oz)}/oz`;
  }

  const goldContent = document.getElementById("gold-content");
  if (goldContent && data.gold) {
    goldContent.innerHTML = `
      <div class="rounded bg-white dark:bg-[#20242d] px-2.5 py-1.5 border border-slate-200 dark:border-[#2e3442] shadow-sm">
        <div class="font-sans text-[10px] font-bold uppercase tracking-wider text-amber-800 dark:text-amber-300">16 Pae (အခေါက်ရွှေ)</div>
        <div class="font-mono text-xs font-bold text-amber-700 dark:text-amber-400 mt-0.5">
          ${formatNumber(data.gold.market_16pae_mmk_tical)} <span class="text-[9px] font-normal text-slate-400">Ks</span>
        </div>
      </div>
      <div class="rounded bg-white dark:bg-[#20242d] px-2.5 py-1.5 border border-slate-200 dark:border-[#2e3442] shadow-sm">
        <div class="flex items-center justify-between font-sans text-[10px] font-bold uppercase tracking-wider text-amber-800 dark:text-amber-300">
          <span>15 Pae</span>
          <span class="text-slate-400 font-normal" title="YGEA Official Reference">YGEA ${formatNumber(Math.round(data.gold.ygea_ref_mmk_tical / 100000) / 10)}M</span>
        </div>
        <div class="font-mono text-xs font-bold text-amber-700 dark:text-amber-400 mt-0.5">
          ${formatNumber(data.gold.market_15pae_mmk_tical)} <span class="text-[9px] font-normal text-slate-400">Ks</span>
        </div>
      </div>
    `;
  }
}

/**
 * Fetch and render Myanmar FX & Gold reference rates from /api/market.
 */
async function loadMarketRates() {
  try {
    const res = await fetch("/api/market");
    if (!res.ok) return;
    const data = await res.json();
    renderMarketData(data);
  } catch {
    // Silent fallback
  }
}

/**
 * Render category filter tabs with unread count badges.
 */
function renderCategoryTabs() {
  const container = document.getElementById("category-tabs");
  if (!container) return;

  const tabs = [
    { name: "All", label: "All", count: state.totalUnread },
    { name: "Saved", label: "★ Saved", count: state.counts["Saved"] || 0 },
    ...CATEGORY_ORDER.map((cat) => ({
      name: cat,
      label: cat,
      count: state.counts[cat] || 0,
    })),
  ];

  container.innerHTML = tabs
    .map((tab) => {
      const isActive = state.activeCategory === tab.name;
      let btnClasses = "bg-white dark:bg-[#1a1d24] text-slate-700 dark:text-slate-300 border-slate-200 dark:border-[#2a2f3a] hover:border-slate-400 dark:hover:border-slate-500 hover:text-slate-950 dark:hover:text-white shadow-sm";
      let badgeClasses = "text-slate-400 dark:text-slate-500 font-mono";

      if (isActive) {
        if (tab.name === "Saved") {
          btnClasses = "bg-amber-600 dark:bg-amber-400 text-white dark:text-slate-950 border-amber-600 dark:border-amber-400 font-bold shadow-sm";
          badgeClasses = "text-white/80 dark:text-black/80 font-mono font-bold";
        } else {
          btnClasses = "bg-slate-900 dark:bg-white text-white dark:text-slate-950 border-slate-900 dark:border-white font-bold shadow-sm";
          badgeClasses = "text-white/80 dark:text-black/80 font-mono font-bold";
        }
      } else if (tab.name === "Saved" && tab.count > 0) {
        btnClasses = "bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border-amber-300 dark:border-amber-800/60 hover:border-amber-400";
        badgeClasses = "text-amber-700 dark:text-amber-400 font-mono font-semibold";
      }

      return `
        <button
          type="button"
          data-category="${escapeHtml(tab.name)}"
          class="category-tab shrink-0 inline-flex items-center gap-1.5 rounded border px-3 py-1.5 font-sans text-xs transition ${btnClasses}"
        >
          <span>${escapeHtml(tab.label)}</span>
          <span class="text-[11px] ${badgeClasses}">
            (${tab.count})
          </span>
        </button>
      `;
    })
    .join("");

  container.querySelectorAll(".category-tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      const selected = btn.getAttribute("data-category") || "All";
      state.activeCategory = selected;
      updateDismissCategoryButtonLabel();
      renderCategoryTabs();
      loadArticles();
    });
  });
}

/**
 * Update the "Dismiss All Visible" button label based on active category.
 */
function updateDismissCategoryButtonLabel() {
  const btn = document.getElementById("dismiss-category-btn");
  const labelEl = document.getElementById("dismiss-category-label");
  if (!btn || !labelEl) return;

  if (state.activeCategory === "Saved") {
    btn.classList.add("hidden");
  } else {
    btn.classList.remove("hidden");
    if (state.activeCategory === "All") {
      labelEl.textContent = "Dismiss All Visible";
    } else {
      labelEl.textContent = `Dismiss All in ${state.activeCategory}`;
    }
  }
}

/**
 * Render the minimalist article cards.
 * Strictly displays ONLY:
 * 1. Category Badge
 * 2. Source Name
 * 3. Article Title
 * 4. Publication Time
 * 5. 2-3 sentence plain-text Brief (max 280 chars)
 * 6. "Read Article" link (new tab)
 * 7. "Skip / Dismiss" button
 */
function renderArticles() {
  const grid = document.getElementById("articles-grid");
  const emptyState = document.getElementById("empty-state");
  if (!grid || !emptyState) return;

  if (state.articles.length === 0) {
    grid.innerHTML = "";
    emptyState.classList.remove("hidden");
    state.focusedArticleId = null;
    return;
  }

  emptyState.classList.add("hidden");

  if (
    !state.focusedArticleId ||
    !state.articles.some((a) => a.id === state.focusedArticleId)
  ) {
    state.focusedArticleId = state.articles[0].id;
  }

  grid.innerHTML = state.articles
    .map((article) => {
      const dotColor =
        CATEGORY_DOT_COLORS[article.category] || "bg-neutral-400";
      const pubTime = formatPubTime(article.published_ts, article.published_at);
      const isFocused = state.focusedArticleId === article.id;

      return `
        <article
          id="card-${escapeHtml(article.id)}"
          data-article-id="${escapeHtml(article.id)}"
          class="card-transition group relative flex flex-col justify-between rounded-lg border border-slate-200/90 dark:border-[#2a2f3a] bg-white dark:bg-[#1a1d24] p-5 hover:border-slate-300 dark:hover:border-[#383f4e] shadow-sm hover:shadow-md ${
            isFocused ? "card-focused" : ""
          }"
        >
          <div>
            <!-- Forbes Eyebrow Meta Header: Category Tag (12px bold), Source (12px), Pub Time -->
            <div class="flex flex-wrap items-center justify-between gap-2 text-xs mb-2.5">
              <div class="flex items-center gap-2 min-w-0">
                <span class="inline-flex items-center gap-1.5 font-sans text-[12px] font-bold tracking-wider uppercase text-rose-700 dark:text-rose-400">
                  <span class="h-2 w-2 rounded-full ${dotColor}"></span>
                  ${escapeHtml(article.category)}
                </span>
                <span class="text-slate-300 dark:text-slate-600 font-mono text-[11px]">/</span>
                <span class="truncate font-sans text-[12px] font-semibold text-slate-500 dark:text-slate-400">
                  ${escapeHtml(article.source)}
                </span>
              </div>
              <time class="shrink-0 font-mono text-[11px] text-slate-400 dark:text-slate-500" datetime="${escapeHtml(article.published_at)}">
                ${escapeHtml(pubTime)}
              </time>
            </div>

            <!-- Forbes Article Headline: 20px-22px Bold Editorial Serif -->
            <h2 class="font-serif text-[20px] md:text-[22px] font-bold leading-[1.3] text-slate-900 dark:text-slate-100 group-hover:text-rose-700 dark:group-hover:text-rose-400 transition-colors">
              <a href="${escapeHtml(article.url)}" target="_blank" rel="noopener noreferrer" class="hover:underline decoration-rose-700/50 underline-offset-4">
                ${escapeHtml(article.title)}
              </a>
            </h2>

            <!-- Forbes Brief / Excerpt: 15px with 1.6 Line Height -->
            <p class="mt-2.5 font-sans text-[15px] leading-[1.6] text-slate-600 dark:text-slate-300">
              ${escapeHtml(article.brief)}
            </p>
          </div>

          <!-- Forbes Action Footer: Read Link (13px Bold), Save / Bookmark Button & Skip Button -->
          <div class="mt-5 flex items-center justify-between border-t border-slate-100 dark:border-[#242934] pt-3.5">
            <a
              href="${escapeHtml(article.url)}"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center gap-1.5 font-sans text-[13px] font-bold text-slate-900 dark:text-slate-200 hover:text-rose-700 dark:hover:text-rose-400 transition"
            >
              <span>Read Full Story</span>
              <span class="text-rose-700 dark:text-rose-400 group-hover:translate-x-1 transition-transform font-bold">→</span>
            </a>

            <div class="flex items-center gap-2">
              <button
                type="button"
                data-save-id="${escapeHtml(article.id)}"
                class="save-btn inline-flex items-center gap-1 rounded border px-2.5 py-1 font-sans text-xs font-semibold transition ${
                  article.saved
                    ? "border-amber-500 bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 hover:bg-amber-100"
                    : "border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-[#20242d] text-slate-600 dark:text-slate-300 hover:border-amber-400 hover:text-amber-700"
                }"
                title="${article.saved ? "Remove from Saved" : "Save to Read Later (press s)"}"
              >
                <svg class="h-3 w-3 ${article.saved ? "fill-amber-500 text-amber-500" : "fill-none text-slate-400"}" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                </svg>
                <span>${article.saved ? "Saved" : "Save"}</span>
              </button>

              <button
                type="button"
                data-dismiss-id="${escapeHtml(article.id)}"
                class="dismiss-btn inline-flex items-center gap-1 rounded border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-[#20242d] px-2.5 py-1 font-sans text-xs font-medium text-slate-500 dark:text-slate-400 hover:border-rose-300 hover:text-rose-700 transition"
                title="Skip this story (press x)"
              >
                <span>${state.activeCategory === "Saved" ? "Remove" : "Skip"}</span>
              </button>
            </div>
          </div>
        </article>
      `;
    })
    .join("");

  grid.querySelectorAll("article[data-article-id]").forEach((cardEl) => {
    cardEl.addEventListener("mouseenter", () => {
      const id = cardEl.getAttribute("data-article-id");
      if (id) setFocusedCard(id, false);
    });
  });

  grid.querySelectorAll(".save-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const id = btn.getAttribute("data-save-id");
      if (id) toggleSaveArticle(id);
    });
  });

  grid.querySelectorAll(".dismiss-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const id = btn.getAttribute("data-dismiss-id");
      if (id) {
        if (state.activeCategory === "Saved") {
          toggleSaveArticle(id);
        } else {
          dismissSingleArticle(id);
        }
      }
    });
  });
}

/**
 * Highlight the focused article card for keyboard navigation ('x', 'j', 'k').
 * @param {string} articleId
 * @param {boolean} scrollIntoView
 */
function setFocusedCard(articleId, scrollIntoView = false) {
  state.focusedArticleId = articleId;
  document.querySelectorAll("article[data-article-id]").forEach((el) => {
    if (el.getAttribute("data-article-id") === articleId) {
      el.classList.add("card-focused");
      if (scrollIntoView) {
        el.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    } else {
      el.classList.remove("card-focused");
    }
  });
}

const STORAGE_KEYS = {
  SAVED: "pulsemm_saved_v1",
  DISMISSED: "pulsemm_dismissed_v1",
};

/** @returns {Set<string>} */
function getLocalSavedIds() {
  try {
    const raw = localStorage.getItem(STORAGE_KEYS.SAVED);
    return new Set(raw ? JSON.parse(raw) : []);
  } catch {
    return new Set();
  }
}

/** @param {Set<string>} set */
function persistLocalSavedIds(set) {
  try {
    localStorage.setItem(STORAGE_KEYS.SAVED, JSON.stringify(Array.from(set)));
  } catch {}
}

/** @returns {Set<string>} */
function getLocalDismissedIds() {
  try {
    const raw = localStorage.getItem(STORAGE_KEYS.DISMISSED);
    return new Set(raw ? JSON.parse(raw) : []);
  } catch {
    return new Set();
  }
}

/** @param {Set<string>} set */
function persistLocalDismissedIds(set) {
  try {
    localStorage.setItem(STORAGE_KEYS.DISMISSED, JSON.stringify(Array.from(set)));
  } catch {}
}

/**
 * Load non-dismissed articles from GET /api/articles and merge with local device state.
 * @returns {Promise<ArticlesPayload | null>}
 */
async function loadArticles() {
  try {
    const query =
      state.activeCategory && state.activeCategory !== "All"
        ? `?category=${encodeURIComponent(state.activeCategory)}`
        : "";
    const res = await fetch(`/api/articles${query}`);
    if (!res.ok) return null;
    /** @type {ArticlesPayload} */
    const data = await res.json();

    const localSaved = getLocalSavedIds();
    const localDismissed = getLocalDismissedIds();

    const rawList = (data.articles || []).map((art) => ({
      ...art,
      saved: art.saved || localSaved.has(art.id),
    }));

    if (state.activeCategory === "Saved") {
      state.articles = rawList.filter((a) => a.saved || localSaved.has(a.id));
    } else {
      state.articles = rawList.filter((a) => !localDismissed.has(a.id));
    }

    state.counts = { ...(data.counts || {}) };
    state.counts["Saved"] = localSaved.size;
    state.totalUnread = Math.max(0, (data.total_unread || 0) - localDismissed.size);

    renderCategoryTabs();
    renderArticles();
    return data;
  } catch {
    return null;
  }
}

/**
 * Dismiss a single article with smooth fade-out and persist locally on this device.
 * @param {string} articleId
 */
async function dismissSingleArticle(articleId) {
  const card = document.getElementById(`card-${articleId}`);
  if (card) {
    card.classList.add("card-dismissing");
  }

  // Persist dismissal locally on this device so each user's feed stays private
  const localDismissed = getLocalDismissedIds();
  localDismissed.add(articleId);
  persistLocalDismissedIds(localDismissed);

  // Determine the next focused card before removing
  const idx = state.articles.findIndex((a) => a.id === articleId);
  const removedArticle = idx >= 0 ? state.articles[idx] : null;
  const nextCandidate =
    idx >= 0
      ? state.articles[idx + 1] || state.articles[idx - 1] || null
      : null;

  try {
    fetch(`/api/articles/${encodeURIComponent(articleId)}/dismiss`, {
      method: "POST",
    }).catch(() => {});
  } catch {
    // Continue optimistic removal
  }

  setTimeout(() => {
    state.articles = state.articles.filter((a) => a.id !== articleId);
    if (removedArticle) {
      const cat = removedArticle.category;
      if (state.counts[cat] && state.counts[cat] > 0) {
        state.counts[cat] -= 1;
      }
      if (state.totalUnread > 0) {
        state.totalUnread -= 1;
      }
    }
    state.focusedArticleId = nextCandidate ? nextCandidate.id : null;
    renderCategoryTabs();
    renderArticles();
  }, 200);
}

/**
 * Dismiss all visible articles in the currently active category (or All).
 */
async function dismissVisibleCategory() {
  if (state.articles.length === 0) return;

  const targetCategory = state.activeCategory || "All";
  const localDismissed = getLocalDismissedIds();
  state.articles.forEach((a) => localDismissed.add(a.id));
  persistLocalDismissedIds(localDismissed);

  document.querySelectorAll("article[data-article-id]").forEach((el) => {
    el.classList.add("card-dismissing");
  });

  try {
    fetch("/api/articles/dismiss-category", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ category: targetCategory }),
    }).catch(() => {});
  } catch {
    // Continue
  }

  showStatusPill(`Dismissed ${state.articles.length} stories in ${targetCategory}`);
  setTimeout(() => {
    loadArticles();
  }, 220);
}

let refreshCooldownSeconds = 0;
/** @type {any} */
let refreshTimer = null;

function startRefreshCooldown(seconds = 60) {
  refreshCooldownSeconds = seconds;
  const btn = document.getElementById("refresh-btn");
  const label = document.getElementById("refresh-label");
  if (btn) btn.setAttribute("disabled", "true");

  if (refreshTimer) clearInterval(refreshTimer);
  refreshTimer = setInterval(() => {
    refreshCooldownSeconds -= 1;
    if (refreshCooldownSeconds <= 0) {
      clearInterval(refreshTimer);
      if (btn) btn.removeAttribute("disabled");
      if (label) label.textContent = "Refresh Feeds";
    } else {
      if (label) label.textContent = `Wait (${refreshCooldownSeconds}s)`;
    }
  }, 1000);
}

/**
 * Trigger concurrent fetch across all 180 RSS feeds via POST /api/refresh (with 60s cooldown).
 */
async function triggerRefreshFeeds() {
  if (state.isRefreshing) return;
  if (refreshCooldownSeconds > 0) {
    showStatusPill(`Cooldown: please wait ${refreshCooldownSeconds}s before refreshing again.`);
    return;
  }
  state.isRefreshing = true;

  const btn = document.getElementById("refresh-btn");
  const icon = document.getElementById("refresh-icon");
  const label = document.getElementById("refresh-label");

  if (btn) btn.setAttribute("disabled", "true");
  if (icon) icon.classList.add("animate-spin");
  if (label) label.textContent = "Fetching Feeds…";
  showStatusPill("Fetching all 180 RSS feeds concurrently…");

  try {
    const res = await fetch("/api/refresh", { method: "POST" });
    if (res.ok) {
      const summary = await res.json();
      showStatusPill(
        `+${summary.inserted_articles} new briefs (${summary.succeeded_feeds}/${summary.total_feeds} feeds in ${summary.duration_seconds}s)`
      );
      startRefreshCooldown(60);
    } else if (res.status === 429) {
      const err = await res.json();
      showStatusPill(err.detail || "Cooldown active: please wait before refreshing again.");
      startRefreshCooldown(30);
    } else {
      showStatusPill("Feed refresh encountered an error");
    }
  } catch {
    showStatusPill("Network error while refreshing feeds");
  } finally {
    state.isRefreshing = false;
    if (icon) icon.classList.remove("animate-spin");
    if (refreshCooldownSeconds <= 0) {
      if (btn) btn.removeAttribute("disabled");
      if (label) label.textContent = "Refresh Feeds";
    }
    await loadArticles();
    loadWeather();
    loadMarketRates();
  }
}

/**
 * Toggle bookmark/saved status of an article for the Read Later tab (persisted in localStorage).
 * @param {string} articleId
 */
async function toggleSaveArticle(articleId) {
  const article = state.articles.find((a) => a.id === articleId);
  const willSave = article ? !article.saved : true;

  const localSaved = getLocalSavedIds();
  if (willSave) {
    localSaved.add(articleId);
  } else {
    localSaved.delete(articleId);
  }
  persistLocalSavedIds(localSaved);

  if (article) {
    article.saved = willSave;
  }

  if (willSave) {
    state.counts["Saved"] = localSaved.size;
    showStatusPill("★ Saved to Read Later");
  } else {
    state.counts["Saved"] = localSaved.size;
    showStatusPill("Removed from Saved");
  }
  renderCategoryTabs();

  // If in Saved tab and un-saving, smoothly fade out card
  if (state.activeCategory === "Saved" && !willSave) {
    const card = document.getElementById(`card-${articleId}`);
    if (card) {
      card.classList.add("card-dismissing");
    }
    setTimeout(() => {
      state.articles = state.articles.filter((a) => a.id !== articleId);
      renderArticles();
    }, 200);
  } else {
    renderArticles();
  }

  try {
    fetch(`/api/articles/${encodeURIComponent(articleId)}/toggle-save`, {
      method: "POST",
    }).catch(() => {});
  } catch {
    // Continue
  }
}

/**
 * Global keyboard shortcuts:
 * - 's': Save / Bookmark focused (or top visible) article card
 * - 'x': Dismiss focused (or top visible) article card
 * - 'j': Focus next article card
 * - 'k': Focus previous article card
 * - 'r': Refresh feeds
 */
function setupKeyboardShortcuts() {
  window.addEventListener("keydown", (event) => {
    const target = /** @type {HTMLElement | null} */ (event.target);
    if (
      target &&
      (target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable)
    ) {
      return;
    }
    if (event.metaKey || event.ctrlKey || event.altKey) return;

    const key = event.key.toLowerCase();
    if (key === "s") {
      if (state.articles.length === 0) return;
      event.preventDefault();
      const targetId = state.focusedArticleId || state.articles[0].id;
      toggleSaveArticle(targetId);
    } else if (key === "x") {
      if (state.articles.length === 0) return;
      event.preventDefault();
      const targetId = state.focusedArticleId || state.articles[0].id;
      if (state.activeCategory === "Saved") {
        toggleSaveArticle(targetId);
      } else {
        dismissSingleArticle(targetId);
      }
    } else if (key === "j") {
      if (state.articles.length === 0) return;
      event.preventDefault();
      const idx = state.articles.findIndex(
        (a) => a.id === state.focusedArticleId
      );
      const nextIdx =
        idx < 0 ? 0 : Math.min(state.articles.length - 1, idx + 1);
      setFocusedCard(state.articles[nextIdx].id, true);
    } else if (key === "k") {
      if (state.articles.length === 0) return;
      event.preventDefault();
      const idx = state.articles.findIndex(
        (a) => a.id === state.focusedArticleId
      );
      const prevIdx = idx <= 0 ? 0 : idx - 1;
      setFocusedCard(state.articles[prevIdx].id, true);
    } else if (key === "r") {
      event.preventDefault();
      triggerRefreshFeeds();
    }
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  // Forbes Theme Toggle (Default Light Paper / Soft Charcoal Dark)
  const themeBtn = document.getElementById("toggle-theme-btn");
  const themeIcon = document.getElementById("theme-icon");
  const themeLabel = document.getElementById("theme-label");

  function applyTheme(isDark) {
    if (isDark) {
      document.documentElement.classList.add("dark");
      if (themeIcon) themeIcon.textContent = "☀️";
      if (themeLabel) themeLabel.textContent = "Light";
      localStorage.setItem("pulsemm_theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      if (themeIcon) themeIcon.textContent = "🌙";
      if (themeLabel) themeLabel.textContent = "Dark";
      localStorage.setItem("pulsemm_theme", "light");
    }
  }

  const savedTheme = localStorage.getItem("pulsemm_theme");
  applyTheme(savedTheme === "dark");

  if (themeBtn) {
    themeBtn.addEventListener("click", () => {
      const isCurrentlyDark = document.documentElement.classList.contains("dark");
      applyTheme(!isCurrentlyDark);
    });
  }

  const refreshBtn = document.getElementById("refresh-btn");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => triggerRefreshFeeds());
  }

  const dismissCatBtn = document.getElementById("dismiss-category-btn");
  if (dismissCatBtn) {
    dismissCatBtn.addEventListener("click", () => dismissVisibleCategory());
  }

  const toggleMarketBtn = document.getElementById("toggle-market-btn");
  const marketCardsContainer = document.getElementById("market-cards-container");
  const toggleMarketIcon = document.getElementById("toggle-market-icon");
  const toggleMarketLabel = document.getElementById("toggle-market-label");
  if (toggleMarketBtn && marketCardsContainer) {
    toggleMarketBtn.addEventListener("click", () => {
      const isHidden = marketCardsContainer.classList.toggle("hidden");
      if (toggleMarketIcon) toggleMarketIcon.textContent = isHidden ? "▼" : "▲";
      if (toggleMarketLabel) toggleMarketLabel.textContent = isHidden ? "Show Market" : "Hide Market";
    });
  }

  const toggleCalBtn = document.getElementById("toggle-calibrate-btn");
  const calDrawer = document.getElementById("calibrate-drawer");
  if (toggleCalBtn && calDrawer) {
    toggleCalBtn.addEventListener("click", () => {
      calDrawer.classList.toggle("hidden");
    });
  }

  const saveCalBtn = document.getElementById("save-calibrate-btn");
  if (saveCalBtn) {
    saveCalBtn.addEventListener("click", async () => {
      /** @param {string} id */
      const readNum = (id) => {
        const el = /** @type {HTMLInputElement | null} */ (
          document.getElementById(id)
        );
        if (!el || !el.value.trim()) return null;
        const val = Number(el.value.trim());
        return Number.isFinite(val) && val > 0 ? val : null;
      };

      const pinEl = /** @type {HTMLInputElement | null} */ (
        document.getElementById("cal-pin")
      );
      const pinVal = pinEl && pinEl.value.trim() ? pinEl.value.trim() : "$Billionaire3";

      const payload = {
        usd_mmk: readNum("cal-usd"),
        gold_16pae_mmk: readNum("cal-gold")
          ? Math.round(Number(readNum("cal-gold")))
          : null,
        thb_mmk: readNum("cal-thb"),
        sgd_mmk: readNum("cal-sgd"),
        eur_mmk: readNum("cal-eur"),
        pin: pinVal,
      };

      const res = await fetch("/api/market/calibrate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const data = await res.json();
        renderMarketData(data);
        if (calDrawer) calDrawer.classList.add("hidden");
        showStatusPill("✓ Saved Yangon street market calibration");
      } else if (res.status === 403) {
        showStatusPill("❌ Invalid Admin PIN! Authorization failed.");
      } else {
        showStatusPill("Failed to save market calibration");
      }
    });
  }

  const resetCalBtn = document.getElementById("reset-calibrate-btn");
  if (resetCalBtn) {
    resetCalBtn.addEventListener("click", async () => {
      const pinEl = /** @type {HTMLInputElement | null} */ (
        document.getElementById("cal-pin")
      );
      const pinVal = pinEl && pinEl.value.trim() ? pinEl.value.trim() : "$Billionaire3";

      const res = await fetch(`/api/market/calibrate?pin=${encodeURIComponent(pinVal)}`, { method: "DELETE" });
      if (res.ok) {
        const data = await res.json();
        renderMarketData(data);
        ["cal-usd", "cal-gold", "cal-thb", "cal-sgd", "cal-eur"].forEach(
          (id) => {
            const el = /** @type {HTMLInputElement | null} */ (
              document.getElementById(id)
            );
            if (el) el.value = "";
          }
        );
        if (calDrawer) calDrawer.classList.add("hidden");
        showStatusPill("✓ Reverted to live auto Yangon street scraper");
      } else if (res.status === 403) {
        showStatusPill("❌ Invalid Admin PIN! Authorization failed.");
      } else {
        showStatusPill("Failed to reset market rates");
      }
    });
  }

  setupKeyboardShortcuts();
  updateDismissCategoryButtonLabel();

  loadWeather();
  loadMarketRates();

  const initialData = await loadArticles();
  if (initialData && initialData.total_unread === 0) {
    triggerRefreshFeeds();
  }

  // Auto-update Gold, Currency & Weather every 15 minutes
  setInterval(() => {
    loadWeather();
    loadMarketRates();
  }, 15 * 60 * 1000);

  // Sync latest articles from backend every 5 minutes
  setInterval(() => {
    if (!state.isRefreshing) {
      loadArticles();
    }
  }, 5 * 60 * 1000);

  // Also refresh Market, Weather & Articles when returning to the browser tab
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible" && !state.isRefreshing) {
      loadWeather();
      loadMarketRates();
      loadArticles();
    }
  });
});

import { useEffect } from "react";

const BASE_URL = "https://meeting-gaffer.com";
const DEFAULT_TITLE = "Gaffer - AI Motivational Speeches for Your Meetings";
const DEFAULT_DESCRIPTION =
  "Get AI-generated football manager-style hype speeches before your meetings. Choose from Ferguson, Klopp, Guardiola, and more.";

type SEOOptions = {
  title?: string;
  description?: string;
  /** Path portion only, e.g. "/privacy". Defaults to window.location.pathname. */
  path?: string;
  /** Override og:title if different from <title> */
  ogTitle?: string;
  /** Override og:description if different from meta description */
  ogDescription?: string;
  /** Prevent search engine indexing (e.g. for /login, /dashboard) */
  noIndex?: boolean;
};

function setMetaTag(
  attribute: "name" | "property",
  key: string,
  content: string,
) {
  let el = document.querySelector(
    `meta[${attribute}="${key}"]`,
  );
  if (!el) {
    el = document.createElement("meta");
    el.setAttribute(attribute, key);
    document.head.appendChild(el);
  }
  el.setAttribute("content", content);
}

function setLinkTag(rel: string, href: string) {
  let el = document.querySelector(
    `link[rel="${rel}"]`,
  );
  if (!el) {
    el = document.createElement("link");
    el.setAttribute("rel", rel);
    document.head.appendChild(el);
  }
  el.setAttribute("href", href);
}

export function useSEO(options: SEOOptions = {}) {
  const {
    title = DEFAULT_TITLE,
    description = DEFAULT_DESCRIPTION,
    path,
    ogTitle,
    ogDescription,
    noIndex = false,
  } = options;

  useEffect(() => {
    const canonicalPath = path ?? window.location.pathname;
    const canonicalUrl = `${BASE_URL}${canonicalPath}`;

    document.title = title;

    setMetaTag("name", "description", description);
    setLinkTag("canonical", canonicalUrl);

    setMetaTag("property", "og:title", ogTitle ?? title);
    setMetaTag("property", "og:description", ogDescription ?? description);
    setMetaTag("property", "og:url", canonicalUrl);

    setMetaTag("name", "twitter:title", ogTitle ?? title);
    setMetaTag("name", "twitter:description", ogDescription ?? description);
    setMetaTag("name", "twitter:url", canonicalUrl);

    if (noIndex) {
      setMetaTag("name", "robots", "noindex, nofollow");
    } else {
      const robotsMeta = document.querySelector('meta[name="robots"]');
      if (robotsMeta) {
        robotsMeta.remove();
      }
    }
  }, [title, description, path, ogTitle, ogDescription, noIndex]);
}

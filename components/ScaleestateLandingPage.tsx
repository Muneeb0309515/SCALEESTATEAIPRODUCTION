import Image from "next/image";
import Link from "next/link";
import {
  ArrowRight,
  Building2,
  Calculator,
  MapPinned,
  Search,
  ShieldCheck,
} from "lucide-react";
import { LivePropertySearch } from "@/components/LivePropertySearch";

const capabilities = [
  {
    icon: Search,
    title: "Discover with source context",
    description:
      "Search provider-backed listings and keep their identity, freshness, and original source attached to the record.",
    href: "/search",
    link: "Explore live search",
  },
  {
    icon: Building2,
    title: "Research the property record",
    description:
      "Carry a listing into an organization-scoped detail view with known facts, provenance, and original photos.",
    href: "/properties",
    link: "Open property records",
  },
  {
    icon: Calculator,
    title: "Underwrite deterministically",
    description:
      "Run transparent server-side formulas from your inputs. Unknowns stay unknown; AI does not calculate the deal.",
    href: "/deals",
    link: "Review deal analysis",
  },
];

export function ScaleestateLandingPage() {
  return (
    <main className="marketing-shell">
      <header className="marketing-nav">
        <Link
          className="marketing-brand"
          href="/"
          aria-label="SCALEESTATE AI home"
        >
          <span className="marketing-brand-mark" aria-hidden="true">
            <Building2 size={19} />
          </span>
          <span className="marketing-brand-type">
            <strong>SCALEESTATE</strong>
            <em>AI</em>
          </span>
        </Link>
        <nav className="marketing-links" aria-label="Main navigation">
          <a href="#platform">Platform</a>
          <a href="#live-search">Live search</a>
          <a href="#workflow">How it works</a>
        </nav>
        <div className="marketing-actions">
          <Link className="marketing-signin" href="/sign-in?next=%2Fsearch">
            Sign in
          </Link>
          <a
            className="button button-primary marketing-nav-cta"
            href="#live-search"
          >
            Explore the platform <ArrowRight size={15} />
          </a>
        </div>
      </header>

      <section className="marketing-hero" aria-labelledby="marketing-title">
        <div className="marketing-hero-copy">
          <p className="marketing-kicker">
            <span /> Real estate intelligence for operators
          </p>
          <h1 id="marketing-title">
            Find the signal.
            <span>Move with confidence.</span>
          </h1>
          <p className="marketing-hero-description">
            SCALEESTATE brings live property discovery, source-aware research,
            and deterministic deal analysis into one disciplined workspace.
          </p>
          <div className="marketing-hero-actions">
            <a className="button button-primary" href="#live-search">
              <Search size={16} /> Explore live property search
            </a>
            <Link
              className="marketing-secondary-link"
              href="/sign-in?next=%2Fsearch"
            >
              Sign in to your workspace <ArrowRight size={15} />
            </Link>
          </div>
          <div className="marketing-assurance">
            <ShieldCheck size={16} />
            <span>Organization-scoped access</span>
            <i />
            <span>Source-aware records</span>
          </div>
        </div>

        <figure className="marketing-hero-visual">
          <Image
            src="/images/scaleestate-hero.webp"
            alt="Contemporary single-family home at golden hour"
            fill
            priority
            sizes="(max-width: 850px) 100vw, 52vw"
            className="marketing-hero-image"
          />
          <div className="marketing-image-shade" aria-hidden="true" />
          <figcaption className="marketing-image-caption">
            <span className="marketing-image-caption-icon">
              <MapPinned size={17} />
            </span>
            <span>
              <strong>Built around the property record</strong>
              <small>From first search to informed next step</small>
            </span>
          </figcaption>
          <span className="marketing-source-chip">
            <span /> Source-first research
          </span>
        </figure>
      </section>

      <section
        className="marketing-principles"
        aria-label="Platform principles"
      >
        <div>
          <ShieldCheck size={18} />
          <span>Organization-scoped workspace</span>
        </div>
        <div>
          <MapPinned size={18} />
          <span>Provider identity and freshness retained</span>
        </div>
        <div>
          <Calculator size={18} />
          <span>Deterministic backend calculations</span>
        </div>
      </section>

      <section className="marketing-capabilities" id="platform">
        <div className="marketing-section-heading">
          <p className="eyebrow">A more disciplined workflow</p>
          <h2>Evidence first. Decisions second.</h2>
          <p>
            Keep property facts, user assumptions, and calculated results
            distinct as you move from discovery to analysis.
          </p>
        </div>
        <div className="marketing-capability-grid" id="workflow">
          {capabilities.map(
            ({ icon: Icon, title, description, href, link }) => (
              <article className="marketing-capability-card" key={title}>
                <span className="marketing-capability-icon">
                  <Icon size={20} />
                </span>
                <h3>{title}</h3>
                <p>{description}</p>
                <Link href={href}>
                  {link} <ArrowRight size={14} />
                </Link>
              </article>
            )
          )}
        </div>
      </section>

      <section className="marketing-live-search" id="live-search">
        <div className="marketing-search-intro">
          <p className="eyebrow">Start with the source</p>
          <h2>Search the market. Keep the context.</h2>
          <p>
            Live searches require an approved workspace account and the
            configured property-data provider. Results are returned by the
            authenticated backend; this page does not show sample or invented
            listings.
          </p>
        </div>
        <LivePropertySearch />
      </section>

      <section className="marketing-bottom-cta">
        <div>
          <p className="eyebrow">SCALEESTATE AI</p>
          <h2>Make the next decision with better evidence.</h2>
          <p>Start in the live search workspace or return to your account.</p>
        </div>
        <div className="marketing-bottom-actions">
          <Link className="button button-primary" href="/search">
            Open property search <ArrowRight size={15} />
          </Link>
          <Link
            className="button button-secondary"
            href="/sign-in?next=%2Fsearch"
          >
            Sign in
          </Link>
        </div>
      </section>

      <footer className="marketing-footer">
        <Link className="marketing-footer-brand" href="/">
          SCALEESTATE <span>AI</span>
        </Link>
        <p>
          Property intelligence with provenance and transparent calculations.
        </p>
        <Link href="/search">
          Workspace <ArrowRight size={13} />
        </Link>
      </footer>
    </main>
  );
}

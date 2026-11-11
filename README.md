# Engineering portfolio

The source for Codeman-lex’s engineering portfolio. All pages are built with HTML, CSS and JavaScript. Each case study includes an interactive example, screenshots from the application, engineering decisions, and a downloadable project with tests.

## Explore the website code

- [HTML entry point](dist/index.html)
- [Navigation and case-study renderer](dist/portfolio.js)
- [Project covers](dist/covers.js) and [cover styling](dist/covers.css)
- [Browser exercises](dist/demos.js)
- [Sentinel AI case study](dist/projects.js)
- [Veritas and Aegis case studies](dist/additional-projects.js)
- [Layout and typography](dist/portfolio.css)

## Run locally

From the repository root, run:

```sh
python3 -m http.server 8080 --directory dist
```

Open http://localhost:8080. The three application source archives in [dist/media](dist/media) include their own installation instructions and tests. All financial, evaluation and onboarding examples use synthetic data. Development was AI-assisted.

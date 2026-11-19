# Graphical XML editor

From `website/editor` run `npm ci` to install the editor dependencies.

- `npm run build` writes the editor bundles to `website/dist/editor`.
- `npm run serve` serves the bundles at `http://localhost:8081/`. Enable
  `GRAPHICAL_EDITOR_WEBPACK_DEV_SERVER_URL` in `website/config.js` to load them in Lexonomy.
- `npm run lint -- --no-fix` checks for lint errors.

See the repository's [installation instructions](../../INSTALL.md) to run Lexonomy and build both frontends.

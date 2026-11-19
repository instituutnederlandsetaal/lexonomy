import riot from 'rollup-plugin-riot'
import nodeResolve from '@rollup/plugin-node-resolve'
import postcss from 'rollup-plugin-postcss'
import url from 'postcss-url'
import { resolve } from 'node:path'

export default [{
  input: 'app.js',
  output: {
    file: 'dist/riot/bundle.js',
    format: 'iife',
    strict: false
  },
  plugins: [
    riot(),
    nodeResolve(),
  ],
  onwarn(warning, warn) {
    if (warning.code === 'EVAL') return;
    warn(warning);
  }
}, {
  input: 'app.static.js',
  context: 'window',
  output: {
    file: 'dist/riot/bundle.static.js',
    format: 'iife',
    strict: false
  },
  plugins: [
    postcss({
      plugins: [url({
        url: 'copy',
        assetsPath: resolve('dist/assets'),
        useHash: true,
        basePath: [
          resolve('.'),
          resolve('widgets'),
          resolve('libs/screenful'),
          resolve('img/materialize-colorpicker'),
          resolve('libs/jquery'),
          '.'
        ]
      })],
      extract: 'bundle.css',
      to: resolve('dist/riot/bundle.css')
    })
  ],
  onwarn(warning, warn) {
    if (warning.code === 'EVAL') return;
    warn(warning);
  }
}]

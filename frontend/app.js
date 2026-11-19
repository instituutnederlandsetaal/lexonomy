import { createApp } from 'vue'
import Main from './components/main.vue'
import { router } from './js/router.ts'
import './libs/materialize/css/materialize.min.css'
import './css/lexonomy.css'
import './css/elexis-style.css'

createApp(Main).use(router).mount('#root')

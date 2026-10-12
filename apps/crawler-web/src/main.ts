import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './assets/styles/main.css'

import DashboardView from './views/DashboardView.vue'
import CrawlView from './views/CrawlView.vue'
import TopicsView from './views/TopicsView.vue'
import NewsView from './views/NewsView.vue'
import SettingsView from './views/SettingsView.vue'

const routes = [
  { path: '/', name: 'dashboard', component: DashboardView },
  { path: '/crawl', name: 'crawl', component: CrawlView },
  { path: '/topics', name: 'topics', component: TopicsView },
  { path: '/news', name: 'news', component: NewsView },
  { path: '/settings', name: 'settings', component: SettingsView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const app = createApp(App)
app.use(router)
app.mount('#app')

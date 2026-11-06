import { createRouter, createWebHistory } from 'vue-router'
import { auth } from './auth'
import LoginView from './views/LoginView.vue'
import EventsView from './views/EventsView.vue'
import EventDetailView from './views/EventDetailView.vue'
import VehicleView from './views/VehicleView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/eventos' },
    { path: '/login', component: LoginView, meta: { public: true } },
    { path: '/eventos', component: EventsView },
    { path: '/eventos/:id', component: EventDetailView, props: true },
    { path: '/vehiculos/:id?', component: VehicleView, props: true }
  ]
})

router.beforeEach((to) => {
  if (to.meta.public) return auth.token ? '/eventos' : true
  if (!auth.token) return '/login'
  return true
})

export default router

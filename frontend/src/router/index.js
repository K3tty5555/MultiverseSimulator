import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import ProfileView from '../views/ProfileView.vue'
import SettingsView from '../views/SettingsView.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/profile',
    name: 'Profile',
    component: ProfileView
  },
  {
    path: '/agents',
    name: 'Agents',
    component: () => import('../views/AgentsView.vue')
  },
  {
    path: '/agents/:name',
    name: 'AgentTimeline',
    component: () => import('../views/AgentTimelineView.vue'),
    props: true
  },
  {
    path: '/settings',
    name: 'Settings',
    component: SettingsView
  },
  {
    path: '/universe',
    name: 'UniverseExplore',
    component: () => import('../views/WorldExploreView.vue')
  },
  {
    path: '/universe/worlds/:worldId',
    name: 'WorldDetail',
    component: () => import('../views/WorldDetailView.vue'),
    props: true,
    beforeEnter: (to) => {
      if (!to.params.worldId) return '/'
    },
  },
  {
    path: '/universe/:universeId',
    name: 'Universe',
    component: () => import('../views/UniverseView.vue'),
    props: true
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

import { createRouter, createWebHistory } from 'vue-router'
// import HomeView from '../views/HomeView.vue'
import HomePage from '../pages/HomePage.vue'
// import CableGlandItemType from '../components/CableGlandItemType';  // Импорт компонента

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomePage,
  },
  {
    path: '/about',
    name: 'about',
    // route level code-splitting
    // this generates a separate chunk (About.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () => import('../pages/AboutPage.vue'),
  },
  // {
  //   path: '/cg',
  //   name: 'CableGlandItemTypes',
  //   component: CableGlandItemType,  // Назначаем компонент для этого маршрута
  // },
  // { path: '/', component: HomePage },
  // { path: '/drive-selection', component: () => import('../pages/electric_actuators/ActuatorList.vue') },
  { path: '/drive-selection', component: () => import('../components/OldSortedTable.vue') },
  { path: '/cable-gland-edit', component: () => import('../pages/cable_glands/CableGlandEditPage.vue') },
  { path: '/cable-gland-body-material-edit', component: () => import('../pages/cable_glands/CableGlandBodyMaterial.vue') },
  { path: '/adaptation-data', component: () => import('../pages/adaptation/AdaptationMainPage.vue') },
  { path: '/cable-input-data', component: () => import('../pages/cable_glands/CableMainPage.vue') },
  { path: '/login', component: () => import('../pages/auth/LoginMainPage.vue') },
  { path: '/register', component: () => import('../pages/auth/RegisterMainPage.vue') },
  { path: '/drive-data', component: () => import('../pages/electric_actuators/DriveDataMainPage.vue') },
  { path: '/ett-decode', component: () => import('../components/ett/EttDecodePage.vue') },
  { path: '/actuator-edit', component: () => import('../components/ActuatorEdit1.vue') },
  { path: '/client-requests', component: () => import('../pages/client_request/ClientRequest.vue') },
  // { path: '/cable-input-data', component: CableGlandEdit },
]
const router = createRouter({
  history: createWebHistory(),
  routes,
});
export default router

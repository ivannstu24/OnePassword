import { createRouter, createWebHistory } from 'vue-router';
import UserAuth from '../views/UserAuth.vue';
import PasswordManager from '../views/PasswordManager.vue';
import PasswordGenerator from '../views/PasswordGenerator.vue';
import Profile from '../views/UserProfile.vue';

const routes = [
    { path: '/', component: UserAuth },
    { path: '/manager', component: PasswordManager },
    { path: '/generator', component: PasswordGenerator },
    { path: '/profile', component: Profile },
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

export default router;
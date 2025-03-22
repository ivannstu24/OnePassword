<template>
  <div id="app">
    <nav v-if="isAuthenticated">
      <router-link to="/manager">Менеджер паролей</router-link> |
      <router-link to="/generator">Генератор паролей</router-link> |
                <router-link to="/profile" class="profile-link">Личный кабинет</router-link> |

      <button @click="logout">Выйти</button>

    </nav>

    <router-view></router-view>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      isAuthenticated: false,
    };
  },
  methods: {
    logout() {
      this.isAuthenticated = false;
      localStorage.removeItem('username');
      this.$router.push('/');
    },
  },
  created() {
    const username = localStorage.getItem('username');
    if (username) {
      this.isAuthenticated = true;
    }
  },
};
</script>

<style>
body {
  font-family: Arial, sans-serif;
  background-color: #f4f4f4;
  margin: 0;
  padding: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
}

nav {
  margin-bottom: 20px;
  text-align: center;
}

nav a {
  margin: 0 10px;
  text-decoration: none;
  color: #3760db;
}

nav a:hover {
  text-decoration: underline;
}

button {
  background-color: #3760db;
  color: white;
  border: none;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background-color: #509ae9;
}
</style>
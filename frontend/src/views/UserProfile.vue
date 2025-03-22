<template>
  <div class="profile-container">
    <h2>Личный кабинет</h2>
    <div class="profile-info">
      <div class="avatar-section">
        <img :src="avatarUrl" alt="Аватар" class="avatar" v-if="avatarUrl">
        <div v-else class="avatar-placeholder">Загрузите аватар</div>
        <input type="file" @change="uploadAvatar" accept="image/*" class="avatar-input">
      </div>
      <div class="user-info">
        <p><strong>Имя пользователя:</strong> {{ username }}</p>
        <p>
          <strong>Почта:</strong>
          <input v-model="email" placeholder="Введите почту" class="email-input">
        </p>
      </div>
    </div>
    <button @click="updateProfile" class="btn">Обновить профиль</button>
  </div>
</template>

<script>
export default {
  data() {
    return {
      username: '',
      email: '',
      avatarUrl: '',
      avatarFile: null,
    };
  },
  async created() {
    const username = localStorage.getItem('username');
    if (username) {
      this.username = username;
      await this.fetchProfile();
    }
  },
  methods: {
    async fetchProfile() {
      const response = await fetch(`http://localhost:5000/get_profile?username=${this.username}`);
      if (response.ok) {
        const profile = await response.json();
        this.email = profile.email;
        this.avatarUrl = profile.avatarUrl;
      }
    },
    uploadAvatar(event) {
      const file = event.target.files[0];
      if (file) {
        this.avatarFile = file;
        this.avatarUrl = URL.createObjectURL(file);
      }
    },
    async updateProfile() {
      const formData = new FormData();
      formData.append('username', this.username);
      formData.append('email', this.email);
      if (this.avatarFile) {
        formData.append('avatar', this.avatarFile);
      }

      const response = await fetch('http://localhost:5000/update_profile', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        this.avatarUrl = result.avatarUrl;
        alert('Профиль обновлен');
      } else {
        alert('Ошибка обновления профиля');
      }
    },
  },
};
</script>

<style scoped>
.profile-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background-color: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  font-size: 14px;
  color: #666;
}

.avatar-input {
  margin-top: 10px;
}

.email-input {
  padding: 5px;
  border: 1px solid #ccc;
  border-radius: 4px;
  margin-left: 10px;
}

.btn {
  padding: 10px 20px;
  background-color: #3760db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn:hover {
  background-color: #509ae9;
}
</style>
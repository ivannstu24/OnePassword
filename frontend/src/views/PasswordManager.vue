<template>
  <div class="manager-container">
    <h2>Менеджер паролей</h2>

    <div class="password-form">
      <input v-model="service" placeholder="Сервис" class="input-field">
      <input v-model="savedPassword" type="password" placeholder="Пароль" class="input-field" @input="checkPasswordStrength">
      <div class="password-strength">
        <div class="strength-bar" :style="strengthBarStyle"></div>
        <span :class="strengthClass">{{ strengthMessage }}</span>
      </div>
      <button @click="savePassword" class="btn">Сохранить</button>
    </div>

    <h3>Мои пароли:</h3>
    <ul class="password-list">
      <li v-for="(pass, index) in passwords" :key="index" class="password-item">
        <span>{{ pass.service }}: </span>
        <span v-if="!pass.visible">••••••••</span>
        <span v-else>{{ pass.password }}</span>
        <button @click="toggleVisibility(index)" class="eye-button">
          <span v-if="!pass.visible">👁️</span>
          <span v-else>👁️‍🗨️</span>
        </button>
        <button @click="editPassword(index)" class="edit-button">✏️</button>
        <button @click="deletePassword(index)" class="delete-button">🗑️</button>
      </li>
    </ul>

    <div v-if="editingIndex !== null" class="modal">
      <div class="modal-content">
        <h3>Редактирование пароля</h3>
        <input v-model="editService" placeholder="Сервис" class="input-field">
        <input v-model="editPasswordValue" type="password" placeholder="Пароль" class="input-field">
        <button @click="saveEditedPassword" class="btn">Сохранить</button>
        <button @click="cancelEdit" class="btn btn-cancel">Отмена</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      service: '',
      savedPassword: '',
      passwords: [],
      strengthMessage: '',
      strengthClass: '',
      strengthBarWidth: '0%',
      strengthBarColor: 'red',
      editingIndex: null,
      editService: '',
      editPasswordValue: '',
    };
  },
  async created() {
    const username = localStorage.getItem('username');
    if (username) {
      const response = await fetch(`http://localhost:5000/get_passwords?username=${username}`);
      const passwords = await response.json();
      this.passwords = passwords.map(pass => ({ ...pass, visible: false }));
    }
  },
  methods: {
    async savePassword() {
      const username = localStorage.getItem('username');
      if (!username) {
        alert('Не авторизован');
        return;
      }

      const response = await fetch('http://localhost:5000/save_password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, service: this.service, password: this.savedPassword }),
      });
      if (response.ok) {
        this.passwords.push({ service: this.service, password: this.savedPassword, visible: false });
        this.service = '';
        this.savedPassword = '';
        alert('Пароль сохранен');
      } else {
        alert('Ошибка сохранения пароля');
      }
    },
    checkPasswordStrength() {
      const password = this.savedPassword;
      let strength = 0;

      if (password.length >= 8) strength += 1;
      if (password.match(/[A-Z]/)) strength += 1;
      if (password.match(/[0-9]/)) strength += 1;
      if (password.match(/[^A-Za-z0-9]/)) strength += 1;

      if (strength === 0) {
        this.strengthMessage = 'Очень слабый';
        this.strengthClass = 'strength-weak';
        this.strengthBarWidth = '20%';
        this.strengthBarColor = 'red';
      } else if (strength === 1) {
        this.strengthMessage = 'Слабый';
        this.strengthClass = 'strength-weak';
        this.strengthBarWidth = '40%';
        this.strengthBarColor = 'red';
      } else if (strength === 2) {
        this.strengthMessage = 'Средний';
        this.strengthClass = 'strength-medium';
        this.strengthBarWidth = '60%';
        this.strengthBarColor = 'orange';
      } else if (strength === 3) {
        this.strengthMessage = 'Сильный';
        this.strengthClass = 'strength-strong';
        this.strengthBarWidth = '80%';
        this.strengthBarColor = 'green';
      } else if (strength === 4) {
        this.strengthMessage = 'Очень сильный';
        this.strengthClass = 'strength-strong';
        this.strengthBarWidth = '100%';
        this.strengthBarColor = 'green';
      }
    },
    toggleVisibility(index) {
      this.passwords[index].visible = !this.passwords[index].visible;
    },
    editPassword(index) {
      this.editingIndex = index;
      this.editService = this.passwords[index].service;
      this.editPasswordValue = this.passwords[index].password;
    },
    async saveEditedPassword() {
      const username = localStorage.getItem('username');
      if (!username) {
        alert('Не авторизован');
        return;
      }

      const response = await fetch('http://localhost:5000/update_password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username,
          oldService: this.passwords[this.editingIndex].service,
          newService: this.editService,
          newPassword: this.editPasswordValue,
        }),
      });

      if (response.ok) {
        this.passwords[this.editingIndex].service = this.editService;
        this.passwords[this.editingIndex].password = this.editPasswordValue;
        this.cancelEdit();
        alert('Пароль обновлен');
      } else {
        alert('Ошибка обновления пароля');
      }
    },
    cancelEdit() {
      this.editingIndex = null;
      this.editService = '';
      this.editPasswordValue = '';
    },
    async deletePassword(index) {
      const username = localStorage.getItem('username');
      if (!username) {
        alert('Не авторизован');
        return;
      }

      const service = this.passwords[index].service;
      const response = await fetch('http://localhost:5000/delete_password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, service }),
      });

      if (response.ok) {
        this.passwords.splice(index, 1);
        alert('Пароль удален');
      } else {
        alert('Ошибка удаления пароля');
      }
    },
  },
  computed: {
    strengthBarStyle() {
      return {
        width: this.strengthBarWidth,
        backgroundColor: this.strengthBarColor,
      };
    },
  },
};
</script>

<style scoped>
.manager-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.profile-link {
  display: block;
  margin-bottom: 20px;
  color: #3760db;
  text-decoration: none;
}

.profile-link:hover {
  text-decoration: underline;
}

.password-form {
  margin-bottom: 20px;
}

.input-field {
  width: 94%;
  padding: 10px;
  margin: 10px 0;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.password-strength {
  margin-top: 10px;
  font-size: 14px;
}

.strength-bar {
  height: 5px;
  border-radius: 2px;
  transition: width 0.3s ease, background-color 0.3s ease;
}

.strength-weak {
  color: red;
}

.strength-medium {
  color: orange;
}

.strength-strong {
  color: green;
}

.btn {
  width: 100%;
  padding: 10px;
  background-color: #3760db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn:hover {
  background-color: #509ae9;
}

.password-list {
  list-style-type: none;
  padding: 0;
}

.password-item {
  padding: 10px;
  margin: 5px 0;
  background-color: #f9f9f9;
  border: 1px solid #ddd;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.eye-button,
.edit-button,
.delete-button {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  margin-left: 10px;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
}

.modal-content {
  background-color: #fff;
  padding: 20px;
  border-radius: 8px;
  width: 300px;
}

.btn-cancel {
  background-color: #ccc;
  margin-left: 10px;
}
</style>
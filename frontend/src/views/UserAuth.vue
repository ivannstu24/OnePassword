<template>
  <div>
    <div v-if="isLoading" class="spinner-overlay">
      <div class="spinner"></div>
    </div>

    <header class="header">
      <h1>One Password 🔓</h1>
    </header>

    <div class="auth-container">
      <div v-if="!showRegister">
        <h2>Вход</h2>
        <input v-model="username" placeholder="Имя пользователя" class="input-field">
        <input v-model="password" type="password" placeholder="Пароль" class="input-field">
        <button @click="login" class="btn">Войти</button>
        <p class="switch-text">
          Нет аккаунта?
          <a href="#" @click.prevent="toggleRegister">Зарегистрироваться</a>
        </p>
      </div>

      <div v-else>
        <h2>Регистрация</h2>
        <input v-model="regUsername" placeholder="Имя пользователя" class="input-field">
        <input v-model="regEmail" placeholder="Электронная почта" class="input-field" @input="validateEmailOnInput">
        <div v-if="emailError" class="error-message">{{ emailError }}</div>
        <input v-model="regPassword" type="password" placeholder="Пароль" class="input-field" @input="validatePasswordOnInput">
        <div v-if="passwordError" class="error-message">{{ passwordError }}</div>
        <input v-model="confirmPassword" type="password" placeholder="Подтвердите пароль" class="input-field">
        <div v-if="confirmPasswordError" class="error-message">{{ confirmPasswordError }}</div>
        <button @click="register" class="btn">Зарегистрироваться</button>
        <p class="switch-text">
          Уже есть аккаунт?
          <a href="#" @click.prevent="toggleRegister">Войти</a>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'UserAuth',
  data() {
    return {
      regUsername: '',
      regEmail: '',
      regPassword: '',
      confirmPassword: '',
      username: '',
      password: '',
      showRegister: false,
      emailError: '',
      passwordError: '',
      confirmPasswordError: '',
      isLoading: false,
    };
  },
  methods: {
    toggleRegister() {
      this.showRegister = !this.showRegister;
      this.clearFields();
    },

    clearFields() {
      this.regUsername = '';
      this.regEmail = '';
      this.regPassword = '';
      this.confirmPassword = '';
      this.username = '';
      this.password = '';
      this.emailError = '';
      this.passwordError = '';
      this.confirmPasswordError = '';
    },

    validateEmail(email) {
      const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return re.test(email);
    },

    validateEmailOnInput() {
      if (!this.regEmail) {
        this.emailError = '';
      } else if (!this.validateEmail(this.regEmail)) {
        this.emailError = 'Пожалуйста, введите корректный адрес электронной почты';
      } else {
        this.emailError = '';
      }
    },

    validatePassword(password) {
      const minLength = 8;
      const hasNumber = /\d/;
      const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/;
      return password.length >= minLength && hasNumber.test(password) && hasSpecialChar.test(password);
    },

    validatePasswordOnInput() {
      if (!this.regPassword) {
        this.passwordError = '';
      } else if (!this.validatePassword(this.regPassword)) {
        this.passwordError = 'Пароль должен содержать минимум 8 символов, включая цифры и специальные символы';
      } else {
        this.passwordError = '';
      }
    },

    validateConfirmPassword() {
      if (this.regPassword !== this.confirmPassword) {
        this.confirmPasswordError = 'Пароли не совпадают';
        return false;
      } else {
        this.confirmPasswordError = '';
        return true;
      }
    },

    validateRegistration() {
      let isValid = true;

      if (!this.regUsername) {
        alert('Пожалуйста, введите имя пользователя');
        isValid = false;
      }

      if (!this.regEmail) {
        this.emailError = 'Пожалуйста, введите адрес электронной почты';
        isValid = false;
      } else if (!this.validateEmail(this.regEmail)) {
        this.emailError = 'Пожалуйста, введите корректный адрес электронной почты';
        isValid = false;
      }

      if (!this.regPassword) {
        this.passwordError = 'Пожалуйста, введите пароль';
        isValid = false;
      } else if (!this.validatePassword(this.regPassword)) {
        this.passwordError = 'Пароль должен содержать минимум 8 символов, включая цифры и специальные символы';
        isValid = false;
      }

      if (!this.confirmPassword) {
        this.confirmPasswordError = 'Пожалуйста, подтвердите пароль';
        isValid = false;
      } else if (!this.validateConfirmPassword()) {
        isValid = false;
      }

      return isValid;
    },

    validateLogin() {
      if (!this.username || !this.password) {
        alert('Пожалуйста, заполните все поля');
        return false;
      }
      return true;
    },

    async register() {
      if (!this.validateRegistration()) return;

      this.isLoading = true;

      try {
        const response = await fetch('http://localhost:5000/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: this.regUsername,
            email: this.regEmail,
            password: this.regPassword
          }),
        });

        if (response.ok) {
          alert('Регистрация успешна');
          this.toggleRegister();
        } else {
          alert('Ошибка регистрации');
        }
      } catch (error) {
        alert('Произошла ошибка при регистрации');
      } finally {
        this.isLoading = false;
      }
    },

    async login() {
      if (!this.validateLogin()) return;

      this.isLoading = true;

      try {
        const response = await fetch('http://localhost:5000/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: this.username, password: this.password }),
        });

        if (response.ok) {
          localStorage.setItem('username', this.username); // Сохраняем имя пользователя в localStorage
          this.$router.push('/manager');
        } else {
          alert('Неверные логин или пароль');
        }
      } catch (error) {
        alert('Произошла ошибка при входе');
      } finally {
        this.isLoading = false;
      }
    },
  },
};
</script>

<style scoped>
.header {
  background-color: #3760db;
  color: white;
  padding: 20px;
  text-align: center;
}

.header h1 {
  margin: 0;
  font-size: 24px;
}

.auth-container {
  max-width: 400px;
  margin: 20px auto;
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.input-field {
  width: 94%;
  padding: 10px;
  margin: 10px 0;
  border: 1px solid #ccc;
  border-radius: 4px;
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

.switch-text {
  text-align: center;
  margin-top: 10px;
}

.switch-text a {
  color: #3760db;
  text-decoration: none;
}

.switch-text a:hover {
  text-decoration: underline;
}

.error-message {
  color: red;
  font-size: 12px;
  margin-top: -8px;
  margin-bottom: 10px;
}

.spinner-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3760db;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
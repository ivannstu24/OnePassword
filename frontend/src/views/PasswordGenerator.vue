<template>
  <div class="generator-container">
    <h2>Генератор паролей</h2>
    <input v-model="generatedPassword" readonly class="input-field">
    <button @click="generatePassword" class="btn">Сгенерировать</button>
    <button @click="copyPassword" class="btn">Скопировать</button>
  </div>
</template>

<script>
export default {
  data() {
    return {
      generatedPassword: '',
    };
  },
  methods: {
    generatePassword() {
      const length = 16;
      const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()-_=+";
      let password = "";
      for (let i = 0; i < length; i++) {
        password += chars.charAt(Math.floor(Math.random() * chars.length));
      }
      this.generatedPassword = password;
    },
    copyPassword() {
      navigator.clipboard.writeText(this.generatedPassword);
      alert('Пароль скопирован');
    },
  },
};
</script>

<style scoped>
.generator-container {
  max-width: 400px;
  margin: 0 auto;
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}
</style>
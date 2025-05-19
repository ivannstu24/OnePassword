<template>
    <div class="notification-container" v-if="notifications.length">
      <div 
        v-for="(notification, index) in notifications" 
        :key="index"
        class="notification"
        :class="notification.type"
        @click="removeNotification(index)"
      >
        {{ notification.message }}
      </div>
    </div>
  </template>
  
  <script>
  export default {
    data() {
      return {
        notifications: []
      };
    },
    methods: {
      addNotification(message, type = 'error') {
        const notification = { message, type };
        this.notifications.push(notification);
        setTimeout(() => {
          this.removeNotification(this.notifications.indexOf(notification));
        }, 5000);
      },
      removeNotification(index) {
        if (index >= 0 && index < this.notifications.length) {
          this.notifications.splice(index, 1);
        }
      }
    }
  };
  </script>
  
  <style scoped>
  .notification-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 1000;
  }
  
  .notification {
    padding: 15px 20px;
    margin-bottom: 10px;
    border-radius: 4px;
    color: white;
    cursor: pointer;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    animation: slideIn 0.3s ease-out;
  }
  
  .error {
    background-color: #ff4444;
  }
  
  .success {
    background-color: #00C851;
  }
  
  .warning {
    background-color: #ffbb33;
  }
  
  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  </style>
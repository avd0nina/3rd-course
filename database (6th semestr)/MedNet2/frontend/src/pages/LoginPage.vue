<template>
  <main class="login-page">
    <section class="login-card">
      <h1>Вход в MedNet</h1>
      <p class="login-subtitle">Авторизация по ролям: администратор системы и специалист лабораторий.</p>

      <div v-if="error" class="error-box">{{ error }}</div>

      <form class="login-form" @submit.prevent="signIn">
        <label class="field">
          <span>Логин</span>
          <input v-model="username" type="text" autocomplete="username" required />
        </label>

        <label class="field">
          <span>Пароль</span>
          <input v-model="password" type="password" autocomplete="current-password" required />
        </label>

        <button class="btn btn-primary" type="submit" :disabled="isLoading">
          {{ isLoading ? 'Вход...' : 'Войти' }}
        </button>
      </form>

      <div class="hints">
        <p><strong>Администратор:</strong> sys_admin / SysAdmin2026</p>
        <p><strong>Специалист лабораторий:</strong> lab_sidorov / LabSidor2026</p>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '../shared/api'
import { getErrorMessage } from '../shared/http'
import { clearAuthState, setAuthToken, setStoredUser } from '../shared/auth'

const router = useRouter()
const username = ref('')
const password = ref('')
const isLoading = ref(false)
const error = ref('')

async function signIn() {
  try {
    isLoading.value = true
    error.value = ''
    clearAuthState()

    const token = btoa(`${username.value}:${password.value}`)
    setAuthToken(token)
    const currentUser = await authApi.me()
    setStoredUser(currentUser)

    await router.push({ name: 'tables' })
  } catch (err) {
    clearAuthState()
    error.value = getErrorMessage(err)
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: linear-gradient(180deg, #edf9ef 0%, #f8fffa 100%);
}

.login-card {
  width: min(520px, 100%);
  background: #ffffff;
  border: 1px solid #d4ecd7;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 10px 28px rgba(42, 111, 55, 0.12);
}

.login-card h1 {
  margin: 0;
  color: #111111;
}

.login-subtitle {
  margin: 8px 0 18px;
  color: #315a37;
}

.login-form {
  display: grid;
  gap: 12px;
}

.field {
  display: grid;
  gap: 6px;
}

.field span {
  font-weight: 600;
}

.field input {
  border: 1px solid #b7dbbf;
  border-radius: 8px;
  padding: 10px;
}

.hints {
  margin-top: 14px;
  border-top: 1px solid #d4ecd7;
  padding-top: 12px;
  color: #315a37;
  font-size: 14px;
}
</style>

<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">
        <h1>MedNet</h1>
        <p>Vue client</p>
      </div>

      <nav>
        <RouterLink
          v-for="item in menu"
          :key="item.to"
          :to="item.to"
          class="nav-link"
          :class="{ active: route.path === item.to }"
        >
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>

    <div class="main">
      <header class="header">
        <div>
          <strong>Frontend:</strong> :5174
        </div>
        <div>
          <strong>Backend:</strong> :8081 (proxy /api)
        </div>
      </header>

      <main class="content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink, RouterView, useRoute } from 'vue-router'

const route = useRoute()

const menu = [
  { label: 'Обзор', to: '/' },
  { label: 'Учреждения', to: '/institutions' },
  { label: 'Сотрудники', to: '/employees' },
  { label: 'Специальности', to: '/specialties' },
  { label: 'Пациенты', to: '/patients' },
  { label: 'Операции', to: '/operations' },
  { label: 'Отчёты', to: '/reports' },
]
</script>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: 250px 1fr;
  min-height: 100vh;
}

.sidebar {
  background: #111827;
  color: #e5e7eb;
  padding: 20px 14px;
}

.brand {
  margin-bottom: 18px;
  padding: 10px;
  border-bottom: 1px solid rgba(229, 231, 235, 0.2);
}

.brand h1 {
  margin: 0;
  font-size: 24px;
}

.brand p {
  margin: 4px 0 0;
  color: #9ca3af;
  font-size: 13px;
}

nav {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.nav-link {
  text-decoration: none;
  color: #d1d5db;
  border-radius: 8px;
  padding: 10px;
  transition: 0.2s;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.08);
}

.nav-link.active {
  background: #2563eb;
  color: #fff;
}

.main {
  display: flex;
  flex-direction: column;
}

.header {
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  padding: 12px 20px;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-size: 14px;
}

.content {
  padding: 20px;
}

@media (max-width: 980px) {
  .layout {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: sticky;
    top: 0;
    z-index: 5;
  }

  nav {
    flex-direction: row;
    flex-wrap: wrap;
  }
}
</style>

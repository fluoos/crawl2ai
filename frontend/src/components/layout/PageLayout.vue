<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">{{ title }}</h1>
      <p v-if="subtitle" class="page-subtitle">{{ subtitle }}</p>
      <slot name="header-actions"></slot>
    </div>
    
    <div class="page-content">
      <slot></slot>
    </div>
    
    <div v-if="$slots.footer" class="page-footer">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    default: ''
  }
});
</script>

<style scoped>
.page-container {
  margin-bottom: 24px;
}

.page-header {
  margin-bottom: 24px;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 500;
}

.page-subtitle {
  margin: 8px 0 0;
  color: rgba(0, 0, 0, 0.45);
}

.page-content {
  min-height: 300px;
}

.page-footer {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}
</style> 
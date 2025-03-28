<template>
  <div class="qa-item">
    <div class="qa-header">
      <div class="qa-id">#{{ source.id }}</div>
      <div class="qa-label">
        <a-tag color="blue" v-if="source.label">{{ source.label }}</a-tag>
        <a-tag color="default" v-else>未标记</a-tag>
      </div>
    </div>
    <div class="qa-content">
      <div class="qa-question">
        <div class="qa-title">问题：</div>
        <div class="qa-text">{{ source.question }}</div>
      </div>
      <div class="qa-answer">
        <div class="qa-title">答案：</div>
        <div class="qa-text">{{ source.answer }}</div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'QAListItem',
  props: {
    source: {
      type: Object,
      required: true
    }
  }
};
</script>

<style scoped>
.qa-item {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.qa-item:last-child {
  border-bottom: none;
}

.qa-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.qa-id {
  font-weight: bold;
  color: #888;
}

.qa-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.qa-question,
.qa-answer {
  display: flex;
}

.qa-title {
  font-weight: bold;
  flex: 0 0 50px;
}

.qa-text {
  flex: 1;
  white-space: pre-wrap;
  word-break: break-word;
}
</style> 
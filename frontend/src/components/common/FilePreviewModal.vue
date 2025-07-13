<template>
  <a-modal
    :visible="modelValue"
    title="文件预览"
    width="800px"
    :footer="null"
    @cancel="handleCancel"
  >
    <div class="file-preview">
      <pre v-if="content">{{ content }}</pre>
      <a-empty v-else description="文件内容为空" />
    </div>
  </a-modal>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue';

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  content: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['update:modelValue']);

const handleCancel = () => {
  emit('update:modelValue', false);
};
</script>

<style scoped>
.file-preview {
  max-height: 600px;
  overflow-y: auto;
}

.file-preview pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  padding: 12px;
  margin: 0;
  background: #f5f5f5;
  border-radius: 4px;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
}
</style> 
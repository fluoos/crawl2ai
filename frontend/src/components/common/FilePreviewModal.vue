<template>
  <a-modal
    :visible="modelValue"
    width="1024px"
    :footer="null"
    @cancel="handleCancel"
  >
    <template #title>
      <div style="display: flex; justify-content: space-between; align-items: center; width: 100%; padding-right: 40px">
        <span class="title-text">文件预览</span>
        <div v-if="isMarkdown" class="view-mode-switch">
          <a-button-group size="small">
            <a-button 
              :type="viewMode === 'preview' ? 'primary' : 'default'"
              @click="viewMode = 'preview'"
            >
              <template #icon><EyeOutlined /></template>
              预览
            </a-button>
            <a-button 
              :type="viewMode === 'source' ? 'primary' : 'default'"
              @click="viewMode = 'source'"
            >
              <template #icon><CodeOutlined /></template>
              源码
            </a-button>
          </a-button-group>
        </div>
      </div>
    </template>
    <div class="file-preview">
      <div v-if="content">
        <div v-if="isMarkdown && viewMode === 'preview'" class="markdown-body" v-html="sanitizedHtml"></div>
        <pre v-else>{{ content }}</pre>
      </div>
      <a-empty v-else description="文件内容为空" />
    </div>
  </a-modal>
</template>

<script setup>
import { defineProps, defineEmits, ref, computed } from 'vue';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { EyeOutlined, CodeOutlined } from '@ant-design/icons-vue';

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  content: {
    type: String,
    default: ''
  },
  fileName: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['update:modelValue']);
const viewMode = ref('source'); // 修改默认值为 'source'

const isMarkdown = computed(() => {
  if (!props.fileName) return false;
  const lowerFileName = props.fileName.toLowerCase();
  return lowerFileName.endsWith('.md') || lowerFileName.endsWith('.markdown');
});

const sanitizedHtml = computed(() => {
  if (!props.content) return '';
  const rawHtml = marked.parse(props.content);
  return DOMPurify.sanitize(rawHtml);
});

const handleCancel = () => {
  emit('update:modelValue', false);
};
</script>

<style scoped>
.title-text {
  font-size: 16px;
  color: rgba(0, 0, 0, 0.85);
}

.view-mode-switch {
  display: flex;
  align-items: center;
}

.file-preview {
  max-height: 600px;
  overflow-y: auto;
  padding: 0 24px;
}

.file-preview pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  padding: 16px;
  margin: 0;
  background: #f6f8fa;
  border-radius: 6px;
  font-family: ui-monospace,SFMono-Regular,SF Mono,Menlo,Consolas,Liberation Mono,monospace;
  font-size: 13px;
  line-height: 1.5;
}

/* GitHub Markdown 样式 */
.markdown-body {
  color: #24292f;
  font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif,"Apple Color Emoji","Segoe UI Emoji";
  font-size: 16px;
  line-height: 1.5;
  word-wrap: break-word;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2) {
  padding-bottom: .3em;
  border-bottom: 1px solid #d0d7de;
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
}

.markdown-body :deep(h1) {
  font-size: 2em;
}

.markdown-body :deep(h2) {
  font-size: 1.5em;
}

.markdown-body :deep(h3),
.markdown-body :deep(h4),
.markdown-body :deep(h5),
.markdown-body :deep(h6) {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
}

.markdown-body :deep(h3) { font-size: 1.25em; }
.markdown-body :deep(h4) { font-size: 1em; }
.markdown-body :deep(h5) { font-size: 0.875em; }
.markdown-body :deep(h6) { font-size: 0.85em; }

.markdown-body :deep(p),
.markdown-body :deep(blockquote),
.markdown-body :deep(ul),
.markdown-body :deep(ol),
.markdown-body :deep(dl),
.markdown-body :deep(table),
.markdown-body :deep(pre) {
  margin-top: 0;
  margin-bottom: 16px;
}

.markdown-body :deep(blockquote) {
  padding: 0 1em;
  color: #57606a;
  border-left: .25em solid #d0d7de;
  margin: 1em 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 2em;
}

.markdown-body :deep(code) {
  padding: .2em .4em;
  margin: 0;
  font-size: 85%;
  background-color: rgba(175,184,193,0.2);
  border-radius: 6px;
  font-family: ui-monospace,SFMono-Regular,SF Mono,Menlo,Consolas,Liberation Mono,monospace;
}

.markdown-body :deep(pre) {
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  background-color: #f6f8fa;
  border-radius: 6px;
}

.markdown-body :deep(pre code) {
  padding: 0;
  margin: 0;
  font-size: 100%;
  word-break: normal;
  white-space: pre;
  background: transparent;
  border: 0;
}

.markdown-body :deep(table) {
  display: block;
  width: 100%;
  width: max-content;
  max-width: 100%;
  overflow: auto;
  border-spacing: 0;
  border-collapse: collapse;
}

.markdown-body :deep(table th),
.markdown-body :deep(table td) {
  padding: 6px 13px;
  border: 1px solid #d0d7de;
}

.markdown-body :deep(table th) {
  font-weight: 600;
  background-color: #f6f8fa;
}

.markdown-body :deep(table tr) {
  background-color: #ffffff;
  border-top: 1px solid #d0d7de;
}

.markdown-body :deep(table tr:nth-child(2n)) {
  background-color: #f6f8fa;
}

.markdown-body :deep(img) {
  max-width: 100%;
  box-sizing: content-box;
  background-color: #ffffff;
}

.markdown-body :deep(hr) {
  height: .25em;
  padding: 0;
  margin: 24px 0;
  background-color: #d0d7de;
  border: 0;
}

.markdown-body :deep(a) {
  color: #0969da;
  text-decoration: none;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}
</style> 
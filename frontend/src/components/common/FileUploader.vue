<template>
  <div class="file-uploader">
    <a-upload-dragger
      :multiple="true"
      :file-list="fileList"
      :before-upload="beforeUpload"
      @change="handleChange"
      :accept="accept"
    >
      <p class="ant-upload-drag-icon">
        <InboxOutlined />
      </p>
      <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
      <p class="ant-upload-hint">支持单个或批量上传，仅支持 .md 文件</p>
    </a-upload-dragger>
    
    <div class="upload-actions" v-if="fileList.length > 0">
      <a-button 
        type="primary" 
        :disabled="uploading" 
        :loading="uploading" 
        @click="handleUpload"
        style="margin-top: 16px"
      >
        {{ uploading ? '上传中...' : '开始上传' }}
      </a-button>
      <a-button 
        style="margin-left: 10px; margin-top: 16px" 
        @click="clearFiles"
        :disabled="uploading"
      >
        清空
      </a-button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { message } from 'ant-design-vue';
import { InboxOutlined } from '@ant-design/icons-vue';
import { uploadFile } from '../../services/api';

const props = defineProps({
  accept: {
    type: String,
    default: '.md'
  }
});

const emit = defineEmits(['upload-success']);

const fileList = ref([]);
const uploading = ref(false);

const beforeUpload = (file) => {
  // 验证文件类型
  const isAccepted = props.accept.split(',').some(ext => 
    file.name.toLowerCase().endsWith(ext.trim())
  );
  
  if (!isAccepted) {
    message.error(`只能上传${props.accept}格式的文件!`);
    return false;
  }
  
  // 验证文件大小 (限制为10MB)
  const isLt10M = file.size / 1024 / 1024 < 10;
  if (!isLt10M) {
    message.error('文件必须小于10MB!');
    return false;
  }
  
  return false; // 手动上传
};

const handleChange = (info) => {
  let newFileList = [...info.fileList];
  
  // 限制最多上传10个文件
  newFileList = newFileList.slice(-10);
  
  fileList.value = newFileList;
};

const handleUpload = async () => {
  if (fileList.value.length === 0) {
    message.warning('请先选择文件');
    return;
  }
  
  uploading.value = true;
  const formData = new FormData();
  
  fileList.value.forEach(file => {
    formData.append('files[]', file.originFileObj);
  });
  
  try {
    const result = await uploadFile(formData);
    message.success('上传成功');
    fileList.value = [];
    emit('upload-success', result);
  } catch (error) {
    console.error('上传失败:', error);
    message.error('上传失败');
  } finally {
    uploading.value = false;
  }
};

const clearFiles = () => {
  fileList.value = [];
};
</script>

<style scoped>
.file-uploader {
  margin-bottom: 24px;
}
</style> 
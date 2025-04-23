<template>
  <a-modal
    :visible="visible"
    title="编辑问答对"
    :confirm-loading="loading"
    @ok="handleOk"
    @cancel="handleCancel"
    width="700px"
  >
    <a-form :model="formState" :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }">
      <a-form-item
        label="问题"
        name="question"
        :rules="[{ required: true, message: '请输入问题' }]"
      >
        <a-textarea
          v-model:value="formState.question"
          placeholder="请输入问题内容"
          :auto-size="{ minRows: 3, maxRows: 6 }"
        />
      </a-form-item>

      <a-form-item label="答案" name="answer" :rules="[{ required: true, message: '请输入答案' }]">
        <a-textarea
          v-model:value="formState.answer"
          placeholder="请输入答案内容"
          :auto-size="{ minRows: 4, maxRows: 8 }"
        />
      </a-form-item>

      <a-form-item label="思维链" name="chainOfThought">
        <a-textarea
          v-model:value="formState.chainOfThought"
          placeholder="请输入思维链内容（可选）"
          :auto-size="{ minRows: 3, maxRows: 6 }"
        />
      </a-form-item>

      <a-form-item label="领域标签" name="label">
        <a-input
          v-model:value="formState.label"
          placeholder="请输入领域标签"
          allow-clear
        ></a-input>
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup>
import { ref, reactive, watch } from 'vue';
import { message } from 'ant-design-vue';
import { updateQAItem } from '../../services/dataset';

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  itemData: {
    type: Object,
    default: () => ({}),
  }
});

const emit = defineEmits(['update:visible', 'edit-success']);

const formState = reactive({
  id: null,
  question: '',
  answer: '',
  chainOfThought: '',
  label: '',
});

const loading = ref(false);

// 监听itemData变化，更新表单
watch(() => props.itemData, (newVal) => {
  if (newVal && newVal.id) {
    formState.id = newVal.id;
    formState.question = newVal.question || '';
    formState.answer = newVal.answer || '';
    formState.chainOfThought = newVal.chainOfThought || '';
    formState.label = newVal.label || '';
  }
}, { immediate: true, deep: true });

const handleOk = async () => {
  if (!formState.question || !formState.answer) {
    message.error('请填写必填项');
    return;
  }

  loading.value = true;
  try {
    const qaData = {
      id: formState.id,
      question: formState.question,
      answer: formState.answer,
      chainOfThought: formState.chainOfThought,
      label: formState.label,
    }
    // 调用API添加数据
    const response = await updateQAItem(qaData);

    if (response && response.status === 'success') {
      message.success('编辑成功');
      emit('edit-success');
      emit('update:visible', false);
    } else {
      message.error(response?.data?.message || '编辑失败');
    }
  } catch (error) {
    console.error('编辑数据失败:', error);
    message.error('编辑失败: ' + (error.response?.data?.detail || error.message));
  } finally {
    loading.value = false;
  }
};

const handleCancel = () => {
  emit('update:visible', false);
};
</script>

<style scoped>
.ant-form-item {
  margin-bottom: 16px;
}
</style> 
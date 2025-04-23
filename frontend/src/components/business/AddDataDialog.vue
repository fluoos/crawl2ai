<template>
  <a-modal
    :visible="visible"
    title="新增数据"
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
import { ref, reactive } from 'vue';
import { message } from 'ant-design-vue';
import { addQAItem } from '../../services/dataset';

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['update:visible', 'add-success']);

// 常用领域标签，可以根据实际情况修改
const domainOptions = [
  { value: '通用', label: '通用' },
  { value: '科技', label: '科技' },
  { value: '教育', label: '教育' },
  { value: '金融', label: '金融' },
  { value: '医疗', label: '医疗' },
  { value: '法律', label: '法律' },
];

const formState = reactive({
  question: '',
  answer: '',
  chainOfThought: '',
  label: '',
});

const loading = ref(false);

const resetForm = () => {
  formState.question = '';
  formState.answer = '';
  formState.chainOfThought = '';
  formState.label = '';
};

const handleOk = async () => {
  if (!formState.question || !formState.answer) {
    message.error('请填写必填项');
    return;
  }

  loading.value = true;
  try {
    // 组装数据格式
    const qaData = {
      question: formState.question,
      answer: formState.answer,
      chainOfThought: formState.chainOfThought,
      label: Array.isArray(formState.label) ? formState.label[0] : formState.label,
    };

    // 调用API添加数据
    const response = await addQAItem(qaData);

    if (response && response.status === 'success') {
      message.success('添加成功');
      resetForm();
      emit('add-success');
      emit('update:visible', false);
    } else {
      message.error(response?.message || '添加失败');
    }
  } catch (error) {
    console.error('添加数据失败:', error);
    message.error('添加失败: ' + (error.message || '未知错误'));
  } finally {
    loading.value = false;
  }
};

const handleCancel = () => {
  resetForm();
  emit('update:visible', false);
};
</script>

<style scoped>
.ant-form-item {
  margin-bottom: 16px;
}
</style>

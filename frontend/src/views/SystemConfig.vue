<template>
  <div class="system-config">
    <a-page-header title="系统配置" subtitle="配置模型API、提示词和文件处理策略" />
    
    <a-card class="card-wrapper">
      <a-tabs v-model:activeKey="activeTabKey" @change="loadTabData">
        <!-- 模型配置 Tab -->
        <a-tab-pane key="models" tab="模型配置">
          <div class="tab-content">
            <div class="table-operations">
              <a-button type="primary" @click="showModelModal()">
                <plus-outlined /> 添加模型
              </a-button>
            </div>
            
            <a-table
              :columns="modelColumns"
              :data-source="modelList"
              :pagination="false"
              :loading="modelsLoading"
              rowKey="id"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'action'">
                  <a-space>
                    <a-button type="link" size="small" @click="editModel(record)">
                      编辑
                    </a-button>
                    <a-button 
                      type="link" 
                      danger 
                      size="small" 
                      @click="confirmDeleteModel(record)"
                    >
                      删除
                    </a-button>
                  </a-space>
                </template>
                <template v-else-if="column.key === 'isDefault'">
                  <a-tag color="green" v-if="record.isDefault">默认使用</a-tag>
                  <a 
                    type="link" 
                    size="small" 
                    v-else 
                    @click="setAsDefault(record)"
                  >
                    设为默认使用
                  </a>
                </template>
                <template v-else-if="column.key === 'apiKey'">
                  <span>{{ record.apiKey ? record.apiKey.slice(0, 4) + '******' + record.apiKey.slice(-4) : '未设置' }}</span>
                </template>
              </template>
            </a-table>
          </div>
        </a-tab-pane>
        
        <!-- 提示词配置 Tab -->
        <a-tab-pane key="prompts" tab="提示词配置">
          <div class="tab-content">
            <a-spin :spinning="promptsLoading">
              <a-form
                :model="promptsForm"
                :label-col="{ span: 4 }"
                :wrapper-col="{ span: 18 }"
                @finish="savePrompts"
              >
                <a-form-item 
                  label="文件转换提示词" 
                  name="fileConversion"
                >
                  <a-textarea
                    v-model:value="promptsForm.data"
                    :rows="6"
                    placeholder="输入文件转换提示词"
                  />
                  <div class="form-item-help">用于指导大模型如何将文本文件转换为问答对</div>
                </a-form-item>
                
                <a-form-item :wrapper-col="{ offset: 4 }">
                  <a-button type="primary" html-type="submit" :loading="promptsSubmitLoading">
                    保存提示词
                  </a-button>
                  <a-button style="margin-left: 10px" @click="handleResetPrompts">
                    重置
                  </a-button>
                </a-form-item>
              </a-form>
            </a-spin>
          </div>
        </a-tab-pane>
        
        <!-- 文件策略配置 Tab -->
        <a-tab-pane key="fileStrategy" tab="文件策略配置">
          <div class="tab-content">
            <a-spin :spinning="strategyLoading">
              <a-form
                :model="strategyForm"
                :label-col="{ span: 6 }"
                :wrapper-col="{ span: 12 }"
                @finish="saveStrategy"
              >
                <a-form-item 
                  label="段落分割大小(字符数)" 
                  name="chunkSize"
                >
                  <a-input-number
                    v-model:value="strategyForm.chunkSize"
                    :min="500"
                    :max="10000"
                    :step="100"
                    style="width: 150px"
                  />
                  <div class="form-item-help">将Markdown文件按多少字符分割为一个段落</div>
                </a-form-item>
                
                <a-form-item 
                  label="段落重叠大小(字符数)" 
                  name="overlapSize"
                >
                  <a-input-number
                    v-model:value="strategyForm.overlapSize"
                    :min="0"
                    :max="1000"
                    :step="50"
                    style="width: 150px"
                  />
                  <div class="form-item-help">相邻段落之间的重叠字符数，有助于保持上下文连贯性</div>
                </a-form-item>
                
                <a-form-item 
                  label="保留Markdown格式" 
                  name="preserveMarkdown"
                >
                  <a-switch v-model:checked="strategyForm.preserveMarkdown" />
                  <div class="form-item-help">开启后，分割时会尽量保持Markdown格式结构的完整性</div>
                </a-form-item>
                
                <a-form-item 
                  label="智能分段" 
                  name="smartChunking"
                >
                  <a-switch v-model:checked="strategyForm.smartChunking" />
                  <div class="form-item-help">开启后，系统会尝试根据段落内容的语义边界进行分割</div>
                </a-form-item>
                
                <a-form-item :wrapper-col="{ offset: 6 }">
                  <a-button type="primary" html-type="submit" :loading="strategySubmitLoading">
                    保存策略配置
                  </a-button>
                  <a-button style="margin-left: 10px" @click="handleResetStrategy">
                    重置
                  </a-button>
                </a-form-item>
              </a-form>
            </a-spin>
          </div>
        </a-tab-pane>
      </a-tabs>
    </a-card>
    
    <!-- 模型编辑对话框 -->
    <a-modal
      v-model:visible="modelModalVisible"
      :title="modelFormMode === 'add' ? '添加模型' : '编辑模型'"
      @ok="submitModelForm"
      :confirm-loading="modelSubmitLoading"
    >
      <a-form
        :model="modelForm"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 16 }"
      >
        <a-form-item 
          label="模型提供商" 
          name="name"
          :rules="[{ required: true, message: '请输入模型提供商' }]"
        >
          <a-input v-model:value="modelForm.name" placeholder="请输入模型提供商，如 DeepSeek" />
        </a-form-item>
        <a-form-item 
          label="模型名称" 
          name="model"
          :rules="[{ required: true, message: '请输入模型名称' }]"
        >
          <a-input v-model:value="modelForm.model" placeholder="请输入模型名称，如 deepseek-chat" />
        </a-form-item>
        
        <a-form-item 
          label="API端点" 
          name="apiEndpoint"
          :rules="[{ required: true, message: '请输入API端点' }]"
        >
          <a-input v-model:value="modelForm.apiEndpoint" autocomplete="off" placeholder="请输入API端点URL" />
        </a-form-item>
        
        <a-form-item 
          label="API密钥" 
          name="apiKey"
          :rules="[{ required: true, message: '请输入API密钥' }]"
        >
          <a-input-password v-model:value="modelForm.apiKey" autocomplete="new-password" placeholder="请输入API密钥" />
        </a-form-item>
        
        <a-form-item 
          label="模型类型" 
          name="type"
        >
          <a-select v-model:value="modelForm.type" placeholder="请选择模型类型">
            <a-select-option value="chat">对话模型</a-select-option>
            <a-select-option value="embedding">嵌入模型</a-select-option>
            <a-select-option value="completion">补全模型</a-select-option>
          </a-select>
        </a-form-item>
        
        <a-form-item 
          label="温度" 
          name="temperature"
        >
          <a-slider
            v-model:value="modelForm.temperature"
            :min="0"
            :max="1"
            :step="0.1"
            :tooltip-visible="true"
          />
        </a-form-item>
        
        <a-form-item 
          label="最大token数" 
          name="maxTokens"
        >
          <a-input-number
            v-model:value="modelForm.maxTokens"
            :min="100"
            :max="8000"
            :step="100"
            style="width: 150px"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { message, Modal } from 'ant-design-vue';
import { PlusOutlined } from '@ant-design/icons-vue';
import {
  getModelList,
  addModel,
  updateModel,
  deleteModel,
  setDefaultModel,
  getPrompts,
  updatePrompts,
  resetPrompts,
  getFileStrategy,
  updateFileStrategy,
  resetFileStrategy
} from '../services/system';

// 当前活动标签
const activeTabKey = ref('models');

// 模型列表状态
const modelList = ref([]);
const modelsLoading = ref(false);
const modelColumns = [
  {
    title: '模型提供商',
    dataIndex: 'name',
    key: 'name',
    width: 120,
  },
  {
    title: '模型名称',
    dataIndex: 'model',
    key: 'model',
    width: 160,
  },
  {
    title: '模型类型',
    dataIndex: 'type',
    key: 'type',
    width: 100,
  },
  {
    title: '默认模型',
    dataIndex: 'isDefault',
    key: 'isDefault',
    width: 120,
  },
  {
    title: 'API端点',
    dataIndex: 'apiEndpoint',
    key: 'apiEndpoint',
    ellipsis: true,
  },
  {
    title: 'ApiKey',
    dataIndex: 'apiKey',
    key: 'apiKey',
    ellipsis: true,
  },
  {
    title: '操作',
    key: 'action',
    width: 160,
  },
];

// 模型表单
const modelModalVisible = ref(false);
const modelSubmitLoading = ref(false);
const modelFormMode = ref('add'); // 'add' or 'edit'
const selectedProvider = ref(null);
const modelForm = reactive({
  id: null,
  name: '',
  model: '', 
  apiEndpoint: '',
  apiKey: '',
  type: 'chat',
  temperature: 0.7,
  maxTokens: 4000,
  isDefault: false,
});

// 提示词配置表单
const promptsLoading = ref(false);
const promptsSubmitLoading = ref(false);
const promptsForm = reactive({
  data: '',
});

// 文件策略表单
const strategyLoading = ref(false);
const strategySubmitLoading = ref(false);
const strategyForm = reactive({
  chunkSize: 2000,
  overlapSize: 200,
  preserveMarkdown: true,
  smartChunking: true
});

// 初始化
onMounted(async () => {
  // 按照当前激活的标签页加载数据
  loadTabData();
});

// 切换标签页时加载相应数据
const loadTabData = () => {
  const key = activeTabKey.value;
  if (key === 'models') {
    fetchModels();
  } else if (key === 'prompts') {
    fetchPrompts();
  } else if (key === 'fileStrategy') {
    fetchStrategy();
  }
};

// 获取模型列表
const fetchModels = async () => {
  modelsLoading.value = true;
  try {
    const response = await getModelList();
    if (response && response.data) {
      modelList.value = response.data || [];
    }
  } catch (error) {
    message.error('获取模型配置失败');
  } finally {
    modelsLoading.value = false;
  }
};

// 获取提示词配置
const fetchPrompts = async () => {
  promptsLoading.value = true;
  try {
    const response = await getPrompts();
    if (response && response.data) {
      promptsForm.data = response.data || '';
    }
  } catch (error) {
    message.error('获取提示词配置失败');
  } finally {
    promptsLoading.value = false;
  }
};

// 获取文件策略配置
const fetchStrategy = async () => {
  strategyLoading.value = true;
  try {
    const response = await getFileStrategy();
    if (response && response.data) {
      const data = response.data
      strategyForm.chunkSize = data.chunkSize || 2000;
      strategyForm.overlapSize = data.overlapSize || 200;
      strategyForm.preserveMarkdown = data.preserveMarkdown !== false;
      strategyForm.smartChunking = data.smartChunking !== false;
    }
  } catch (error) {
    message.error('获取文件策略配置失败');
  } finally {
    strategyLoading.value = false;
  }
};

// 显示模型表单对话框
const showModelModal = (record = null) => {
  if (record) {
    // 编辑模式
    modelFormMode.value = 'edit';
    // 复制记录到表单
    Object.assign(modelForm, record);
  } else {
    // 添加模式
    modelFormMode.value = 'add';
    // 重置表单
    modelForm.id = null;
    modelForm.name = '';
    modelForm.apiEndpoint = '';
    modelForm.apiKey = '';
    modelForm.type = 'chat';
    modelForm.temperature = 0.7;
    modelForm.maxTokens = 4000;
    modelForm.isDefault = false;
    selectedProvider.value = null;
  }
  
  modelModalVisible.value = true;
};

// 编辑模型
const editModel = (record) => {
  showModelModal(record);
};

// 提交模型表单
const submitModelForm = async () => {
  // 简单验证
  if (!modelForm.name || !modelForm.apiEndpoint || !modelForm.apiKey || !modelForm.model) {
    message.error('请填写必填字段');
    return;
  }
  
  modelSubmitLoading.value = true;
  try {
    if (modelFormMode.value === 'add') {
      // 发送添加成功
      const response = await addModel(modelForm);
      
      if (response && response.status === 'success') {
        message.success(response.message || '添加模型成功');
      } else {
        message.error('添加模型失败');
      }
    } else {
      const response = await updateModel(modelForm);
      
      if (response && response.status === 'success') {
        message.success(response.message || '更新模型成功');
      } else {
        message.error('更新模型失败');
      }
    }
    loadTabData();
    // 关闭对话框并刷新列表
    modelModalVisible.value = false;
  } catch (error) {
    console.error('保存模型失败:', error);
    message.error('保存模型失败');
  } finally {
    modelSubmitLoading.value = false;
  }
};

// 确认删除模型
const confirmDeleteModel = (record) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除模型 "${record.name}" 吗？`,
    okText: '确认',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        const response = await deleteModel(record.id);
        if (response && response.status === 'success') {
          message.success(response.message || '删除模型成功');
        } else {
          message.error('删除模型失败');
        }
        loadTabData();
      } catch (error) {
        message.error('删除模型失败');
      }
    }
  });
};

// 设置为默认模型
const setAsDefault = async (record) => {
  try {
    const response = await setDefaultModel(record.id);
    if (response && response.status === 'success') {
      message.success(response.message || '设置默认成功');
    } else {
      message.error('设置默认失败');
    }
    loadTabData();
  } catch (error) {
    message.error('设置默认失败');
  }
};

// 保存提示词配置
const savePrompts = async () => {
  promptsSubmitLoading.value = true;
  try {
    const response = await updatePrompts(promptsForm);
    if (response && response.status === 'success') {
      message.success(response.message || '提示词配置保存成功');
    } else {
      message.error('设置默认失败');
    }
    loadTabData();
  } catch (error) {
    message.error('保存提示词配置失败');
  } finally {
    promptsSubmitLoading.value = false;
  }
};

// 重置提示词配置
const handleResetPrompts = async () => {
  promptsSubmitLoading.value = true;
  try {
    const response = await resetPrompts();
    if (response && response.status === 'success') {
      message.success(response.message || '提示词配置重置成功');
    } else {
      message.error('设置默认失败');
    }
    loadTabData();
  } catch (error) {
    message.error('重置提示词配置失败');
  } finally {
    promptsSubmitLoading.value = false;
  }
};

// 保存文件策略配置
const saveStrategy = async () => {
  strategySubmitLoading.value = true;
  try {
    const response = await updateFileStrategy(strategyForm);
    if (response && response.status === 'success') {
      message.success(response.message || '文件策略配置保存成功');
    } else {
      message.error('保存文件策略配置失败');
    }
    loadTabData();
  } catch (error) {
    message.error('保存文件策略配置失败');
  } finally {
    strategySubmitLoading.value = false;
  }
};

// 重置文件策略配置
const handleResetStrategy = async () => {
  strategySubmitLoading.value = true;
  try {
    const response = await resetFileStrategy();
    if (response && response.status === 'success') {
      message.success(response.message || '文件策略重置成功');
    } else {
      message.error('文件策略重置失败');
    }
    loadTabData();
  } catch (error) {
    message.error('文件策略重置失败');
  } finally {
    strategySubmitLoading.value = false;
  }
};
</script>

<style scoped>
.system-config {
  max-width: 1200px;
  margin: 0 auto;
}

.card-wrapper {
  margin-bottom: 24px;
}

.tab-content {
  padding: 16px 0;
}

.table-operations {
  margin-bottom: 16px;
}

.form-item-help {
  color: rgba(0, 0, 0, 0.45);
  font-size: 14px;
  margin-top: 4px;
}
</style> 
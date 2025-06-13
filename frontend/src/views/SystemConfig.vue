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
              <div class="strategy-config-container">
                <!-- 配置说明 -->
                <div class="config-description">
                  <a-alert
                    message="智能分段配置"
                    description="智能分段功能会根据内容语义自动分割Markdown文件，适用于RAG检索和大模型训练微调场景。配置将应用于所有文件处理操作。"
                    type="info"
                    show-icon
                    :style="{ marginBottom: '24px' }"
                  />
                </div>

                <a-form
                  :model="strategyForm"
                  layout="vertical"
                  @finish="saveStrategy"
                  class="strategy-form"
                >
                  <!-- 智能分段开关 -->
                  <div class="config-section">
                    <div class="section-title">
                      <span class="title-text">智能分段设置</span>
                    </div>
                    <a-form-item 
                      name="enableSmartSplit"
                      class="switch-item"
                    >
                      <div class="switch-container">
                        <a-switch 
                          v-model:checked="strategyForm.enableSmartSplit" 
                          checked-children="开启"
                          un-checked-children="关闭"
                          size="default"
                        />
                        <div class="switch-content">
                          <span class="switch-label">启用智能分段</span>
                          <div class="switch-desc">开启后，系统将使用智能算法对Markdown文件进行语义化分段</div>
                        </div>
                      </div>
                    </a-form-item>
                  </div>
                  
                  <!-- 智能分段详细配置 -->
                  <template v-if="strategyForm.enableSmartSplit">
                    <div class="config-section smart-config-section">
                      <div class="section-title">
                        <span class="title-text">分段参数配置</span>
                      </div>
                      
                      <a-form-item 
                        label="最大Token数" 
                        name="maxTokens"
                        class="config-item"
                      >
                        <a-input-number 
                          v-model:value="strategyForm.maxTokens"
                          :min="500"
                          :max="20000"
                          :step="100"
                          size="large"
                          placeholder="8000"
                          class="number-input"
                          :formatter="value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')"
                          :parser="value => value.replace(/\$\s?|(,*)/g, '')"
                        />
                        <div class="form-item-help">
                          设置每个分段的最大Token数量，建议范围：2000-10000
                        </div>
                      </a-form-item>
                      
                      <a-form-item 
                        label="最小Token数" 
                        name="minTokens"
                        class="config-item"
                      >
                        <a-input-number 
                          v-model:value="strategyForm.minTokens"
                          :min="100"
                          :max="2000"
                          :step="50"
                          size="large"
                          placeholder="300"
                          class="number-input"
                          :formatter="value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')"
                          :parser="value => value.replace(/\$\s?|(,*)/g, '')"
                        />
                        <div class="form-item-help">
                          设置每个分段的最小Token数量，避免分段过小影响语义完整性
                        </div>
                      </a-form-item>
                      
                      <a-form-item 
                        label="分段策略" 
                        name="splitStrategy"
                        class="config-item"
                      >
                        <a-select 
                          v-model:value="strategyForm.splitStrategy"
                          placeholder="选择分段策略"
                          size="large"
                          class="strategy-select"
                        >
                          <a-select-option value="conservative">🛡️ 保守策略 - 较少分段，保持内容完整性</a-select-option>
                          <a-select-option value="balanced">⚖️ 平衡策略 - 兼顾完整性和检索效果（推荐）</a-select-option>
                          <a-select-option value="aggressive">🎯 积极策略 - 更多分段，适合精细检索</a-select-option>
                        </a-select>
                        <div class="form-item-help">
                          选择合适的分段策略以平衡内容完整性和搜索效果，建议使用平衡策略
                        </div>
                      </a-form-item>
                    </div>
                  </template>

                  <!-- 操作按钮 -->
                  <div class="form-actions">
                    <a-button 
                      type="primary" 
                      html-type="submit" 
                      :loading="strategySubmitLoading"
                      size="large"
                      class="save-btn"
                    >
                      保存配置
                    </a-button>
                    <a-button 
                      @click="handleResetStrategy"
                      size="large"
                      class="reset-btn"
                    >
                      重置为默认
                    </a-button>
                  </div>
                </a-form>
              </div>
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
import { PlusOutlined, SaveOutlined, ReloadOutlined } from '@ant-design/icons-vue';
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
  // 智能分段配置
  enableSmartSplit: true,
  maxTokens: 8000,
  minTokens: 300,
  splitStrategy: 'balanced'
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
      const data = response.data;
      // 智能分段配置
      strategyForm.enableSmartSplit = data.enableSmartSplit !== false;
      strategyForm.maxTokens = data.maxTokens || 8000;
      strategyForm.minTokens = data.minTokens || 300;
      strategyForm.splitStrategy = data.splitStrategy || 'balanced';
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

/* 文件策略配置容器 */
.strategy-config-container {
  max-width: 800px;
  margin: 0 auto;
}

/* 配置说明 */
.config-description {
  margin-bottom: 20px;
}

/* 策略表单 */
.strategy-form {
  padding: 0;
}

/* 配置区块 */
.config-section {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  border: 1px solid #f0f0f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
  transition: all 0.3s ease;
}

.config-section:hover {
  border-color: #d9d9d9;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

/* 区块标题 */
.section-title {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 10px;
  border-bottom: 2px solid #f0f2f5;
}

.title-icon {
  font-size: 20px;
  margin-right: 12px;
}

.title-text {
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}

/* 开关容器 */
.switch-container {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.switch-content {
  flex: 1;
}

.switch-label {
  font-size: 16px;
  font-weight: 500;
  color: #262626;
  display: block;
  margin-bottom: 4px;
}

.switch-desc {
  font-size: 14px;
  color: #8c8c8c;
  line-height: 1.5;
}

.switch-item {
  margin-bottom: 0 !important;
}

/* 智能分段配置区块 */
.smart-config-section {
  background: linear-gradient(135deg, #f8fbff 0%, #f0f8ff 100%);
  border: 1px solid #e6f3ff;
}

.smart-config-section:hover {
  border-color: #91caff;
}

/* 配置项 */
.config-item {
  margin-bottom: 20px !important;
}

.config-item .ant-form-item-label > label {
  font-size: 15px;
  font-weight: 500;
  color: #262626;
}

/* 数字输入框 */
.number-input {
  width: 100% !important;
  border-radius: 8px;
}

.number-input .ant-input-number-input {
  font-size: 16px;
  font-weight: 500;
}

/* 策略选择框 */
.strategy-select {
  width: 100%;
  border-radius: 8px;
}

.strategy-select .ant-select-selector {
  border-radius: 8px !important;
  height: 44px !important;
  padding: 0 12px !important;
  display: flex !important;
  align-items: center !important;
}

.strategy-select .ant-select-selection-search {
  display: flex !important;
  align-items: center !important;
}

.strategy-select .ant-select-selection-search-input {
  height: 44px !important;
  line-height: 44px !important;
}

.strategy-select .ant-select-selection-item {
  display: flex !important;
  align-items: center !important;
  height: 44px !important;
  line-height: 44px !important;
  font-size: 16px !important;
  font-weight: 500 !important;
}

.strategy-select .ant-select-selection-placeholder {
  display: flex !important;
  align-items: center !important;
  height: 44px !important;
  line-height: 44px !important;
  font-size: 16px !important;
}

/* 下拉选项样式 */
.strategy-select .ant-select-item-option {
  padding: 12px 16px !important;
  font-size: 14px !important;
  line-height: 1.5 !important;
}

.strategy-select .ant-select-item-option-selected {
  background-color: #e6f3ff !important;
  font-weight: 500 !important;
}

/* 帮助文本 */
.form-item-help {
  display: flex;
  align-items: flex-start;
  margin-top: 8px;
  padding: 8px 12px;
  background: #fafafa;
  border-radius: 6px;
  color: #666;
  font-size: 13px;
  line-height: 1.5;
}

.help-icon {
  margin-right: 6px;
  flex-shrink: 0;
}

/* 操作按钮 */
.form-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 24px 0 12px;
  margin-top: 20px;
}

.save-btn {
  min-width: 140px;
  height: 44px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 500;
  box-shadow: 0 2px 4px rgba(24, 144, 255, 0.2);
}

.save-btn:hover {
  box-shadow: 0 4px 8px rgba(24, 144, 255, 0.3);
  transform: translateY(-1px);
}

.reset-btn {
  min-width: 140px;
  height: 44px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.reset-btn:hover {
  border-color: #faad14;
  color: #faad14;
  transform: translateY(-1px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .strategy-config-container {
    max-width: 100%;
    padding: 0 16px;
  }
  
  .config-section {
    padding: 16px;
    margin-bottom: 16px;
  }
  
  .switch-container {
    flex-direction: column;
    gap: 12px;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .save-btn,
  .reset-btn {
    width: 100%;
  }
}
</style> 
<template>
  <div class="dataset-manager">
    <a-page-header title="数据集管理" subtitle="管理和导出训练数据集" />
    
    <a-row :gutter="24" class="stats-row">
      <a-col :span="8">
        <a-card>
          <template #title>
            <span><DatabaseOutlined /> 数据总量</span>
          </template>
          <a-statistic 
            :value="stats.totalCount" 
            :loading="statsLoading"
            :precision="0"
          />
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card>
          <template #title>
            <span><CheckCircleOutlined /> 有效数据量</span>
          </template>
          <a-statistic 
            :value="stats.validCount" 
            :loading="statsLoading"
            :precision="0"
          />
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card>
          <template #title>
            <span><BarChartOutlined /> 平均数据长度</span>
          </template>
          <a-statistic 
            :value="stats.avgLength" 
            :loading="statsLoading"
            :precision="2"
            suffix="字符"
          />
        </a-card>
      </a-col>
    </a-row>
    
    <a-card title="数据集问答对" class="card-wrapper">
      <template #extra>
        <a-space>
          <a-button @click="fetchQAList">
            <ReloadOutlined /> 刷新列表
          </a-button>
          <a-button 
            type="danger" 
            :disabled="selectedRowKeys.length === 0"
            @click="confirmBatchDelete"
          >
            <DeleteOutlined /> 批量删除
          </a-button>
          <a-button type="primary" @click="showExportDialog">
            <ExportOutlined /> 导出数据集
          </a-button>
        </a-space>
      </template>
      
      <!-- 使用Ant Design表格替代虚拟滚动列表 -->
      <a-table
        :columns="columns"
        :data-source="qaList"
        :pagination="pagination"
        :loading="tableLoading"
        :row-selection="{ selectedRowKeys, onChange: onSelectChange }"
        row-key="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, text, record }">
          <template v-if="column.dataIndex === 'question'">
            <div class="qa-text">{{ text }}</div>
          </template>
          <template v-else-if="column.dataIndex === 'answer'">
            <div class="qa-text">{{ text }}</div>
          </template>
          <template v-else-if="column.dataIndex === 'label'">
            <a-tag color="blue" v-if="text">{{ text }}</a-tag>
            <a-tag color="default" v-else>未标记</a-tag>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-button type="link" danger @click="confirmDelete(record)">
              删除
            </a-button>
          </template>
        </template>
      </a-table>
    </a-card>
    
    <!-- 导出配置对话框 -->
    <ExportDialog
      v-model:visible="exportDialogVisible"
      @export-success="handleExportSuccess"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { message, Modal } from 'ant-design-vue';
import { DatabaseOutlined, CheckCircleOutlined, BarChartOutlined, ExportOutlined, ReloadOutlined, DeleteOutlined } from '@ant-design/icons-vue';
import ExportDialog from '../components/business/ExportDialog.vue';
import { getDataStats, getDatasetList, deleteQAItems } from '../services/dataset';

// 数据统计
const stats = reactive({
  totalCount: 0,
  validCount: 0,
  avgLength: 0
});
const statsLoading = ref(false);

// 表格数据
const qaList = ref([]);
const tableLoading = ref(false);
const selectedRowKeys = ref([]);
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total) => `共 ${total} 条`
});

// 导出对话框
const exportDialogVisible = ref(false);

// 表格列定义
const columns = [
  {
    title: 'ID',
    dataIndex: 'id',
    width: 80
  },
  {
    title: '问题',
    dataIndex: 'question',
    ellipsis: true,
    width: '40%'
  },
  {
    title: '答案',
    dataIndex: 'answer',
    ellipsis: true
  },
  {
    title: '领域标签',
    dataIndex: 'label',
    width: 120
  },
  {
    title: '操作',
    key: 'action',
    width: 90,
    fixed: 'right'
  }
];

// 初始化
onMounted(() => {
  fetchStats();
  fetchQAList();
});

// 获取数据统计
const fetchStats = async () => {
  statsLoading.value = true;
  try {
    const response = await getDataStats();
    
    if (response) {
      stats.totalCount = response.totalCount || 0;
      stats.validCount = response.validCount || 0;
      stats.avgLength = response.avgLength || 0;
    }
  } catch (error) {
    console.error('获取数据统计失败:', error);
  } finally {
    statsLoading.value = false;
  }
};

// 获取问答列表
const fetchQAList = async () => {
  tableLoading.value = true;
  try {
    const response = await getDatasetList({
      format: 'jsonl',
      style: 'Custom',
      template: {
        query: { field: 'question' },
        response: { field: 'answer' },
        category: { field: 'label' }
      },
      page: pagination.current,
      pageSize: pagination.pageSize
    });
    
    if (response && response.data) {
      // 转换为表格数据格式
      qaList.value = response.data.map((item, index) => ({
        id: ((pagination.current - 1) * pagination.pageSize) + index + 1,
        question: item.query || item.question,
        answer: item.response || item.answer,
        label: item.category || item.label
      }));
      
      pagination.total = response.total || 0;
    } else {
      qaList.value = [];
      pagination.total = 0;
    }
  } catch (error) {
    console.error('获取问答列表失败:', error);
    message.error('获取问答列表失败');
  } finally {
    tableLoading.value = false;
  }
};

// 表格分页变化
const handleTableChange = (pag) => {
  pagination.current = pag.current;
  pagination.pageSize = pag.pageSize;
  fetchQAList();
};

// 显示导出对话框
const showExportDialog = () => {
  exportDialogVisible.value = true;
};

// 导出成功处理
const handleExportSuccess = (response) => {
  if (response && response.downloadUrl) {
    message.success('导出成功');
    setTimeout(() => {
      window.open(response.downloadUrl, '_blank');
    }, 500);
  }
};

// 删除问答对
const confirmDelete = (record) => {
  Modal.confirm({
    title: '确认删除',
    content: `您确定要删除问题 "${record.question.substring(0, 30)}${record.question.length > 30 ? '...' : ''}" 及其答案吗？`,
    okText: '确认',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        // 发送删除请求，注意这里要传实际索引（由于表格的ID是从1开始的，需要转换）
        const realIndex = record.id - 1;
        const response = await deleteQAItems([realIndex]);
        
        if (response && response.status === 'success') {
          message.success(response.message || '删除成功');
          // 刷新数据和统计
          fetchQAList();
          fetchStats();
        } else {
          message.error('删除失败');
        }
      } catch (error) {
        console.error('删除问答对失败:', error);
        message.error('删除失败: ' + (error.message || '未知错误'));
      }
    }
  });
};

// 批量删除
const confirmBatchDelete = () => {
  if (selectedRowKeys.value.length === 0) {
    return;
  }
  
  Modal.confirm({
    title: '批量删除',
    content: `您确定要删除选中的 ${selectedRowKeys.value.length} 个问答对吗？`,
    okText: '确认',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        // 获取真实索引（页面ID从1开始，后端从0开始）
        const realIndices = selectedRowKeys.value.map(id => id - 1);
        const response = await deleteQAItems(realIndices);
        
        if (response && response.status === 'success') {
          message.success(response.message || '批量删除成功');
          // 清空选择
          selectedRowKeys.value = [];
          // 刷新数据和统计
          fetchQAList();
          fetchStats();
        } else {
          message.error('批量删除失败');
        }
      } catch (error) {
        console.error('批量删除问答对失败:', error);
        message.error('批量删除失败: ' + (error.message || '未知错误'));
      }
    }
  });
};

// 行选择变化处理
const onSelectChange = (keys) => {
  selectedRowKeys.value = keys;
};
</script>

<style scoped>
.dataset-manager {
  max-width: 1200px;
  margin: 0 auto;
}

.stats-row {
  margin-bottom: 24px;
}

.card-wrapper {
  margin-bottom: 24px;
}

.qa-text {
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 100px;
  overflow-y: auto;
  padding: 4px;
}
</style> 
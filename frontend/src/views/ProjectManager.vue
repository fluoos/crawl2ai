<template>
    <div class="project-manager">
        
      <a-empty 
        v-if="projectList.length === 0 && !projectsLoading" 
        description="您还没有创建任何项目，点击新建项目按钮开始创建" 
      >
        <a-button type="primary" @click="showCreateProjectModal">
          <PlusOutlined /> 新建项目
        </a-button>
      </a-empty>
      
      <a-spin :spinning="projectsLoading" v-else>
        <a-row class="project-list" :gutter="[24, 24]">
          <a-col :xs="24" :sm="12" :md="8" v-for="project in projectList" :key="project.id">
            <a-card 
              hoverable 
              class="project-card"
            >
              <template #title>
                <span class="project-id">项目ID:{{ project.id }}</span>
              </template>
              <template #extra>
                <a-dropdown>
                  <template #overlay>
                    <a-menu>
                      <a-menu-item key="edit" @click.stop="editProject(project)">
                        <EditOutlined /> 编辑
                      </a-menu-item>
                      <a-menu-item key="delete" @click.stop="confirmDeleteProject(project)">
                        <DeleteOutlined /> 删除
                      </a-menu-item>
                    </a-menu>
                  </template>
                  <a-button type="text" @click.stop>
                    <EllipsisOutlined />
                  </a-button>
                </a-dropdown>
              </template>
              <div class="project-name-container">
                <div class="project-name">
                  {{ project.name }}
                </div>
                <a-button type="primary" ghost size="small" @click="navigateToProject(project)">进入项目</a-button>
              </div>
              <div class="project-desc">{{ project.description || '暂无描述' }}</div>
              <div class="project-footer">
                <div class="project-stats">
                  <a-tag color="blue">
                    <DatabaseOutlined /> 数据: {{ project.dataset_count }}
                  </a-tag>
                </div>
                <div class="project-date">创建于: {{ formatDate(project.created_at) }}</div>
              </div>
            </a-card>
          </a-col>
          <a-col :xs="24" :sm="12" :md="8">
            <a-card 
              hoverable 
              class="project-card project-card-new"
            >
              <a-button type="primary" @click="showCreateProjectModal">
                <PlusOutlined /> 新建项目
              </a-button>
            </a-card>
          </a-col>
        </a-row>
      </a-spin>
      
      <!-- 创建项目对话框 -->
      <a-modal
        v-model:visible="createProjectModalVisible"
        title="新建项目"
        @ok="handleCreateProject"
        :confirm-loading="createLoading"
      >
        <a-form
          :model="projectForm"
          :rules="projectFormRules"
          ref="projectFormRef"
          :label-col="{ span: 4 }"
          :wrapper-col="{ span: 20 }"
        >
          <a-form-item label="项目名称" name="name">
            <a-input v-model:value="projectForm.name" placeholder="请输入项目名称(中文或英文)" />
          </a-form-item>
          <a-form-item label="项目描述" name="description">
            <a-textarea 
              v-model:value="projectForm.description" 
              placeholder="请输入项目描述" 
              :auto-size="{ minRows: 3, maxRows: 5 }" 
            />
          </a-form-item>
        </a-form>
      </a-modal>
      
      <!-- 编辑项目对话框 -->
      <a-modal
        v-model:visible="editProjectModalVisible"
        title="编辑项目"
        @ok="handleUpdateProject"
        :confirm-loading="updateLoading"
      >
        <a-form
          :model="editProjectForm"
          :rules="projectFormRules"
          ref="editProjectFormRef"
          :label-col="{ span: 4 }"
          :wrapper-col="{ span: 20 }"
        >
          <a-form-item label="项目名称" name="name">
            <a-input v-model:value="editProjectForm.name" placeholder="请输入项目名称" />
          </a-form-item>
          <a-form-item label="项目描述" name="description">
            <a-textarea 
              v-model:value="editProjectForm.description" 
              placeholder="请输入项目描述（选填）" 
              :auto-size="{ minRows: 3, maxRows: 5 }" 
            />
          </a-form-item>
        </a-form>
      </a-modal>
    </div>
  </template>
  
  <script setup>
  import { ref, reactive, onMounted } from 'vue';
  import { useRouter } from 'vue-router';
  import { message, Modal, Empty } from 'ant-design-vue';
  import {
    DatabaseOutlined,
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
    EllipsisOutlined
  } from '@ant-design/icons-vue';
  import { createProject, updateProject, deleteProject, listProjects } from '../services/project';
  
  const router = useRouter();
  
  // 项目列表
  const projectList = ref([]);
  const projectsLoading = ref(false);
  
  // 新建项目相关
  const createProjectModalVisible = ref(false);
  const createLoading = ref(false);
  const projectForm = reactive({
    name: '',
    description: ''
  });
  const projectFormRef = ref(null);
  
  // 编辑项目相关
  const editProjectModalVisible = ref(false);
  const updateLoading = ref(false);
  const editProjectForm = reactive({
    id: null,
    name: '',
    description: ''
  });
  const editProjectFormRef = ref(null);
  
  // 表单验证规则
  const projectFormRules = {
    name: [
      { required: true, message: '请输入项目名称', trigger: 'blur' },
      { min: 2, max: 50, message: '项目名称长度应在2-50个字符之间', trigger: 'blur' }
    ]
  };
  
  // 页面初始化
  onMounted(() => {
    fetchProjects();
  });
  
  // 格式化日期
  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', { 
      year: 'numeric', 
      month: '2-digit', 
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  // 获取项目列表
  const fetchProjects = async () => {
    projectsLoading.value = true;
    try {
      const response = await listProjects();
      if (response && response.status === 'success') {
        projectList.value = response.data;
      } else {
        projectList.value = [];
      }
    } catch (error) {
      console.error('获取项目列表失败:', error);
      message.error('获取项目列表失败');
    } finally {
      projectsLoading.value = false;
    }
  };
  
  // 显示创建项目对话框
  const showCreateProjectModal = () => {
    projectForm.name = '';
    projectForm.description = '';
    createProjectModalVisible.value = true;
  };
  
  // 处理创建项目
  const handleCreateProject = async () => {
    try {
      await projectFormRef.value.validate();
      createLoading.value = true;
      
      const response = await createProject(projectForm);
      if (response && response.status === 'success') {
        message.success('项目创建成功');
        createProjectModalVisible.value = false;
        fetchProjects();
      } else {
        // 处理后端返回的错误消息
        message.error(response.message || '项目创建失败');
      }
    } catch (error) {
      console.error('创建项目失败:', error);
    } finally {
      createLoading.value = false;
    }
  };
  
  // 编辑项目
  const editProject = (project) => {
    editProjectForm.id = project.id;
    editProjectForm.name = project.name;
    editProjectForm.description = project.description || '';
    editProjectModalVisible.value = true;
  };
  
  // 处理更新项目
  const handleUpdateProject = async () => {
    try {
      await editProjectFormRef.value.validate();
      updateLoading.value = true;
      
      const response = await updateProject(editProjectForm.id, {
        name: editProjectForm.name,
        description: editProjectForm.description
      });
      
      if (response && response.status === 'success') {
        message.success('项目更新成功');
        editProjectModalVisible.value = false;
        fetchProjects();
      } else {
        // 处理后端返回的错误消息
        if (response && response.status === 'error') {
          message.error(response.message || '项目更新失败');
        } else {
          message.error('项目更新失败');
        }
      }
    } catch (error) {
      console.error('更新项目失败:', error);
    } finally {
      updateLoading.value = false;
    }
  };
  
  // 确认删除项目
  const confirmDeleteProject = (project) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除项目"${project.name}"吗？此操作将同时删除项目下的所有数据集，且不可恢复！`,
      okText: '确认',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await deleteProject(project.id);
          if (response) {
            message.success('项目删除成功');
            fetchProjects();
          } else {
            message.error('项目删除失败');
          }
        } catch (error) {
          console.error('删除项目失败:', error);
          message.error('删除项目失败');
        }
      }
    });
  };
  
  const navigateToProject = (project) => {
    // 进入项目前，先把当前项目的信息存储到localstorage中
    localStorage.setItem('currentProject', JSON.stringify(project));
    router.push({
      path: '/links',
      params: { projectId: project.id }
    });
  };
  </script>
  
  <style scoped>
  .project-manager {
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 500px;
  }

  .project-list {
    min-width: 74vw;
  }
  
  .project-card {
    height: 100%;
    display: flex;
    flex-direction: column;
    cursor: pointer;
    min-width: 320px;
    max-width: 520px;
    min-height: 200px;
  }
  
  .project-id {
    color: #8c8c8c;
    margin-right: 8px;
    font-size: 14px;
  }

  .project-name-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  .project-name {
    font-size: 18px;
    font-weight: bold;
  }
  
  .project-desc {
    color: #595959;
    margin-bottom: 16px;
    min-height: 50px;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .project-footer {
    margin-top: auto;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .project-date {
    font-size: 12px;
    color: #8c8c8c;
  }

  .project-card-new {
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
  }
  </style>
## 导入规范

本项目使用以下导入规范:

### ✅ 推荐的导入方式

```python
# 导入路由模块
from app.api.routes import crawler, files

# 导入特定类或函数
from app.api.routes.crawler import CrawlRequest
```

### ❌ 不推荐的导入方式 (已弃用)

```python
# 不要直接从app.api导入
from app.api import crawler  # 已弃用
```

`app/api/`目录下的文件只是对`app/api/routes/`下对应文件的重新导出，计划在将来版本中移除。 
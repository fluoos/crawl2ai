from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api import crawler, files, converter, common, system, dataset

# 确保必要的目录存在
for dir_path in ["output", "upload", "export", "config"]:
    os.makedirs(dir_path, exist_ok=True)

# 确保导出子目录存在
for style in ["alpaca", "sharegpt", "custom"]:
    os.makedirs(os.path.join("export", style), exist_ok=True)

app = FastAPI(
    title="数据集生成与大模型微调工具",
    description="一键爬取指定域名的链接，转换为大模型友好的markdown文件，并生成训练数据集",
    version="1.0.0",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应当限定为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(common.router, prefix="/api", tags=["通用"])
app.include_router(crawler.router, prefix="/api/crawler", tags=["链接爬虫"])
app.include_router(files.router, prefix="/api/files", tags=["文件管理"])
app.include_router(converter.router, prefix="/api/converter", tags=["文件转换"])
app.include_router(dataset.router, prefix="/api/dataset", tags=["数据集管理"])
app.include_router(system.router, prefix="/api/system", tags=["系统配置"])

# 挂载静态文件
app.mount("/output", StaticFiles(directory="output"), name="output")
app.mount("/export", StaticFiles(directory="export"), name="export")

@app.get("/")
async def root():
    return {"message": "欢迎使用数据集生成与大模型微调工具 API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 
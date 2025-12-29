import mlflow
import os

print("当前工作目录:", os.getcwd())
print("MLflow tracking URI:", mlflow.get_tracking_uri())

try:
    with mlflow.start_run() as run:
        print(f"Run ID: {run.info.run_id}")
        mlflow.log_param("model", "tree")
        mlflow.log_metric("rmse", 0.85)
        print("参数和指标记录成功!")
        print(f"Run 信息: {run.info}")
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

print("脚本执行完成")
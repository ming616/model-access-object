# Agent Task Runtime

Task context persistence, execution recovery, and Agent instance composition for Agent Teams.

Agent Task Runtime（ATR）为 Agentic Team 提供通用任务运行基础：保存任务上下文与记忆，根据业务定义装配角色 Agent，并支持从已保存的执行进度继续任务。

**项目状态：设计筹备。当前内容为项目定位、接口草案和使用示例；运行时实现尚未建立。**

## 核心功能

1. 任务管理：创建任务、记录进度、暂停、恢复、完成与取消。
2. 上下文与记忆：保存任务资料、交互历史、阶段成果以及待处理事项。
3. Agent 实例装配：根据角色定义创建运行实例，注入 MAO、工具和存储访问接口。
4. 检查点与恢复：保存一致的任务状态；重新创建运行对象后继续执行。

持久化以任务为中心。Agent、MAO、MSCP 的对象由应用和容器在运行时装配。模型访问所需资源通过 MAO 和 MSCP 按调用获取与释放。

## 体系中的职责

| 部分 | 核心职责 |
| --- | --- |
| Agent Team | 业务需求、角色职责、协作规则、业务完成条件 |
| ATR | 任务运行、上下文保存与恢复、Agent 实例装配及生命周期 |
| [MAO](https://github.com/ming616/model-access-object) | 模型访问使用方式 |
| [MSCP](https://github.com/ming616/model-service-connector-pool) | 模型资源获取、占用与释放 |
| TaskStore | 任务记录和检查点的持久化接口 |

ATR 接收 Team 定义的工作项和后续动作。业务协作可以包含分支、并行需求与反馈循环；首轮实现先验证逐步执行与恢复。

## 首轮验证案例

申报书撰写 Team 完成初稿并保存检查点后，退出运行进程。启动新的运行环境，从同一个任务 ID 加载草稿和待审阅工作，重新装配审阅 Agent，继续审阅与修改。

## 文档

- [架构与边界](docs/architecture.zh-CN.md)
- [接口草案](docs/api.md)
- [使用与恢复示例](docs/usage.md)
- [任务检查点样例](examples/checkpoint.json)
- [建设路线](ROADMAP.md)

## 仓库筹备说明

目标独立仓库名为 `agent-task-runtime`。当前筹备内容临时保存在 MAO 的独立分支中；本目录可整体迁入新仓库根目录。MAO 的运行代码仍按原有职责维护。

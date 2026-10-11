# 使用与恢复示例

本文为调用顺序示意，ATR 接口尚未实现。实际可运行示例将在首轮实现阶段补齐。

## 应用组装

应用启动时创建 MSCP、MAO 和 TaskStore，再登记业务 Team 和角色工厂。

```python
# 接口草案：mao 由应用通过 MSCPAdapter(pool) 创建。
services = {"mao": mao}
container = AgentContainer(services=services)

container.register("writer", WriterAgent)
container.register("reviewer", ReviewerAgent)

runtime = TaskRuntime(
    container=container,
    store=task_store,
    teams={"proposal-writing@1": proposal_team_definition},
)
```

WriterAgent 和 ReviewerAgent 的业务代码由申报书 Team 项目提供。角色通过注入的 MAO 访问模型。TeamDefinition 决定初稿、审阅和修改之间的协作关系。

## 创建与推进

```python
# 接口草案
task_id = await runtime.create(
    team_key="proposal-writing",
    definition_version="1",
    input={"topic": "智能软件研发教学案例"},
)

await runtime.advance(task_id)  # 完成初稿并保存成果、历史及待审阅工作。
await runtime.pause(task_id)
```

这时持久化的数据类似 [checkpoint.json](../examples/checkpoint.json)。任务记录包含初稿，以及 `review-1` 待执行工作。运行环境退出后，业务数据继续保存在 TaskStore 中。

## 新运行环境中的恢复

新的应用运行环境按同样的组装方式创建依赖并登记版本兼容的 Team 定义，连接原来的 TaskStore。

```python
# 接口草案：runtime 是重新组装的对象。
await runtime.resume(task_id)
```

运行时加载已保存的任务，创建新的 ReviewerAgent 对象，为它提供初稿和相关上下文，从审阅工作继续。需要修改时，TeamDefinition 生成新一轮撰写工作及审阅工作。

恢复过程沿用 task_id 和已保存的业务进度。每次模型调用均通过 MAO 获取 MSCP 租约，完成或取消后归还。

## 两个任务同时存在

每个任务使用各自的 task_id、共享上下文和角色私有历史。同一应用可以复用 MAO 和 MSCP。

首轮执行器逐项推进每个任务。任务 A 的审阅意见只写入任务 A，任务 B 使用自己的上下文。跨任务知识共享通过显式的外部记忆接口扩展。

## 需要核对的恢复场景

正常暂停且无在途工作时，从 pending_work 继续。异常退出后存在 inflight 记录时，先调用 Team 的恢复策略。外部提交结果未确认的工作应先核对实际结果，再决定下一步动作。

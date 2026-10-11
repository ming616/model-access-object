# 接口草案

本文描述首轮实现目标。以下名称、签名和行为均为草案，当前尚无可调用的 ATR 运行时实现。

## 核心数据

| 类型 | 核心字段 |
| --- | --- |
| TaskRecord | schema_version、task_id、team_key、definition_version、revision、status、input、context、pending_work、completed_work、inflight |
| TaskContext | shared、actors、memory |
| WorkItem | work_id、role、context_key、input |
| WorkResult | work_id、output、context_updates、memory_updates |
| Transition | pending_work、completed、result |

`actors` 保存任务内各参与位置的私有上下文。WorkResult 中的更新由 Team 和运行时协调提交，写入时与后续工作合并为一个检查点。较大文件和成果可以保存引用，文件内容由相应存储服务管理。

状态候选为 `created`、`running`、`paused`、`completed`、`failed` 和 `cancelled`。具体转换及异常行为随首轮实现验证。

## TeamDefinition

| 接口 | 行为 |
| --- | --- |
| roles | 角色名与 Agent 工厂的登记关系 |
| initial_work(input) | 根据业务输入生成初始工作项 |
| advance(context, work, result) | 接收工作成果，更新业务上下文并确定后续工作或任务完成 |
| recover(context, inflight) | 对未确认的工作决定核对、重试或暂停等待 |

Team 定义登记 `team_key` 和 `definition_version`。任务恢复前需要有兼容的定义；版本迁移采用显式转换规则。

业务可在角色 Agent 中使用 MAO、工具或其他服务。运行时通过 WorkItem 选择已登记的角色工厂和上下文位置。

## AgentContainer

| 接口 | 行为 |
| --- | --- |
| register(role, factory) | 登记角色工厂 |
| scope(task_context) | 开启一次任务运行作用域 |
| scope.get(role, context_key) | 按需创建实例并注入服务，同一作用域内按键复用 |
| scope.aclose() | 关闭本作用域创建的对象，完成清理 |

工厂接收所需服务和任务上下文访问接口。共享依赖通过应用配置提供；共享依赖的关闭由应用负责。

## TaskStore

| 异步接口 | 行为 |
| --- | --- |
| create(record) | 原子创建新任务；相同 task_id 已存在时失败 |
| load(task_id) | 加载最新记录 |
| save(record, expected_revision) | 检查当前版本并原子保存；成功后返回新的 revision |

存储数据为可序列化的任务记录。首轮采用 SQLite，并设计可替换的存储接口。数据库事务只覆盖任务存储自身的更新。

## TaskRuntime

| 异步接口 | 行为 |
| --- | --- |
| create(team_key, definition_version, input) | 创建并保存任务，返回 task_id |
| advance(task_id) | 推进一个可执行工作项并提交检查点 |
| run(task_id) | 持续推进，直到完成、暂停、取消或失败 |
| pause(task_id) | 请求在安全步骤边界暂停并保存进度 |
| resume(task_id) | 加载记录、检查定义及未确认工作，重新装配实例并继续 |
| cancel(task_id) | 请求停止执行并保留取消状态及必要的任务记录 |

首轮每个任务只允许一个执行者。并行分支、多个进程竞争任务及跨机器恢复需要后续扩展。

## 错误与取消

需要区分任务不存在、任务已完成、定义不匹配、版本冲突和未确认工作等情况。MAO 的访问错误由工作执行产生，Team 的策略决定是否重试、转交角色或暂停。

取消应沿调用链传播，确保模型租约和临时资源得到释放。任务取消与删除任务历史采用独立操作，保存范围由应用策略决定。

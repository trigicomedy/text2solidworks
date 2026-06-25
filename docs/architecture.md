# text2solidworks 工程架构与处理流程

> 状态：Accepted，当前架构基线  
> 目标：确定项目目录、模块职责、数据契约和执行流程。后续代码迁移与 Skill 建设以本文档为准。

## 1. 项目目标

`text2solidworks` 将自然语言机械设计需求转换为：

1. 可检查、可修改的设计计划。
2. 可确定执行的 SolidWorks 建模操作。
3. 参数化零件和装配体。
4. STEP、Parasolid 等交换文件。
5. 可选的工程图、爆炸图和仿真输入。

项目采用四层结构：

```text
自然语言需求
    ↓
Skill：理解、设计与规划
    ↓
Planning：校验、标准化和调度计划
    ↓
SolidWorks Runtime：确定性执行建模操作
    ↓
SolidWorks：生成零件、装配体和导出文件
```

基本原则：

- Skill 负责推理，不直接堆叠大量 COM 调用。
- Runtime 负责确定性操作，不自行猜测设计意图。
- JSON 计划是 Skill 与 Python runtime 之间的正式契约。
- 工程源码与任务生成物分开保存。
- 装配优先使用基准面、基准轴和坐标系，不依赖易失效的面编号。

## 2. 固定目录结构

### 2.1 源码仓库

建议源码仓库位于：

```text
D:\text2solidworks
```

正式结构：

```text
text2solidworks/
├─ README.md
├─ LICENSE
├─ AGENTS.md
├─ pyproject.toml
├─ requirements.txt
├─ .gitignore
│
├─ .agents/
│  └─ skills/
│     ├─ part-design/
│     │  ├─ SKILL.md
│     │  └─ references/
│     │     ├─ part_categories.md
│     │     ├─ parameter_schema.md
│     │     └─ ansys_modal_workflow.md
│     │
│     ├─ assembly-planning/
│     │  ├─ SKILL.md
│     │  └─ references/
│     │
│     └─ solidworks-execution/
│        ├─ SKILL.md
│        └─ references/
│           ├─ api_compatibility.md
│           ├─ naming_and_encoding.md
│           └─ debugging_workflow.md
│
├─ src/
│  └─ text2solidworks/
│     ├─ __init__.py
│     │
│     ├─ planning/
│     │  ├─ __init__.py
│     │  ├─ plan_loader.py
│     │  ├─ validators.py
│     │  ├─ normalizers.py
│     │  └─ orchestrator.py
│     │
│     └─ runtime/
│        ├─ __init__.py
│        └─ solidworks/
│           ├─ __init__.py
│           ├─ application.py
│           ├─ documents.py
│           ├─ selection.py
│           ├─ sketches.py
│           ├─ features.py
│           ├─ reference_geometry.py
│           ├─ components.py
│           ├─ mates.py
│           ├─ export.py
│           ├─ units.py
│           ├─ compatibility.py
│           │
│           └─ operations/
│              ├─ __init__.py
│              ├─ primitives.py
│              ├─ holes.py
│              ├─ links.py
│              ├─ joints.py
│              └─ interfaces.py
│
├─ schemas/
│  ├─ design_plan.schema.json
│  ├─ part_plan.schema.json
│  ├─ modeling_plan.schema.json
│  ├─ interface_plan.schema.json
│  ├─ connection_plan.schema.json
│  └─ execution_result.schema.json
│
├─ examples/
│  ├─ debug_circle_extrude.py
│  ├─ create_box.py
│  ├─ create_link.py
│  └─ create_6dof_robot_arm.py
│
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  └─ solidworks/
│
├─ scripts/
│  ├─ check_environment.py
│  ├─ validate_plans.py
│  └─ install_user_skills.ps1
│
└─ docs/
   ├─ architecture.md
   ├─ plan_contracts.md
   ├─ solidworks_setup.md
   └─ development_rules.md
```

### 2.2 任务工作区

所有 Prompt、中间计划、日志和 CAD 结果放在：

```text
D:\text2solidworks_workspace
```

每个任务建立独立项目：

```text
text2solidworks_workspace/
└─ projects/
   └─ <project_id>/
      ├─ prompt/
      │  └─ original_prompt.md
      │
      ├─ plans/
      │  ├─ design_plan.json
      │  ├─ part_plans/
      │  │  └─ <part_id>.json
      │  ├─ modeling_plans/
      │  │  └─ <part_id>.json
      │  ├─ interface_plans/
      │  │  └─ <part_id>.json
      │  └─ connection_plan.json
      │
      ├─ generated_scripts/
      ├─ logs/
      ├─ parts/
      ├─ assemblies/
      ├─ exports/
      ├─ simulation/
      ├─ drawings/
      └─ reports/
```

任务工作区默认不提交到源码仓库。

## 3. 各层职责

### 3.1 Skills

Skill 是大模型的领域工作流程和设计知识。

#### `part-design`

负责：

- 识别单个零件的名称、品类和功能。
- 生成参数表。
- 分析载荷路径、制造要求和轻量化需求。
- 规划特征顺序。
- 规划基准面、轴线、坐标系和连接接口。
- 生成零件级仿真计划。

不负责：

- 直接执行 SolidWorks COM API。
- 求解装配配合。
- 编造仿真结果。

#### `assembly-planning`

负责：

- 确定零件层级。
- 描述零件之间的功能连接。
- 规划具体配合。
- 预测配合后的剩余自由度。
- 检查配合是否过约束、欠约束或存在装配冲突。

#### `solidworks-execution`

负责：

- 指导 Agent 如何调用 Python runtime。
- 处理 SolidWorks 版本、语言和 COM 兼容问题。
- 规定可见执行、日志、重建和调试方法。
- 规定原生圆、圆弧、孔和圆角特征的使用要求。

它不是 Runtime 的替代品，只是调用 Runtime 的操作说明。

### 3.2 Planning

`src/text2solidworks/planning` 是计划进入 Runtime 之前的控制层。

负责：

- 读取 JSON 计划。
- 使用 JSON Schema 校验结构。
- 检查单位、引用、名称和依赖。
- 将默认值和兼容写法标准化。
- 按依赖关系排列零件和特征。
- 调度零件建模、装配和导出。
- 收集每一步执行结果。

不负责：

- 生成复杂机械设计。
- 直接调用底层 COM 接口。
- 在计划缺少关键参数时自行猜测。

### 3.3 SolidWorks Runtime

`src/text2solidworks/runtime/solidworks` 封装底层 SolidWorks API。

#### 基础模块

| 模块 | 职责 |
|---|---|
| `application.py` | 连接、启动和显示 SolidWorks |
| `documents.py` | 新建、打开、保存和关闭文档 |
| `selection.py` | 选择平面、草图、特征、面和边 |
| `sketches.py` | 创建草图及原生草图实体 |
| `features.py` | 拉伸、切除、孔、阵列、圆角和倒角 |
| `reference_geometry.py` | 创建基准面、轴线、点和坐标系 |
| `components.py` | 插入、读取和定位装配组件 |
| `mates.py` | 建立配合并读取配合状态 |
| `export.py` | 导出 STEP、Parasolid 等格式 |
| `units.py` | 毫米与 SolidWorks API SI 单位转换 |
| `compatibility.py` | SW 版本、语言、COM 调用和空对象兼容 |

基础模块中的函数应尽量只表达一次明确的 SolidWorks 操作。

示例：

```python
create_circle(...)
extrude_boss(...)
create_datum_axis(...)
add_concentric_mate(...)
```

#### 高级操作模块

`runtime/solidworks/operations` 仍属于 Runtime，但用于表达机械建模意图。

示例：

```python
create_mounting_flange(...)
create_robot_link(...)
create_joint_housing(...)
create_bolt_circle(...)
create_rotary_interface(...)
```

高级函数组合基础模块，不直接重复散落的 COM 调用。

当前不单独建立顶层 `operations` 或 `execution` 包，避免早期层级过多。

### 3.4 Schemas

Schema 是 Skill、Planning 和 Runtime 之间的数据契约。

主要计划：

| 文件 | 内容 |
|---|---|
| `design_plan.json` | 整体任务、零件表和装配层级 |
| `part_plan.json` | 单个零件的功能、品类和参数 |
| `modeling_plan.json` | 有序建模特征和依赖 |
| `interface_plan.json` | 基准面、轴线、坐标系及连接语义 |
| `connection_plan.json` | 零件间连接、Mate 和剩余自由度 |
| `execution_result.json` | Runtime 每一步的成功、失败和产物 |

计划未通过 Schema 和语义校验时，不进入 SolidWorks 执行。

## 4. 完整处理流程

### 阶段 A：建立任务

输入：用户自然语言 Prompt。

操作：

1. 生成稳定的 `project_id`。
2. 创建独立 workspace 项目目录。
3. 原样保存 `original_prompt.md`。
4. 记录时间、版本和运行环境。

### 阶段 B：整体设计规划

由设计规划 Skill 生成 `design_plan.json`：

- 项目目标。
- 零件清单。
- 每个零件的 `part_id`、显示名、品类和功能。
- 装配层级。
- 全局尺寸与约束。
- 用户明确条件、推断条件和待确认项。

### 阶段 C：单零件规划

对每个零件调用 `part-design`：

1. 生成 `part_plan.json`。
2. 生成 `modeling_plan.json`。
3. 生成 `interface_plan.json`。
4. 检查可制造性和仿真准备情况。

接口必须在零件建模前规划，而不是装配失败后再补。

### 阶段 D：连接规划

由 `assembly-planning` 读取全部零件接口，生成 `connection_plan.json`。

每个连接至少包含：

- 父零件与子零件。
- 连接功能。
- 使用的双方接口。
- 所需 Mate 列表。
- 每条 Mate 的方向和预期状态。
- 连接完成后的剩余自由度。
- 运动范围和干涉检查要求。

### 阶段 E：计划校验

Planning 层依次执行：

1. JSON Schema 校验。
2. 单位校验。
3. 名称唯一性校验。
4. 参数引用校验。
5. 特征依赖校验。
6. 接口引用校验。
7. 装配连接和自由度初步校验。

发现关键错误时停止，不调用 SolidWorks。

### 阶段 F：零件生成

Runtime 对每个零件：

1. 新建零件文档。
2. 建立或确认主基准。
3. 按 `modeling_plan` 执行特征。
4. 创建 `interface_plan` 指定的稳定参考几何。
5. 重建并检查实体。
6. 保存 SLDPRT。
7. 按需导出 STEP 或 Parasolid。
8. 写入零件执行结果。

支持三种模式：

```text
full            重新生成零件并装配
parts-only      只生成或更新零件
assembly-only   读取已有零件并重新装配
```

### 阶段 G：装配生成

Runtime：

1. 新建装配体。
2. 插入已有零件。
3. 固定基准零件。
4. 根据 `connection_plan` 选择命名接口。
5. 逐条创建 Mate。
6. 每完成一个功能连接就检查剩余自由度。
7. 重建并检查 Mate 状态。
8. 检查组件位置和明显干涉。
9. 保存 SLDASM。

插入零件时允许使用初始坐标帮助显示，但最终定位必须由 Mate 或明确固定状态决定。

### 阶段 H：后处理

按用户要求执行：

- STEP 或 Parasolid 导出。
- 爆炸图。
- 工程图。
- 质量属性。
- 干涉检查。
- ANSYS 输入与仿真报告。

## 5. 旧 Python 代码的迁移规则

迁移时不直接重写全部代码，先分类再移动。

| 旧代码内容 | 新位置 |
|---|---|
| 连接或启动 SW | `runtime/solidworks/application.py` |
| 新建、打开、保存文件 | `runtime/solidworks/documents.py` |
| 选择中文或英文基准面 | `selection.py` 与 `compatibility.py` |
| 画圆、矩形、圆弧 | `sketches.py` |
| 拉伸、切除、孔、圆角 | `features.py` |
| 基准面、轴线、坐标系 | `reference_geometry.py` |
| 插入零件 | `components.py` |
| 装配 Mate | `mates.py` |
| 创建完整连杆或关节 | `operations/links.py` 或 `operations/joints.py` |
| 调试圆形拉伸脚本 | `examples/debug_circle_extrude.py` |
| 六轴机械臂完整脚本 | 暂留 `examples/create_6dof_robot_arm.py` |

迁移步骤：

1. 保留原脚本可运行。
2. 提取已验证的通用函数。
3. 给旧脚本增加兼容导入。
4. 运行最小调试示例。
5. 运行零件示例。
6. 最后运行装配示例。

不在迁移同时改变全部 COM 参数和模型结构。

## 6. 稳定性规则

### 6.1 几何

- 圆、圆孔、圆弧、圆角和端部圆形安装区必须使用 SolidWorks 原生特征。
- 不允许用多段线近似圆形，除非用户明确允许。
- 装配接口优先使用命名基准几何。
- 实体面只可作为辅助引用或带有几何识别规则的回退引用。
- 切除和圆角可能改变拓扑，不能依赖面在特征树中的顺序编号。

### 6.2 命名

- 程序索引使用稳定英文 `id`。
- 面向用户可同时保存中文 `display_name`。
- 不依赖默认名称 `Sketch1`、`草图1` 或不同语言模板名称。
- Runtime 必须兼容中文和英文默认基准面。

### 6.3 单位

- 计划文件默认使用 `mm`、`deg`、`N`、`kg`。
- 所有参数显式携带单位。
- 仅在 Runtime API 边界转换为米和弧度。

### 6.4 执行

- 可见模式下让用户看到 SolidWorks 操作过程。
- 主要特征完成后重建并更新视图。
- API 返回 `False`、`None` 或 COM 异常时记录完整上下文。
- 关键特征失败后停止当前零件，不继续制造虚假的成功结果。

## 7. 测试策略

### 单元测试

不启动 SolidWorks：

- 单位转换。
- Schema 校验。
- 计划标准化。
- 依赖排序。
- 名称和接口引用检查。

### 集成测试

使用伪 Runtime 或录制的执行结果：

- 从计划到调用序列。
- 单零件操作编排。
- 装配连接编排。

### SolidWorks 测试

需要本机安装 SolidWorks：

1. 新建并保存空零件。
2. 圆形草图和拉伸。
3. 通孔切除。
4. 圆角和倒角。
5. 创建基准轴、基准面和坐标系。
6. 插入两个零件。
7. 创建重合和同轴 Mate。
8. 导出 STEP 与 Parasolid。

复杂机械臂不作为最底层功能的唯一测试。

## 8. 发布方式

Git 仓库包含：

- `.agents/skills`
- `src`
- `schemas`
- `examples`
- `tests`
- `scripts`
- `docs`

不包含：

- 用户 Prompt。
- 生成的 SLDPRT、SLDASM。
- 大型 STEP 或 Parasolid 文件。
- 临时日志。
- 本机模板绝对路径。
- Python 虚拟环境。

项目级 Skill 保存在 `.agents/skills`，随仓库发布。若需要在所有项目使用，可通过安装脚本复制或链接到用户级 Skill 目录，但用户级目录不是源码的唯一保存位置。

## 9. 当前阶段暂不建立的内容

为了控制复杂度，当前不建立：

- 独立顶层 `operations` 包。
- 独立顶层 `execution` 包。
- 数据库。
- Web 管理界面。
- 自动训练或微调流水线。
- 完整 PLM/PDM 集成。
- 自动生成所有类型机械零件的超大函数库。

只有当现有 `planning` 或 `runtime` 明显过大时，才通过架构决策记录进一步拆分。

## 10. 审核后实施顺序

架构确认后按以下顺序实施：

1. 建立固定目录和基础工程配置。
2. 将 `part-design` Skill 放入 `.agents/skills`。
3. 盘点现有 Python 文件并生成迁移清单。
4. 迁移已验证的底层 SW 函数。
5. 建立第一版 JSON Schema。
6. 跑通“圆形草图 → 拉伸 → 保存”的最小链路。
7. 跑通“单零件计划 → Runtime”的链路。
8. 跑通“已有零件 → assembly-only → Mate”的链路。
9. 再逐步重构六轴机械臂示例。

## 11. 待审核决定

请重点确认：

- 是否接受 Skill、Planning、Runtime、SolidWorks 四层关系。
- 是否接受高级函数位于 `runtime/solidworks/operations`。
- 是否接受 `.agents/skills` 作为 Skill 的仓库源码位置。
- 是否接受源码与 `text2solidworks_workspace` 任务产物分离。
- 是否接受 JSON 计划必须校验后才能执行。
- 是否接受先迁移并保持旧脚本可运行，再逐步重构。

本文档确认后，任何新增顶层目录或职责变化都应先更新架构文档，再修改代码。

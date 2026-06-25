# 零件参数与计划结构

## 参数记录原则

每个参数建议包含：

```json
{
  "name": "joint_center_distance",
  "value": 420,
  "unit": "mm",
  "status": "fixed",
  "source": "user_prompt",
  "rationale": "用户明确给定大臂长度",
  "range": null,
  "affects": ["main_body", "joint_interface_b"]
}
```

`status` 可取：

- `fixed`：用户明确给定。
- `inferred`：依据标准、功能或相邻尺寸推断。
- `fuzzy`：仍需选择具体值或范围。
- `detail`：不改变主功能的局部细节。

推断参数必须记录 `rationale`。存在合理区间时，应同时记录 `range`，不要只留下一个看似精确的数字。

## 零件身份

```json
{
  "part_id": "upper_arm_link",
  "display_name": "大臂连杆",
  "category": "robot_link",
  "function": "连接肩关节与肘关节并传递弯矩和扭矩",
  "parent_assembly": "shoulder_upper_arm_assembly",
  "manufacturing_process": ["CNC_machining"],
  "revision": 1
}
```

`part_id` 应稳定、唯一、便于文件命名和程序索引。`display_name` 面向用户。`category` 用于驱动参数需求和设计检查。

## 通用参数组

### 几何

- 总长、宽、高或厚度。
- 中心距和关键偏置。
- 截面尺寸。
- 孔径、孔深、孔距和孔阵列。
- 端部安装区尺寸。
- 壁厚。
- 空腔、槽、窗口和减重孔尺寸。
- 圆角与倒角。
- 装配间隙和加工余量。

### 材料

- 材料牌号。
- 弹性模量。
- 泊松比。
- 密度。
- 屈服强度。
- 疲劳或阻尼数据，仅在分析需要时填写。

### 仿真

- 分析类型。
- 载荷类型、大小、方向和作用区域。
- 约束类型、自由度和作用区域。
- 接触与连接。
- 目标频段。
- 求解阶数。
- 最大允许变形、应力或应变。
- 需要避开的工作频率及安全裕度。

## 品类驱动参数

### 连杆 `robot_link`

重点参数：

- 两端关节中心距。
- 主截面宽度、厚度和变化规律。
- 两端安装区尺寸与轴线。
- 壁厚和中空结构。
- 减重窗口位置、长度、宽度和端部圆角。
- 加强筋位置和厚度。
- 弯曲与扭转刚度方向。
- 电缆通道和维护开口。

重点检查：

- 减重窗口不得切断主要载荷路径。
- 关节连接区应局部增厚。
- 窗口端部使用圆弧或原生圆角降低应力集中。

### 支架 `bracket`

重点参数：

- 安装面尺寸和夹角。
- 孔型、孔距和定位方式。
- 板厚或壁厚。
- 加强筋。
- 工具进入空间。
- 载荷作用点与安装面距离。

重点检查：

- 根部圆角。
- 螺栓孔边距。
- 偏心载荷造成的弯矩。

### 关节壳体 `joint_housing`

重点参数：

- 旋转轴线。
- 外径、内径和轴向厚度。
- 轴承、减速器和电机安装位。
- 端盖和紧固结构。
- 线缆通道。
- 运动包络和防干涉间隙。

重点检查：

- 同轴接口。
- 轴承台阶与挡肩。
- 运动范围内的外形干涉。
- 装配、拆卸和紧固路径。

### 轴类 `shaft`

重点参数：

- 总长和各轴段直径。
- 轴承位、密封位和配合公差。
- 台阶、挡圈槽、键槽和螺纹。
- 中心孔或通孔。
- 圆角与退刀槽。

重点检查：

- 直径突变处应力集中。
- 轴承位和配合面的加工精度。
- 键槽对疲劳强度的影响。

### 法兰 `flange`

重点参数：

- 外径、厚度和中心孔。
- 螺栓孔数量、孔径和分布圆。
- 定位止口。
- 密封面或接触面。
- 背部加强结构。

重点检查：

- 孔阵列必须使用圆周阵列或孔向导等原生特征。
- 螺栓孔和中心孔之间保留合理壁厚。

### 板件 `plate`

重点参数：

- 长宽厚。
- 折弯、翻边或局部凸台。
- 孔、槽和切口。
- 基准边和定位孔。

重点检查：

- 薄板应明确采用实体、钣金或板壳分析路径。
- 避免无法加工的内角和过窄槽。

## 推荐计划结构

`part_design_plan.md` 面向人阅读，至少包括：

1. 设计目标。
2. 零件身份与品类。
3. 参数摘要。
4. 结构与载荷路径。
5. 制造策略。
6. 建模步骤摘要。
7. 装配接口摘要。
8. 仿真目的与边界条件。
9. 假设、风险和待确认项。

`modeling_plan.json` 面向 runtime，每个步骤建议包含：

```json
{
  "step_id": "F010",
  "operation": "extrude_boss",
  "feature_name": "main_body",
  "reference": "PLN_MID",
  "parameters": ["body_width", "body_height", "body_length"],
  "depends_on": ["REF001"],
  "creates": ["BODY_MAIN"],
  "validation": ["solid_body_count == 1"]
}
```

`interface_plan.json` 每个接口建议包含：

```json
{
  "name": "AXIS_JOINT_A",
  "type": "datum_axis",
  "construction_method": "through_cylindrical_face",
  "design_intent": "肩关节旋转轴",
  "connected_part": "shoulder_housing",
  "expected_relation": "concentric",
  "remaining_dof_after_connection": ["rotation_about_axis"],
  "fallback_reference": "CSYS_PART"
}
```


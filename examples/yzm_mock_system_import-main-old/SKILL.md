# 员工入职系统_import - Agent 使用指南

> **网络ID**: yzm_mock_system_import  
> **版本**:   

## 网络概览

### 核心对象

| 对象 | 文件路径 | 说明 |
|------|----------|------|
| 4444 | `object_types/44444.bkn` |  |
| 1 | `object_types/d6scnjmrp5plcj8ejjk0.bkn` |  |
| dddd | `object_types/dddd.bkn` |  |
| 部门 | `object_types/department.bkn` |  |
| 员工 | `object_types/employee.bkn` |  |
| 员工部门关系 | `object_types/relation.bkn` |  |

### 核心关系

| 关系 | 文件路径 | 说明 |
|------|----------|------|
| source_object_type_id | `relation_types/source_object_type_id.bkn` |  |

### 可用行动

| 行动 | 文件路径 | 说明 |
|------|----------|------|
| 1111 | `action_types/1111.bkn` |  |
| 222 | `action_types/222.bkn` |  |
| 2223 | `action_types/2223.bkn` |  |
| 44 | `action_types/44.bkn` |  |
| test0206 | `action_types/d62pdl8jijbh3srg26qg.bkn` |  |
| test-demo | `action_types/d62qc80jijbh3srg26rg.bkn` |  |
| del | `action_types/d6p330u1v4b3l62f0l00.bkn` |  |
| 新员工入职 | `action_types/new_job.bkn` |  |
| 新员工入职2 | `action_types/new_job2.bkn` |  |
| no | `action_types/no.bkn` |  |
| xxx | `action_types/xxx.bkn` | xxx |

## 目录结构

```
.
├── network.bkn
├── SKILL.md
├── CHECKSUM
├── object_types/
├── relation_types/
└── action_types/
```

## 使用建议

### 查询场景

1. **获取所有对象定义**
   - 查看 `object_types/` 目录下的文件

2. **查找关系定义**
   - 查看 `relation_types/` 目录下的文件

### 运维场景

1. **执行运维操作**
   - 查看 `action_types/` 目录下的行动定义
   - 了解触发条件和参数绑定

## 索引表

### 按类型索引

- **对象定义**: `object_types/`
- **关系定义**: `relation_types/`
- **行动定义**: `action_types/`

## 注意事项

1. 本网络由 BKN SDK 自动生成 SKILL.md
2. 所有定义遵循 BKN 规范
3. 使用 CHECKSUM 文件验证网络完整性

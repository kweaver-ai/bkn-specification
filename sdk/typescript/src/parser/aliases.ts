// Copyright The kweaver.ai Authors.
//
// Licensed under the Apache License, Version 2.0.
// See the LICENSE file in the project root for details.

/**
 * Column and section name aliases (English canonical <-> Chinese).
 */

export const COLUMN_ALIASES: Record<string, string> = {
  属性: "Property",
  显示名: "Display Name",
  显示名称: "Display Name",
  类型: "Type",
  约束: "Constraint",
  描述: "Description",
  说明: "Description",
  主键: "Primary Key",
  显示属性: "Display Key",
  索引: "Index",
  数据来源: "Data Source",
  名称: "Name",
  起点: "Source",
  终点: "Target",
  必须: "Required",
  起点属性: "Source Property",
  终点属性: "Target Property",
  参数: "Parameter",
  来源: "Source",
  绑定: "Binding",
  工具: "Tool ID",
  绑定对象: "Bound Object",
  行动类型: "Action Type",
  对象: "Object",
  检查: "Check",
  条件: "Condition",
  消息: "Message",
  表达式: "Expression",
  索引配置: "Index Config",
  影响说明: "Impact Description",
  端点: "Endpoint",
  凭据引用: "Secret Ref",
  管控对象: "Controlled Object",
  管控行动: "Controlled Action",
  风险等级: "Risk Level",
  策略: "Strategy",
  检查项: "Check Item",
};

export const SECTION_ALIASES: Record<string, string> = {
  连接定义: "Connection",
  数据来源: "Data Source",
  数据属性: "Data Properties",
  属性覆盖: "Property Override",
  逻辑属性: "Logic Properties",
  业务语义: "Business Semantics",
  关联定义: "Endpoints",
  映射规则: "Mapping Rules",
  映射视图: "Mapping View",
  起点映射: "Source Mapping",
  终点映射: "Target Mapping",
  绑定对象: "Bound Object",
  触发条件: "Trigger Condition",
  前置条件: "Pre-conditions",
  工具配置: "Tool Configuration",
  参数绑定: "Parameter Binding",
  调度配置: "Schedule",
  影响范围: "Scope of Impact",
  执行说明: "Execution Description",
  管控范围: "Control Scope",
  管控策略: "Control Strategy",
  前置检查: "Pre-checks",
  回滚方案: "Rollback Plan",
  审计要求: "Audit Requirements",
  Endpoint: "Endpoints",
  "Affect Object": "Scope of Impact", // compat: example drift
};

export function normalizeColumn(name: string): string {
  const trimmed = name.trim();
  return COLUMN_ALIASES[trimmed] ?? trimmed;
}

export function normalizeSection(name: string): string {
  const trimmed = name.trim();
  return SECTION_ALIASES[trimmed] ?? trimmed;
}

export function isYes(val: string): boolean {
  return val.trim().toUpperCase() === "YES";
}
// Copyright The kweaver.ai Authors.
//
// Licensed under the Apache License, Version 2.0.
// See the LICENSE file in the project root for details.

package bkn

import (
	"fmt"
	"strings"

	"gopkg.in/yaml.v3"
)

// SerializeBknNetwork Serializes BknNetwork to BKN format
func SerializeBknNetwork(doc *BknNetwork) string {
	fm := doc.BknNetworkFrontmatter
	var sb strings.Builder
	sb.WriteString("---\n")
	sb.WriteString("type: knowledge_network\n")
	sb.WriteString(fmt.Sprintf("id: %s\n", fm.ID))
	sb.WriteString(fmt.Sprintf("name: %s\n", fm.Name))
	sb.WriteString(fmt.Sprintf("tags: [%s]\n", strings.Join(fm.Tags, ", ")))

	if fm.Version != "" {
		sb.WriteString(fmt.Sprintf("version: %s\n", fm.Version))
	}
	if fm.Branch != "" {
		sb.WriteString(fmt.Sprintf("branch: %s\n", fm.Branch))
	}
	if fm.BusinessDomain != "" {
		sb.WriteString(fmt.Sprintf("business_domain: %s\n", fm.BusinessDomain))
	}
	sb.WriteString("---\n\n")

	sb.WriteString(fmt.Sprintf("# %s\n\n", fm.Name))
	if fm.Description != "" {
		sb.WriteString(fm.Description + "\n")
	}

	// Write Network Overview section
	sb.WriteString("\n## Network Overview\n\n")

	if len(doc.ObjectTypes) > 0 {
		var names []string
		for _, ot := range doc.ObjectTypes {
			names = append(names, ot.ID)
		}
		sb.WriteString(fmt.Sprintf("- **ObjectTypes** (object_types/): %s\n", strings.Join(names, ", ")))
	}
	if len(doc.RelationTypes) > 0 {
		var names []string
		for _, rt := range doc.RelationTypes {
			names = append(names, rt.ID)
		}
		sb.WriteString(fmt.Sprintf("- **RelationTypes** (relation_types/): %s\n", strings.Join(names, ", ")))
	}
	if len(doc.ActionTypes) > 0 {
		var names []string
		for _, at := range doc.ActionTypes {
			names = append(names, at.ID)
		}
		sb.WriteString(fmt.Sprintf("- **ActionTypes** (action_types/): %s\n", strings.Join(names, ", ")))
	}
	if len(doc.RiskTypes) > 0 {
		var names []string
		for _, rt := range doc.RiskTypes {
			names = append(names, rt.ID)
		}
		sb.WriteString(fmt.Sprintf("- **RiskTypes** (risk_types/): %s\n", strings.Join(names, ", ")))
	}
	if len(doc.ConceptGroups) > 0 {
		var names []string
		for _, cg := range doc.ConceptGroups {
			names = append(names, cg.ID)
		}
		sb.WriteString(fmt.Sprintf("- **ConceptGroups** (concept_groups/): %s\n", strings.Join(names, ", ")))
	}

	return sb.String()
}

// SerializeObjectType Serializes BknObjectType to BKN format
func SerializeObjectType(ot *BknObjectType) string {
	var sb strings.Builder
	sb.WriteString("---\n")
	sb.WriteString("type: object_type\n")
	sb.WriteString(fmt.Sprintf("id: %s\n", ot.ID))
	sb.WriteString(fmt.Sprintf("name: %s\n", ot.Name))
	sb.WriteString(fmt.Sprintf("tags: [%s]\n", strings.Join(ot.Tags, ", ")))
	sb.WriteString("---\n\n")

	sb.WriteString(fmt.Sprintf("## ObjectType: %s\n\n", ot.Name))
	if ot.Description != "" {
		sb.WriteString(ot.Description + "\n\n")
	}

	// Data Source
	sb.WriteString("### Data Source\n\n")
	sb.WriteString("| Type | ID | Name |\n")
	sb.WriteString("|------|-----|------|\n")
	if ot.DataSource != nil {
		sb.WriteString(fmt.Sprintf("| %s | %s | %s |\n",
			ot.DataSource.Type, ot.DataSource.ID, ot.DataSource.Name))
	}
	sb.WriteString("\n")

	// Data Properties
	sb.WriteString("### Data Properties\n\n")
	sb.WriteString("| Name | Display Name | Type | Description | Mapped Field |\n")
	sb.WriteString("|------|--------------|------|-------------|--------------|\n")
	if len(ot.DataProperties) > 0 {
		for _, dp := range ot.DataProperties {
			sb.WriteString(fmt.Sprintf("| %s | %s | %s | %s | %s |\n",
				dp.Name, dp.DisplayName, dp.Type, dp.Description, dp.MappedField))
		}
	}
	sb.WriteString("\n")

	// Logic Properties
	sb.WriteString("### Logic Properties\n\n")
	for _, lp := range ot.LogicProperties {
		sb.WriteString(fmt.Sprintf("#### %s\n\n", lp.Name))
		if lp.Type != "" {
			sb.WriteString(fmt.Sprintf("- **Type**: %s\n", lp.Type))
		}
		if lp.DataSource != nil {
			sb.WriteString(fmt.Sprintf("- **Source**: %s (%s)\n", lp.DataSource.Type, lp.DataSource.Name))
		}
		if lp.Description != "" {
			sb.WriteString(fmt.Sprintf("- **Description**: %s\n", lp.Description))
		}
		if len(lp.Parameters) > 0 {
			sb.WriteString("\n| Parameter | Type | Source | Binding | Description |\n")
			sb.WriteString("|-----------|------|--------|---------|-------------|\n")
			for _, p := range lp.Parameters {
				sb.WriteString(fmt.Sprintf("| %s | %s | %s | %s | %s |\n",
					p.Name, p.Type, p.Source, p.Operation, p.Description))
			}
		}
	}
	sb.WriteString("\n")

	// Keys section
	sb.WriteString("### Keys\n\n")
	sb.WriteString(fmt.Sprintf("Primary Key: %s\n", strings.Join(ot.PrimaryKeys, ", ")))
	sb.WriteString(fmt.Sprintf("Display Key: %s\n", ot.DisplayKey))
	sb.WriteString(fmt.Sprintf("Incremental Key: %s\n", ot.IncrementalKey))
	sb.WriteString("\n")

	return sb.String()
}

// SerializeRelationType Serializes BknRelationType to BKN format
func SerializeRelationType(rt *BknRelationType) string {
	var sb strings.Builder
	sb.WriteString("---\n")
	sb.WriteString("type: relation_type\n")
	sb.WriteString(fmt.Sprintf("id: %s\n", rt.ID))
	sb.WriteString(fmt.Sprintf("name: %s\n", rt.Name))
	sb.WriteString(fmt.Sprintf("tags: [%s]\n", strings.Join(rt.Tags, ", ")))
	sb.WriteString("---\n\n")

	sb.WriteString(fmt.Sprintf("## RelationType: %s\n\n", rt.Name))
	if rt.Description != "" {
		sb.WriteString(rt.Description + "\n\n")
	}

	// Endpoint
	sb.WriteString("### Endpoint\n\n")
	sb.WriteString("| Source | Target | Type |\n")
	sb.WriteString("|--------|--------|------|\n")
	sb.WriteString(fmt.Sprintf("| %s | %s | %s |\n\n", rt.Endpoint.Source, rt.Endpoint.Target, rt.Endpoint.Type))

	switch rt.Endpoint.Type {
	case "direct":
		// ### Mapping Rules — simple source→target property table
		sb.WriteString("### Mapping Rules\n\n")
		sb.WriteString("| Source Property | Target Property |\n")
		sb.WriteString("|-----------------|------------------|\n")
		if rules, ok := rt.MappingRules.(DirectMappingRule); ok {
			for _, r := range rules {
				sb.WriteString(fmt.Sprintf("| %s | %s |\n", r.SourceProperty, r.TargetProperty))
			}
		}
		sb.WriteString("\n")

	case "data_view":
		// ### Mapping View — backing data source reference
		sb.WriteString("### Mapping View\n\n")
		sb.WriteString("| Type | ID |\n")
		sb.WriteString("|------|-----|\n")
		if rules, ok := rt.MappingRules.(InDirectMappingRule); ok {
			if rules.BackingDataSource != nil {
				sb.WriteString(fmt.Sprintf("| %s | %s |\n", rules.BackingDataSource.Type, rules.BackingDataSource.ID))
			}
			sb.WriteString("\n")

			// ### Source Mapping — source property → view property
			sb.WriteString("### Source Mapping\n\n")
			sb.WriteString("| Source Property | View Property |\n")
			sb.WriteString("|-----------------|----------------|\n")
			for _, r := range rules.SourceMappingRules {
				sb.WriteString(fmt.Sprintf("| %s | %s |\n", r.SourceProperty, r.TargetProperty))
			}
			sb.WriteString("\n")

			// ### Target Mapping — view property → target property
			sb.WriteString("### Target Mapping\n\n")
			sb.WriteString("| View Property | Target Property |\n")
			sb.WriteString("|---------------|------------------|\n")
			for _, r := range rules.TargetMappingRules {
				sb.WriteString(fmt.Sprintf("| %s | %s |\n", r.SourceProperty, r.TargetProperty))
			}
			sb.WriteString("\n")
		} else {
			sb.WriteString("\n")
		}
	}

	return sb.String()
}

// SerializeActionType Serializes BknActionType to BKN format
func SerializeActionType(at *BknActionType) string {
	var sb strings.Builder
	sb.WriteString("---\n")
	sb.WriteString("type: action_type\n")
	sb.WriteString(fmt.Sprintf("id: %s\n", at.ID))
	sb.WriteString(fmt.Sprintf("name: %s\n", at.Name))
	sb.WriteString(fmt.Sprintf("tags: [%s]\n", strings.Join(at.Tags, ", ")))
	sb.WriteString(fmt.Sprintf("action_type: %s\n", at.ActionType))
	sb.WriteString("---\n\n")

	sb.WriteString(fmt.Sprintf("## ActionType: %s\n\n", at.Name))
	if at.Description != "" {
		sb.WriteString(at.Description + "\n\n")
	}

	// Bound Object
	sb.WriteString("### Bound Object\n\n")
	sb.WriteString("| Bound Object |\n")
	sb.WriteString("|--------------|\n")
	if at.BoundObject != "" {
		sb.WriteString(fmt.Sprintf("| %s |\n", at.BoundObject))
	}
	sb.WriteString("\n")

	// Affect Object
	sb.WriteString("### Affect Object\n\n")
	sb.WriteString("| Affect Object | Affect Description |\n")
	sb.WriteString("|---------------|--------------------|\n")
	if at.AffectObject != nil {
		sb.WriteString(fmt.Sprintf("| %s | %s |\n", at.AffectObject.ObjectType, at.AffectObject.Description))
	}
	sb.WriteString("\n")

	// Trigger Condition
	sb.WriteString("### Trigger Condition\n\n")
	if at.TriggerCondition != nil {
		sb.WriteString("```yaml\n")
		yamlContent, _ := yaml.Marshal(at.TriggerCondition)
		sb.Write(yamlContent)
		sb.WriteString("```\n")
	}
	sb.WriteString("\n")

	// Action Source
	sb.WriteString("### Action Source\n\n")
	sb.WriteString("| Type | BoxID | ToolID | McpID | ToolName |\n")
	sb.WriteString("|------|-------|--------|-------|----------|\n")
	if at.ActionSource != nil && at.ActionSource.Type != "" {
		sb.WriteString(fmt.Sprintf("| %s | %s | %s | %s | %s |\n",
			at.ActionSource.Type, at.ActionSource.BoxID, at.ActionSource.ToolID,
			at.ActionSource.McpID, at.ActionSource.ToolName))
	}
	sb.WriteString("\n")

	// Parameter Binding
	sb.WriteString("### Parameter Binding\n\n")
	sb.WriteString("| Name | Type | Source | Operation | ValueFrom | Value | Description |\n")
	sb.WriteString("|------|------|--------|-----------|-----------|-------|-------------|\n")
	for _, p := range at.Parameters {
		v := p.Value
		if v == nil {
			v = ""
		}
		sb.WriteString(fmt.Sprintf("| %s | %s | %s | %s | %s | %s | %s |\n",
			p.Name, p.Type, p.Source, p.Operation, p.ValueFrom, v, p.Description))
	}
	sb.WriteString("\n")

	// Schedule
	sb.WriteString("### Schedule\n\n")
	sb.WriteString("| Type | Expression |\n")
	sb.WriteString("|------|------------|\n")
	if at.Schedule != nil && at.Schedule.Type != "" {
		sb.WriteString(fmt.Sprintf("| %s | %s |\n", at.Schedule.Type, at.Schedule.Expression))
	}
	sb.WriteString("\n")

	return sb.String()
}

// SerializeRiskType Serializes BknRiskType to BKN format
func SerializeRiskType(rt *BknRiskType) string {
	var sb strings.Builder
	sb.WriteString("---\n")
	sb.WriteString("type: risk_type\n")
	sb.WriteString(fmt.Sprintf("id: %s\n", rt.ID))
	sb.WriteString(fmt.Sprintf("name: %s\n", rt.Name))
	sb.WriteString(fmt.Sprintf("tags: [%s]\n", strings.Join(rt.Tags, ", ")))
	sb.WriteString("---\n\n")

	sb.WriteString(fmt.Sprintf("## RiskType: %s\n\n", rt.Name))
	if rt.Description != "" {
		sb.WriteString(rt.Description + "\n\n")
	}

	sb.WriteString("### Control Scope\n\n")
	if rt.ControlScope != "" {
		sb.WriteString(rt.ControlScope)
		sb.WriteString("\n")
	}
	sb.WriteString("\n")

	sb.WriteString("### Control Policy\n\n")
	if rt.ControlPolicy != "" {
		sb.WriteString(rt.ControlPolicy)
		sb.WriteString("\n")
	}
	sb.WriteString("\n")

	sb.WriteString("### Rollback Plan\n\n")
	if rt.RollbackPlan != "" {
		sb.WriteString(rt.RollbackPlan)
		sb.WriteString("\n")
	}
	sb.WriteString("\n")

	sb.WriteString("### Audit Requirements\n\n")
	if rt.AuditRequirements != "" {
		sb.WriteString(rt.AuditRequirements)
		sb.WriteString("\n")
	}
	sb.WriteString("\n")

	return sb.String()
}

// SerializeConceptGroup Serializes BknConceptGroup to BKN format
func SerializeConceptGroup(cg *BknConceptGroup) string {
	var sb strings.Builder
	sb.WriteString("---\n")
	sb.WriteString("type: concept_group\n")
	sb.WriteString(fmt.Sprintf("id: %s\n", cg.ID))
	sb.WriteString(fmt.Sprintf("name: %s\n", cg.Name))
	sb.WriteString(fmt.Sprintf("tags: [%s]\n", strings.Join(cg.Tags, ", ")))
	sb.WriteString("---\n\n")

	sb.WriteString(fmt.Sprintf("## ConceptGroup: %s\n\n", cg.Name))
	if cg.Description != "" {
		sb.WriteString(cg.Description + "\n\n")
	}

	return sb.String()
}

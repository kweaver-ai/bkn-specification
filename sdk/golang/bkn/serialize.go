// Copyright The kweaver.ai Authors.
//
// Licensed under the Apache License, Version 2.0.
// See the LICENSE file in the project root for details.

package bkn

import (
	"bytes"
	"fmt"
	"sort"
	"strings"

	"gopkg.in/yaml.v3"
)

// encodeYAMLBlock encodes v to YAML and wraps it in a ```yaml code fence.
func encodeYAMLBlock(v any) string {
	var buf bytes.Buffer
	enc := yaml.NewEncoder(&buf)
	enc.SetIndent(2)
	_ = enc.Encode(v)
	_ = enc.Close()
	return "```yaml\n" + buf.String() + "```\n"
}

// SerializeBknNetwork Serializes BknNetwork to BKN format
func SerializeBknNetwork(doc *BknNetwork) string {
	var sb strings.Builder
	sb.WriteString("---\n")
	sb.WriteString("type: knowledge_network\n")
	sb.WriteString(fmt.Sprintf("id: %s\n", doc.ID))
	sb.WriteString(fmt.Sprintf("name: %s\n", doc.Name))
	sb.WriteString(fmt.Sprintf("tags: [%s]\n", strings.Join(doc.Tags, ", ")))

	if doc.Version != "" {
		sb.WriteString(fmt.Sprintf("version: %s\n", doc.Version))
	}
	if doc.Branch != "" {
		sb.WriteString(fmt.Sprintf("branch: %s\n", doc.Branch))
	}
	if doc.BusinessDomain != "" {
		sb.WriteString(fmt.Sprintf("business_domain: %s\n", doc.BusinessDomain))
	}
	sb.WriteString("---\n\n")

	sb.WriteString(fmt.Sprintf("# %s\n\n", doc.Name))
	if doc.Description != "" {
		sb.WriteString(doc.Description + "\n")
	}

	// Network Overview
	sb.WriteString("\n## Network Overview\n")

	sb.WriteString("\n### Object Types\n\n")
	sb.WriteString("| ID | Name | File Path | Description |\n")
	sb.WriteString("|----|------|-----------|-------------|\n")
	if len(doc.ObjectTypes) > 0 {
		sort.Slice(doc.ObjectTypes, func(i, j int) bool { return doc.ObjectTypes[i].ID < doc.ObjectTypes[j].ID })
		for _, ot := range doc.ObjectTypes {
			fmt.Fprintf(&sb, "| %s | %s | `object_types/%s.bkn` | %s |\n", ot.ID, ot.Name, ot.ID, ot.Summary)
		}
	}

	sb.WriteString("\n### Relation Types\n\n")
	sb.WriteString("| ID | Name | File Path | Description |\n")
	sb.WriteString("|----|------|-----------|-------------|\n")
	if len(doc.RelationTypes) > 0 {
		sort.Slice(doc.RelationTypes, func(i, j int) bool { return doc.RelationTypes[i].ID < doc.RelationTypes[j].ID })
		for _, rt := range doc.RelationTypes {
			fmt.Fprintf(&sb, "| %s | %s | `relation_types/%s.bkn` | %s |\n", rt.ID, rt.Name, rt.ID, rt.Summary)
		}
	}

	sb.WriteString("\n### Action Types\n\n")
	sb.WriteString("| ID | Name | File Path | Description |\n")
	sb.WriteString("|----|------|-----------|-------------|\n")
	if len(doc.ActionTypes) > 0 {
		sort.Slice(doc.ActionTypes, func(i, j int) bool { return doc.ActionTypes[i].ID < doc.ActionTypes[j].ID })
		for _, at := range doc.ActionTypes {
			fmt.Fprintf(&sb, "| %s | %s | `action_types/%s.bkn` | %s |\n", at.ID, at.Name, at.ID, at.Summary)
		}
	}

	sb.WriteString("\n### Risk Types\n\n")
	sb.WriteString("| ID | Name | File Path | Description |\n")
	sb.WriteString("|----|------|-----------|-------------|\n")
	if len(doc.RiskTypes) > 0 {
		sort.Slice(doc.RiskTypes, func(i, j int) bool { return doc.RiskTypes[i].ID < doc.RiskTypes[j].ID })
		for _, rt := range doc.RiskTypes {
			fmt.Fprintf(&sb, "| %s | %s | `risk_types/%s.bkn` | %s |\n", rt.ID, rt.Name, rt.ID, rt.Summary)
		}
	}

	sb.WriteString("\n### Concept Groups\n\n")
	sb.WriteString("| ID | Name | File Path | Description |\n")
	sb.WriteString("|----|------|-----------|-------------|\n")
	if len(doc.ConceptGroups) > 0 {
		sort.Slice(doc.ConceptGroups, func(i, j int) bool { return doc.ConceptGroups[i].ID < doc.ConceptGroups[j].ID })
		for _, cg := range doc.ConceptGroups {
			fmt.Fprintf(&sb, "| %s | %s | `concept_groups/%s.bkn` | %s |\n", cg.ID, cg.Name, cg.ID, cg.Summary)
		}
	}

	// Directory Structure — full tree with file listings
	type dirEntry struct {
		dir   string
		files []string
	}
	var dirs []dirEntry
	if len(doc.ObjectTypes) > 0 {
		files := make([]string, len(doc.ObjectTypes))
		for i, ot := range doc.ObjectTypes {
			files[i] = ot.ID + ".bkn"
		}
		dirs = append(dirs, dirEntry{"object_types", files})
	}
	if len(doc.RelationTypes) > 0 {
		files := make([]string, len(doc.RelationTypes))
		for i, rt := range doc.RelationTypes {
			files[i] = rt.ID + ".bkn"
		}
		dirs = append(dirs, dirEntry{"relation_types", files})
	}
	if len(doc.ActionTypes) > 0 {
		files := make([]string, len(doc.ActionTypes))
		for i, at := range doc.ActionTypes {
			files[i] = at.ID + ".bkn"
		}
		dirs = append(dirs, dirEntry{"action_types", files})
	}
	if len(doc.RiskTypes) > 0 {
		files := make([]string, len(doc.RiskTypes))
		for i, rt := range doc.RiskTypes {
			files[i] = rt.ID + ".bkn"
		}
		dirs = append(dirs, dirEntry{"risk_types", files})
	}
	if len(doc.ConceptGroups) > 0 {
		files := make([]string, len(doc.ConceptGroups))
		for i, cg := range doc.ConceptGroups {
			files[i] = cg.ID + ".bkn"
		}
		dirs = append(dirs, dirEntry{"concept_groups", files})
	}

	sb.WriteString("\n## Directory Structure\n\n```\n.\n├── network.bkn\n├── SKILL.md\n├── CHECKSUM\n")
	for i, d := range dirs {
		isLastDir := i == len(dirs)-1
		dirPrefix, childPrefix := "├── ", "│   "
		if isLastDir {
			dirPrefix, childPrefix = "└── ", "    "
		}
		fmt.Fprintf(&sb, "%s%s/\n", dirPrefix, d.dir)
		for j, f := range d.files {
			if j == len(d.files)-1 {
				fmt.Fprintf(&sb, "%s└── %s\n", childPrefix, f)
			} else {
				fmt.Fprintf(&sb, "%s├── %s\n", childPrefix, f)
			}
		}
	}
	sb.WriteString("```\n")

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
	sb.WriteString("|------|----|------|\n")
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

		// Meta table
		sb.WriteString("**Meta**\n\n")
		sb.WriteString("| Display Name | Type | Description |\n")
		sb.WriteString("|--------------|------|-------------|\n")
		sb.WriteString(fmt.Sprintf("| %s | %s | %s |\n\n", lp.DisplayName, lp.Type, lp.Description))

		// Source table
		sb.WriteString("**Source**\n\n")
		sb.WriteString("| Source Type | Source ID | Source Name |\n")
		sb.WriteString("|-------------|-----------|-------------|\n")
		if lp.DataSource != nil {
			sb.WriteString(fmt.Sprintf("| %s | %s | %s |\n", lp.DataSource.Type, lp.DataSource.ID, lp.DataSource.Name))
		}
		sb.WriteString("\n")

		// Parameter table
		sb.WriteString("**Parameters**\n\n")
		sb.WriteString("| Name | Type | Source | Operation | ValueFrom | Value | Description |\n")
		sb.WriteString("|------|------|--------|-----------|-----------|-------|-------------|\n")
		for _, p := range lp.Parameters {
			v := ""
			if p.Value != nil {
				v = fmt.Sprintf("%v", p.Value)
			}
			sb.WriteString(fmt.Sprintf("| %s | %s | %s | %s | %s | %s | %s |\n",
				p.Name, p.Type, p.Source, p.Operation, p.ValueFrom, v, p.Description))
		}
		sb.WriteString("\n")

		// Analysis Dims table
		sb.WriteString("**Analysis Dimensions**\n\n")
		sb.WriteString("| Name | Display Name | Type | Description |\n")
		sb.WriteString("|------|--------------|------|-------------|\n")
		for _, d := range lp.AnalysisDims {
			sb.WriteString(fmt.Sprintf("| %s | %s | %s | %s |\n", d.Name, d.DisplayName, d.Type, d.Description))
		}
		sb.WriteString("\n")
	}
	sb.WriteString("\n")

	// Keys section
	sb.WriteString("### Keys\n\n")
	sb.WriteString(fmt.Sprintf("Primary Keys: %s\n", strings.Join(ot.PrimaryKeys, ", ")))
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
	case RELATION_MAPPING_TYPE_DIRECT:
		// ### Mapping Rules — simple source→target property table
		sb.WriteString("### Mapping Rules\n\n")
		sb.WriteString("| Source Property | Target Property |\n")
		sb.WriteString("|-----------------|-----------------|\n")
		if rules, ok := rt.MappingRules.(DirectMappingRule); ok {
			for _, r := range rules {
				sb.WriteString(fmt.Sprintf("| %s | %s |\n", r.SourceProperty, r.TargetProperty))
			}
		}
		sb.WriteString("\n")

	case RELATION_MAPPING_TYPE_DATA_VIEW:
		// ### Mapping View — backing data source reference
		sb.WriteString("### Mapping View\n\n")
		sb.WriteString("| Type | ID |\n")
		sb.WriteString("|------|----|\n")
		if rules, ok := rt.MappingRules.(*InDirectMappingRule); ok {
			if rules.BackingDataSource != nil {
				sb.WriteString(fmt.Sprintf("| %s | %s |\n", rules.BackingDataSource.Type, rules.BackingDataSource.ID))
			}
			sb.WriteString("\n")

			// ### Source Mapping — source property → view property
			sb.WriteString("### Source Mapping\n\n")
			sb.WriteString("| Source Property | View Property |\n")
			sb.WriteString("|-----------------|---------------|\n")
			for _, r := range rules.SourceMappingRules {
				sb.WriteString(fmt.Sprintf("| %s | %s |\n", r.SourceProperty, r.TargetProperty))
			}
			sb.WriteString("\n")

			// ### Target Mapping — view property → target property
			sb.WriteString("### Target Mapping\n\n")
			sb.WriteString("| View Property | Target Property |\n")
			sb.WriteString("|---------------|-----------------|\n")
			for _, r := range rules.TargetMappingRules {
				sb.WriteString(fmt.Sprintf("| %s | %s |\n", r.SourceProperty, r.TargetProperty))
			}
			sb.WriteString("\n")
		} else {
			sb.WriteString("\n")
		}

	case RELATION_MAPPING_TYPE_FILTERED_CROSS_JOIN:
		if fcj, ok := rt.MappingRules.(*FilteredCrossJoinMapping); ok {
			sb.WriteString("### Source Condition\n\n")
			if fcj.SourceCondition != nil {
				sb.WriteString(encodeYAMLBlock(fcj.SourceCondition))
			}
			sb.WriteString("\n")

			sb.WriteString("### Target Condition\n\n")
			if fcj.TargetCondition != nil {
				sb.WriteString(encodeYAMLBlock(fcj.TargetCondition))
			}
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
		sb.WriteString(encodeYAMLBlock(at.TriggerCondition))
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

	return sb.String()
}

// SerializeConceptGroup Serializes BknConceptGroup to BKN format.
// otIndex maps ObjectType ID → *BknObjectType for Name/Description lookup.
func SerializeConceptGroup(cg *BknConceptGroup, otIndex map[string]*BknObjectType) string {
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

	sb.WriteString("### Object Types\n\n")
	sb.WriteString("| ID | Name | Description |\n")
	sb.WriteString("|----|------|-------------|\n")
	if len(cg.ObjectTypes) > 0 {
		ids := append([]string(nil), cg.ObjectTypes...)
		sort.Strings(ids)
		for _, id := range ids {
			name, desc := id, ""
			if ot, ok := otIndex[id]; ok {
				name = ot.Name
				desc = ot.Summary
			}
			sb.WriteString(fmt.Sprintf("| %s | %s | %s |\n", id, name, desc))
		}
	}
	sb.WriteString("\n")

	return sb.String()
}

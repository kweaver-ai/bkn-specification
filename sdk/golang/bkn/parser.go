// Copyright The kweaver.ai Authors.
//
// Licensed under the Apache License, Version 2.0.
// See the LICENSE file in the project root for details.

package bkn

import (
	"fmt"
	"regexp"
	"strings"

	"gopkg.in/yaml.v3"
)

var sectionRE = regexp.MustCompile(`(?m)^###\s+(.+)$`)
var subSectionRE = regexp.MustCompile(`(?m)^####\s+(.+)$`)
var inlineMetaRE = regexp.MustCompile(`(?m)^-\s+\*\*(\w+)\*\*:\s*(.+)$`)
var h1HeadingRE = regexp.MustCompile(`(?m)^#\s+(.+)$`)
var h2HeadingRE = regexp.MustCompile(`(?m)^##\s+(.+)$`)
var tableSepRE = regexp.MustCompile(`^\|?[\s:*-]+(\|[\s:*-]+)*\|?$`)
var yamlBlockRE = regexp.MustCompile("(?s)```yaml\\s*\\n(.+?)```")

// extractBodyDescription extracts the description text from the body.
// For network files (with # heading): extracts between # and ##
// For other files (with ## heading): extracts between ## and ###
func extractBodyDescription(text string) string {
	_, body := splitFrontmatter(text)

	// Check if there's a # heading (H1) - network file format
	h1Loc := h1HeadingRE.FindStringIndex(body)
	if h1Loc != nil {
		// Start after the # heading line
		rest := body[h1Loc[1]:]
		// Find the first ## section (H2) - this marks the end of description
		secLoc := h2HeadingRE.FindStringIndex(rest)
		if secLoc == nil {
			return strings.TrimSpace(rest)
		}
		return strings.TrimSpace(rest[:secLoc[0]])
	}

	// Check if there's a ## heading (H2) - object_type/relation_type etc. format
	h2Loc := h2HeadingRE.FindStringIndex(body)
	if h2Loc != nil {
		// Start after the ## heading line
		rest := body[h2Loc[1]:]
		// Find the first ### section - this marks the end of description
		secLoc := sectionRE.FindStringIndex(rest)
		if secLoc == nil {
			return strings.TrimSpace(rest)
		}
		return strings.TrimSpace(rest[:secLoc[0]])
	}

	return ""
}

func splitFrontmatter(text string) (fm string, body string) {
	text = strings.TrimPrefix(text, "\ufeff")
	if !strings.HasPrefix(text, "---") {
		return "", text
	}
	end := strings.Index(text[3:], "\n---")
	if end == -1 {
		return "", text
	}
	end += 3
	idx := strings.Index(text[end+3:], "\n")
	if idx == -1 {
		return strings.TrimSpace(text[3:end]), ""
	}
	fm = strings.TrimSpace(text[3:end])
	body = text[end+4+idx:]
	return fm, body
}

func splitRow(row string) []string {
	row = strings.TrimSpace(row)
	row = strings.TrimPrefix(row, "|")
	row = strings.TrimSuffix(row, "|")
	parts := strings.Split(row, "|")
	for i := range parts {
		parts[i] = strings.TrimSpace(parts[i])
	}
	return parts
}

func parseTable(lines []string) []map[string]string {
	var tableLines []string
	for _, line := range lines {
		s := strings.TrimSpace(line)
		if strings.HasPrefix(s, "|") {
			tableLines = append(tableLines, s)
		} else if len(tableLines) > 0 {
			break
		}
	}
	if len(tableLines) < 2 {
		return nil
	}
	headers := splitRow(tableLines[0])
	sepLine := strings.TrimSpace(tableLines[1])
	dataStart := 2
	if !tableSepRE.MatchString(sepLine) {
		dataStart = 1
	}
	var rows []map[string]string
	for _, line := range tableLines[dataStart:] {
		cells := splitRow(line)
		row := make(map[string]string)
		for i, h := range headers {
			if i < len(cells) {
				row[h] = cells[i]
			} else {
				row[h] = ""
			}
		}
		rows = append(rows, row)
	}
	return rows
}

func extractSections(body string, level string) map[string]string {
	var re *regexp.Regexp
	if level == "###" {
		re = sectionRE
	} else {
		re = subSectionRE
	}
	matches := re.FindAllStringSubmatchIndex(body, -1)
	sections := make(map[string]string)
	for i, m := range matches {
		title := strings.TrimSpace(body[m[2]:m[3]])
		start := m[1]
		end := len(body)
		if i+1 < len(matches) {
			end = matches[i+1][0]
		}
		sections[title] = strings.TrimSpace(body[start:end])
	}
	return sections
}

func parseDataSource(sectionText string) *ResourceInfo {
	rows := parseTable(strings.Split(sectionText, "\n"))
	if len(rows) == 0 {
		return nil
	}
	r := rows[0]
	return &ResourceInfo{
		Type: r["Type"],
		ID:   r["ID"],
		Name: r["Name"],
	}
}

func parseDataProperties(sectionText string) []*DataProperty {
	rows := parseTable(strings.Split(sectionText, "\n"))
	var props []*DataProperty
	for _, row := range rows {
		props = append(props, &DataProperty{
			Name:        row["Name"],
			DisplayName: row["Display Name"],
			Type:        row["Type"],
			Description: row["Description"],
			MappedField: row["Mapped Field"],
		})
	}
	return props
}

func parseLogicProperties(sectionText string) []*LogicProperty {
	// Sub-section format: #### name + inline metadata + parameter table
	subSections := extractSections(sectionText, "####")
	if len(subSections) > 0 {
		// Use ordered extraction to preserve sub-section order
		matches := subSectionRE.FindAllStringSubmatchIndex(sectionText, -1)
		var props []*LogicProperty
		for i, m := range matches {
			name := strings.TrimSpace(sectionText[m[2]:m[3]])
			start := m[1]
			end := len(sectionText)
			if i+1 < len(matches) {
				end = matches[i+1][0]
			}
			content := strings.TrimSpace(sectionText[start:end])
			props = append(props, parseLogicPropertySubSection(name, content))
		}
		return props
	}

	// Flat table format
	rows := parseTable(strings.Split(sectionText, "\n"))
	var props []*LogicProperty
	for _, row := range rows {
		props = append(props, &LogicProperty{
			Name:        row["Name"],
			DisplayName: row["Display Name"],
			Type:        row["Type"],
			Description: row["Description"],
		})
	}
	return props
}

func parseLogicPropertySubSection(name, content string) *LogicProperty {
	prop := &LogicProperty{Name: name}

	for _, line := range strings.Split(content, "\n") {
		matches := inlineMetaRE.FindStringSubmatch(strings.TrimSpace(line))
		if len(matches) == 3 {
			val := strings.TrimSpace(matches[2])
			switch matches[1] {
			case "Display":
				prop.DisplayName = val
			case "Type":
				prop.Type = val
			case "Source":
				prop.DataSource = parseInlineSource(val)
			case "Description":
				prop.Description = val
			}
		}
	}

	// Parse parameter table
	rows := parseTable(strings.Split(content, "\n"))
	for _, row := range rows {
		prop.Parameters = append(prop.Parameters, Parameter{
			Name:        row["Parameter"],
			Type:        row["Type"],
			Source:      row["Source"],
			ValueFrom:   row["Binding"],
			Description: row["Description"],
		})
	}

	return prop
}

// parseInlineSource parses "name (type)" format, e.g. "bom_tree_builder (operator)"
func parseInlineSource(val string) *ResourceInfo {
	if idx := strings.Index(val, "("); idx > 0 {
		name := strings.TrimSpace(val[:idx])
		typePart := strings.TrimSuffix(strings.TrimSpace(val[idx+1:]), ")")
		return &ResourceInfo{ID: name, Name: name, Type: typePart}
	}
	return &ResourceInfo{ID: val, Name: val}
}

func parseKeys(sectionText string) (pks []string, dk string, ik string) {
	for _, line := range strings.Split(sectionText, "\n") {
		trimmed := strings.TrimSpace(line)
		if after, ok := strings.CutPrefix(trimmed, "Primary Key:"); ok {
			val := strings.TrimSpace(after)
			if val != "" {
				pks = strings.Split(val, ",")
				for i := range pks {
					pks[i] = strings.TrimSpace(pks[i])
				}
			}
		} else if after, ok := strings.CutPrefix(trimmed, "Primary Keys:"); ok {
			val := strings.TrimSpace(after)
			if val != "" {
				pks = strings.Split(val, ",")
				for i := range pks {
					pks[i] = strings.TrimSpace(pks[i])
				}
			}
		} else if after, ok := strings.CutPrefix(trimmed, "Display Key:"); ok {
			dk = strings.TrimSpace(after)
		} else if after, ok := strings.CutPrefix(trimmed, "Incremental Key:"); ok {
			ik = strings.TrimSpace(after)
		}
	}
	return pks, dk, ik
}

// ParseFrontmatter parses the YAML frontmatter of a .bkn file.
func ParseFrontmatter(text string) (map[string]any, error) {
	fmStr, _ := splitFrontmatter(text)
	if fmStr == "" {
		return map[string]any{}, nil
	}
	var data map[string]any
	if err := yaml.Unmarshal([]byte(fmStr), &data); err != nil {
		return nil, err
	}
	if data == nil {
		data = make(map[string]any)
	}

	return data, nil
}

func strVal(m map[string]any, key string) string {
	if v, ok := m[key]; ok && v != nil {
		return fmt.Sprint(v)
	}
	return ""
}

// strSliceVal safely extracts a string slice from a map value.
// YAML unmarshals arrays as []interface{}, so we need to convert each element.
func strSliceVal(m map[string]any, key string) []string {
	if v, ok := m[key]; ok && v != nil {
		switch val := v.(type) {
		case []string:
			return val
		case []interface{}:
			result := make([]string, 0, len(val))
			for _, item := range val {
				if item != nil {
					result = append(result, fmt.Sprint(item))
				}
			}
			return result
		case string:
			// Handle single string as single-element slice
			return []string{val}
		}
	}
	return nil
}

// ParseNetworkFile parses a network.bkn file (type: network).
// Network files contain only frontmatter, no body definitions.
func ParseNetworkFile(text string, sourcePath string) (*BknNetwork, error) {
	fmData, err := ParseFrontmatter(text)
	if err != nil {
		return nil, err
	}

	// Validate required fields
	if strVal(fmData, "type") == "" {
		return nil, fmt.Errorf("missing required field 'type' in network.bkn frontmatter")
	}
	if strVal(fmData, "id") == "" {
		return nil, fmt.Errorf("missing required field 'id' in network.bkn frontmatter")
	}

	network := &BknNetwork{
		BknNetworkFrontmatter: BknNetworkFrontmatter{
			Type:           strVal(fmData, "type"),
			ID:             strVal(fmData, "id"),
			Name:           strVal(fmData, "name"),
			Tags:           strSliceVal(fmData, "tags"),
			Description:    extractBodyDescription(text),
			Version:        strVal(fmData, "version"),
			Branch:         strVal(fmData, "branch"),
			BusinessDomain: strVal(fmData, "business_domain"),
		},
		RawContent: text,
	}

	return network, nil
}

// ParseObjectTypeFile parses an object_type definition file.
func ParseObjectTypeFile(text string, sourcePath string) (*BknObjectType, error) {
	fmData, err := ParseFrontmatter(text)
	if err != nil {
		return nil, err
	}

	obj := &BknObjectType{
		BknObjectTypeFrontmatter: BknObjectTypeFrontmatter{
			Type:        "object_type",
			ID:          strVal(fmData, "id"),
			Name:        strVal(fmData, "name"),
			Tags:        strSliceVal(fmData, "tags"),
			Description: extractBodyDescription(text),
		},
		RawContent: text,
	}

	sections := extractSections(text, "###")
	if s, ok := sections["Data Source"]; ok {
		obj.DataSource = parseDataSource(s)
	}
	if s, ok := sections["Data Properties"]; ok {
		obj.DataProperties = parseDataProperties(s)
	}
	if s, ok := sections["Logic Properties"]; ok {
		obj.LogicProperties = parseLogicProperties(s)
	}
	if s, ok := sections["Keys"]; ok {
		pks, dk, ik := parseKeys(s)
		obj.PrimaryKeys = pks
		obj.DisplayKey = dk
		obj.IncrementalKey = ik
	}

	return obj, nil
}

// ParseRelationTypeFile parses a relation_type definition file.
func ParseRelationTypeFile(text string, sourcePath string) (*BknRelationType, error) {
	fmData, err := ParseFrontmatter(text)
	if err != nil {
		return nil, err
	}

	rel := &BknRelationType{
		BknRelationTypeFrontmatter: BknRelationTypeFrontmatter{
			Type:        "relation_type",
			ID:          strVal(fmData, "id"),
			Name:        strVal(fmData, "name"),
			Tags:        strSliceVal(fmData, "tags"),
			Description: extractBodyDescription(text),
		},
		RawContent: text,
	}

	sections := extractSections(text, "###")

	if s, ok := sections["Endpoint"]; ok {
		rows := parseTable(strings.Split(s, "\n"))
		if len(rows) > 0 {
			row := rows[0]
			rel.Endpoint = Endpoint{
				Source: row["Source"],
				Target: row["Target"],
				Type:   row["Type"],
			}
		}
	}

	switch rel.Endpoint.Type {
	case "direct":
		if s, ok := sections["Mapping Rules"]; ok {
			rows := parseTable(strings.Split(s, "\n"))
			var rules []MappingRule
			for _, row := range rows {
				sp, tp := row["Source Property"], row["Target Property"]
				if sp != "" || tp != "" {
					rules = append(rules, MappingRule{SourceProperty: sp, TargetProperty: tp})
				}
			}
			rel.MappingRules = DirectMappingRule(rules)
		}
	case "data_view":
		indirect := InDirectMappingRule{}
		if s, ok := sections["Mapping View"]; ok {
			rows := parseTable(strings.Split(s, "\n"))
			if len(rows) > 0 {
				indirect.BackingDataSource = &ResourceInfo{
					Type: rows[0]["Type"],
					ID:   rows[0]["ID"],
				}
			}
		}
		if s, ok := sections["Source Mapping"]; ok {
			rows := parseTable(strings.Split(s, "\n"))
			for _, row := range rows {
				sp, vp := row["Source Property"], row["View Property"]
				if sp != "" || vp != "" {
					indirect.SourceMappingRules = append(indirect.SourceMappingRules, MappingRule{SourceProperty: sp, TargetProperty: vp})
				}
			}
		}
		if s, ok := sections["Target Mapping"]; ok {
			rows := parseTable(strings.Split(s, "\n"))
			for _, row := range rows {
				vp, tp := row["View Property"], row["Target Property"]
				if vp != "" || tp != "" {
					indirect.TargetMappingRules = append(indirect.TargetMappingRules, MappingRule{SourceProperty: vp, TargetProperty: tp})
				}
			}
		}
		rel.MappingRules = indirect
	}

	return rel, nil
}

// ParseActionTypeFile parses an action_type definition file.
func ParseActionTypeFile(text string, sourcePath string) (*BknActionType, error) {
	fmData, err := ParseFrontmatter(text)
	if err != nil {
		return nil, err
	}

	act := &BknActionType{
		BknActionTypeFrontmatter: BknActionTypeFrontmatter{
			Type:        "action_type",
			ID:          strVal(fmData, "id"),
			Name:        strVal(fmData, "name"),
			Tags:        strSliceVal(fmData, "tags"),
			ActionType:  strVal(fmData, "action_type"),
			Description: extractBodyDescription(text),
		},
		RawContent: text,
	}

	sections := extractSections(text, "###")

	if s, ok := sections["Bound Object"]; ok {
		act.BoundObject = parseBoundObject(s)
	}
	if s, ok := sections["Affect Object"]; ok {
		act.AffectObject = parseAffectObject(s)
	}
	if s, ok := sections["Trigger Condition"]; ok {
		act.TriggerCondition = parseTriggerCondition(s)
	}
	if s, ok := sections["Action Source"]; ok {
		act.ActionSource = parseActionSource(s)
	}
	if s, ok := sections["Parameter Binding"]; ok {
		act.Parameters = parseParameterBinding(s)
	}
	if s, ok := sections["Schedule"]; ok {
		act.Schedule = parseSchedule(s)
	}

	return act, nil
}

// parseBoundObject parses the bound object section.
func parseBoundObject(sectionText string) (boundObject string) {
	rows := parseTable(strings.Split(sectionText, "\n"))
	if len(rows) == 0 {
		return ""
	}
	r := rows[0]
	return r["Bound Object"]
}

// parseAffectObject parses the affect object section.
func parseAffectObject(sectionText string) (affectObject *ActionAffect) {
	rows := parseTable(strings.Split(sectionText, "\n"))
	if len(rows) == 0 {
		return nil
	}
	r := rows[0]
	affectObject = &ActionAffect{
		ObjectType:  r["Affect Object"],
		Description: r["Affect Description"],
	}
	return affectObject
}

// parseTriggerCondition parses the trigger condition from YAML code block.
func parseTriggerCondition(sectionText string) *CondCfg {
	// Extract YAML content from ```yaml ... ``` block
	matches := yamlBlockRE.FindStringSubmatch(sectionText)
	if len(matches) < 2 {
		return nil
	}

	yamlContent := matches[1]

	var cond CondCfg
	if err := yaml.Unmarshal([]byte(yamlContent), &cond); err != nil {
		return nil
	}
	return &cond
}

// parseParameterBinding parses the parameter binding table.
func parseParameterBinding(sectionText string) []Parameter {
	rows := parseTable(strings.Split(sectionText, "\n"))
	var params []Parameter
	for _, row := range rows {
		param := Parameter{
			Name:        row["Name"],
			Type:        row["Type"],
			Source:      row["Source"],
			Operation:   row["Operation"],
			ValueFrom:   row["ValueFrom"],
			Value:       row["Value"],
			Description: row["Description"],
		}
		params = append(params, param)
	}
	return params
}

// parseActionSource parses the action source table.
func parseActionSource(sectionText string) *ActionSource {
	rows := parseTable(strings.Split(sectionText, "\n"))
	if len(rows) == 0 {
		return nil
	}
	r := rows[0]

	actSrc := &ActionSource{
		Type: r["Type"],
	}
	switch actSrc.Type {
	case "tool":
		actSrc.BoxID = r["BoxID"]
		actSrc.ToolID = r["ToolID"]
	case "mcp":
		actSrc.McpID = r["McpID"]
		actSrc.ToolName = r["ToolName"]
	}

	return actSrc
}

// parseSchedule parses the schedule table.
func parseSchedule(sectionText string) *Schedule {
	rows := parseTable(strings.Split(sectionText, "\n"))
	if len(rows) == 0 {
		return nil
	}
	r := rows[0]
	return &Schedule{
		Type:       r["Type"],
		Expression: r["Expression"],
	}
}

// ParseRiskTypeFile parses a risk_type definition file.
func ParseRiskTypeFile(text string, sourcePath string) (*BknRiskType, error) {
	fmData, err := ParseFrontmatter(text)
	if err != nil {
		return nil, err
	}

	risk := &BknRiskType{
		BknRiskTypeFrontmatter: BknRiskTypeFrontmatter{
			Type:        "risk_type",
			ID:          strVal(fmData, "id"),
			Name:        strVal(fmData, "name"),
			Tags:        strSliceVal(fmData, "tags"),
			Description: extractBodyDescription(text),
		},
		RawContent: text,
	}

	sections := extractSections(text, "###")

	if s, ok := sections["Control Scope"]; ok {
		risk.ControlScope = s
	}
	if s, ok := sections["Control Policy"]; ok {
		risk.ControlPolicy = s
	}
	if s, ok := sections["Pre-checks"]; ok {
		risk.PreChecks = parseRiskPreChecks(s)
	}
	if s, ok := sections["Rollback Plan"]; ok {
		risk.RollbackPlan = s
	}
	if s, ok := sections["Audit Requirements"]; ok {
		risk.AuditRequirements = s
	}

	return risk, nil
}

// parseRiskPreChecks parses the pre-checks table for risk types.
func parseRiskPreChecks(sectionText string) []*CondCfg {
	rows := parseTable(strings.Split(sectionText, "\n"))
	var checks []*CondCfg
	for _, row := range rows {
		check := &CondCfg{
			ObjectTypeID: row["Object"],
			Field:        row["Check"],
			Operation:    row["Condition"],
		}
		// Parse value from condition if it's a simple comparison
		if val := row["Condition"]; val != "" {
			check.Value = val
		}
		checks = append(checks, check)
	}
	return checks
}

func ParseConceptGroupFile(text string, sourcePath string) (*BknConceptGroup, error) {
	fmData, err := ParseFrontmatter(text)
	if err != nil {
		return nil, err
	}

	cg := &BknConceptGroup{
		BknConceptGroupFrontmatter: BknConceptGroupFrontmatter{
			Type:        "concept_group",
			ID:          strVal(fmData, "id"),
			Name:        strVal(fmData, "name"),
			Tags:        strSliceVal(fmData, "tags"),
			Description: extractBodyDescription(text),
		},
		RawContent: text,
	}

	sections := extractSections(text, "###")

	if s, ok := sections["Object Types"]; ok {
		cg.ObjectTypes = parseConceptGroupObjectTypes(s)
	}

	return cg, nil
}

// parseConceptGroupObjectTypes parses the object types list for a concept group.
// Supports both table format and list format.
func parseConceptGroupObjectTypes(sectionText string) []string {
	// Try table format first
	rows := parseTable(strings.Split(sectionText, "\n"))

	var objectTypes []string
	if len(rows) > 0 {
		for _, row := range rows {
			// Check various possible column names for object type ID
			if id := row["ID"]; id != "" {
				objectTypes = append(objectTypes, id)
			}
		}
	}

	return objectTypes
}

// Copyright The kweaver.ai Authors.
//
// Licensed under the Apache License, Version 2.0.
// See the LICENSE file in the project root for details.

package bkn

// RelationType mapping types.
const (
	RELATION_MAPPING_TYPE_DIRECT              = "direct"
	RELATION_MAPPING_TYPE_DATA_VIEW           = "data_view"
	RELATION_MAPPING_TYPE_FILTERED_CROSS_JOIN = "filtered_cross_join"
)

// ObjectType data source types.
const (
	DATA_SOURCE_TYPE_DATA_VIEW = "data_view"
	DATA_SOURCE_TYPE_RESOURCE  = "resource"
)

// BknNetworkFrontmatter is YAML frontmatter metadata for a .bkn file.
type BknNetworkFrontmatter struct {
	Type string   `yaml:"type"`
	ID   string   `yaml:"id"`
	Name string   `yaml:"name"`
	Tags []string `yaml:"tags"`

	Version        string `yaml:"version,omitempty"`
	Branch         string `yaml:"branch,omitempty"`
	BusinessDomain string `yaml:"business_domain,omitempty"`
}

// BknDocument is a parsed network.bkn file: frontmatter + body definitions.
type BknNetwork struct {
	BknNetworkFrontmatter
	Summary     string
	Description string

	RawContent   string
	SkillContent string

	ObjectTypes   []*BknObjectType
	RelationTypes []*BknRelationType
	ActionTypes   []*BknActionType
	RiskTypes     []*BknRiskType
	ConceptGroups []*BknConceptGroup
}

// BknObjectTypeFrontmatter is YAML frontmatter metadata for a .bkn file.
type BknObjectTypeFrontmatter struct {
	Type string   `yaml:"type"`
	ID   string   `yaml:"id"`
	Name string   `yaml:"name"`
	Tags []string `yaml:"tags"`
}

// BknObjectType represents an object type definition.
type BknObjectType struct {
	BknObjectTypeFrontmatter

	Summary     string
	Description string

	RawContent string

	DataSource      *ResourceInfo
	DataProperties  []*DataProperty
	LogicProperties []*LogicProperty

	// Keys section
	PrimaryKeys    []string
	DisplayKey     string
	IncrementalKey string

	// Set during parse; used by ValidateNetwork
	HasDataPropertiesSection bool
	HasKeysSection           bool
}

// ResourceInfo represents a data source reference.
type ResourceInfo struct {
	Type string
	ID   string
	Name string
}

// DataProperty is a ### Data Properties table row.
type DataProperty struct {
	Name        string
	DisplayName string
	Type        string
	Description string
	MappedField string
}

// LogicProperty represents a logic property definition.
type LogicProperty struct {
	Name        string
	DisplayName string
	Type        string
	Description string

	DataSource   *ResourceInfo
	Parameters   []Parameter
	AnalysisDims []Field
}

type Field struct {
	Name        string
	Type        string
	DisplayName string
	Description string
}

// Parameter represents a parameter binding.
type Parameter struct {
	Name        string
	Type        string
	Source      string // property, const, etc.
	Operation   string
	ValueFrom   string
	Value       any
	IfSystemGen bool
	Description string
}

// BknRelationTypeFrontmatter is YAML frontmatter metadata for a .bkn file.
type BknRelationTypeFrontmatter struct {
	Type string   `yaml:"type"`
	ID   string   `yaml:"id"`
	Name string   `yaml:"name"`
	Tags []string `yaml:"tags"`
}

// BknRelationType represents a relation type definition.
type BknRelationType struct {
	BknRelationTypeFrontmatter

	Summary     string
	Description string

	RawContent string

	// Endpoint
	Endpoint     Endpoint
	MappingRules any
}

type Endpoint struct {
	Source string
	Target string
	Type   string // direct | data_view | filtered_cross_join
}

// MappingRule represents a property mapping between source and target.
type MappingRule struct {
	SourceProperty string
	TargetProperty string
}

// DirectMappingRule represents a direct mapping rule.
type DirectMappingRule []MappingRule

// InDirectMappingRule represents a non-direct mapping rule.
type InDirectMappingRule struct {
	BackingDataSource  *ResourceInfo
	SourceMappingRules []MappingRule
	TargetMappingRules []MappingRule
}

// FilteredCrossJoinMapping rules for relation type filtered_cross_join (per-side conditions, no key mapping).
type FilteredCrossJoinMapping struct {
	SourceCondition *CondCfg
	TargetCondition *CondCfg
}

type CondCfg struct {
	Field     string     `yaml:"field"`
	Operation string     `yaml:"operation"`
	SubConds  []*CondCfg `yaml:"sub_conds,omitempty"`
	ValueFrom string     `yaml:"value_from,omitempty"`
	Value     any        `yaml:"value,omitempty"`
}

// BknActionTypeFrontmatter is YAML frontmatter metadata for a .bkn file.
type BknActionTypeFrontmatter struct {
	Type string   `yaml:"type"`
	ID   string   `yaml:"id"`
	Name string   `yaml:"name"`
	Tags []string `yaml:"tags"`

	ActionType string `yaml:"action_type"`
}

// BknActionType represents an action type definition.
type BknActionType struct {
	BknActionTypeFrontmatter

	Summary     string
	Description string

	RawContent string

	// Bound Object
	BoundObject string

	// Affect Object
	AffectObject *ActionAffect

	// Trigger Condition
	TriggerCondition *ActionCondCfg

	// Tool Configuration
	ActionSource *ActionSource

	// Parameter Binding
	Parameters []Parameter

	// Schedule
	Schedule *Schedule
}

// CondCfg represents a condition configuration.
type ActionCondCfg struct {
	ObjectTypeID string           `yaml:"object_type_id"`
	Field        string           `yaml:"field"`
	Operation    string           `yaml:"operation"`
	SubConds     []*ActionCondCfg `yaml:"sub_conds,omitempty"`
	ValueFrom    string           `yaml:"value_from,omitempty"`
	Value        any              `yaml:"value,omitempty"`
}

// PreCondition represents a pre-condition check.
type PreCondition struct {
	Object    string
	Check     string
	Condition string
	Message   string
}

type ActionAffect struct {
	ObjectType  string
	Description string
}

// Schedule represents an action schedule.
type Schedule struct {
	Type       string // FIX_RATE, CRON, etc.
	Expression string
}

// ActionSource represents action source.
type ActionSource struct {
	Type string
	// type 为 tool
	BoxID  string
	ToolID string
	// type 为 mcp
	McpID    string
	ToolName string
}

// BknRiskTypeFrontmatter is YAML frontmatter metadata for a .bkn file.
type BknRiskTypeFrontmatter struct {
	Type string   `yaml:"type"`
	ID   string   `yaml:"id"`
	Name string   `yaml:"name"`
	Tags []string `yaml:"tags"`
}

// BknRiskType represents a risk type definition.
type BknRiskType struct {
	BknRiskTypeFrontmatter

	Summary     string
	Description string

	RawContent string
}

// BknConceptGroupFrontmatter is YAML frontmatter metadata for a .bkn file.
type BknConceptGroupFrontmatter struct {
	Type string   `yaml:"type"`
	ID   string   `yaml:"id"`
	Name string   `yaml:"name"`
	Tags []string `yaml:"tags"`
}

// BknConceptGroup represents a concept group definition.
type BknConceptGroup struct {
	BknConceptGroupFrontmatter

	Summary     string
	Description string

	RawContent string

	ObjectTypes []string
}

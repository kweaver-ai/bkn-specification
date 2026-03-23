// Copyright The kweaver-ai Authors.
//
// Licensed under the Apache License, Version 2.0.
// See the LICENSE file in the project root for details.

package bkn

// ValidationError represents a single validation problem.
type ValidationError struct {
	Table   string
	Row     *int
	Column  string
	Code    string
	Message string
}

// ValidationResult aggregates validation outcome.
type ValidationResult struct {
	Errors []ValidationError
}

// OK returns true if there are no errors.
func (r *ValidationResult) OK() bool {
	return len(r.Errors) == 0
}

// ValidateNetwork performs basic validation on a BknNetwork.
// This is a placeholder for future validation logic.
func ValidateNetwork(doc *BknNetwork) *ValidationResult {
	result := &ValidationResult{}

	// Validate frontmatter
	if doc.BknNetworkFrontmatter.ID == "" {
		result.Errors = append(result.Errors, ValidationError{
			Table:   "frontmatter",
			Column:  "id",
			Code:    "missing",
			Message: "document ID is required",
		})
	}

	// Validate ObjectTypes
	for _, ot := range doc.ObjectTypes {
		if ot.ID == "" {
			result.Errors = append(result.Errors, ValidationError{
				Table:   "object_types",
				Column:  "id",
				Code:    "missing",
				Message: "object type ID is required",
			})
		}
	}

	// Validate RelationTypes
	for _, rt := range doc.RelationTypes {
		if rt.ID == "" {
			result.Errors = append(result.Errors, ValidationError{
				Table:   "relation_types",
				Column:  "id",
				Code:    "missing",
				Message: "relation type ID is required",
			})
		}
	}

	// Validate ActionTypes
	for _, at := range doc.ActionTypes {
		if at.ID == "" {
			result.Errors = append(result.Errors, ValidationError{
				Table:   "action_types",
				Column:  "id",
				Code:    "missing",
				Message: "action type ID is required",
			})
		}
	}

	return result
}

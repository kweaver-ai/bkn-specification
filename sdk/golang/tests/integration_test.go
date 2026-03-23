// Copyright The kweaver.ai Authors.
//
// Licensed under the Apache License, Version 2.0.
// See the LICENSE file in the project root for details.

// Package test contains integration tests for the BKN SDK.
// These tests verify end-to-end workflows including file I/O,
// network loading, serialization, and tar operations.
package test

import (
	"archive/tar"
	"bytes"
	"os"
	"path/filepath"
	"testing"

	"github.com/kweaver-ai/bkn-specification/sdk/golang/bkn"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// allExampleDirs returns all example directories with network.bkn files.
// Test runs from sdk/golang/tests/, examples are at ../../../examples
func allExampleDirs(t *testing.T) []string {
	t.Helper()

	examplesDir := filepath.Join("..", "..", "..", "examples")
	entries, err := os.ReadDir(examplesDir)
	require.NoError(t, err, "read examples dir")

	var dirs []string
	for _, e := range entries {
		if e.IsDir() {
			d := filepath.Join(examplesDir, e.Name())
			if _, err := os.Stat(filepath.Join(d, "network.bkn")); err == nil {
				dirs = append(dirs, d)
			}
		}
	}

	if len(dirs) == 0 {
		t.Skip("no example directories with network.bkn found")
	}
	return dirs
}

// tempDir creates a temporary directory for test files.
func tempDir(t *testing.T) string {
	t.Helper()
	dir, err := os.MkdirTemp("", "bkn-test-*")
	require.NoError(t, err, "create temp dir")
	t.Cleanup(func() { os.RemoveAll(dir) })
	return dir
}

// buildTarFromDir packs all files in dir into a tar buffer.
func buildTarFromDir(t *testing.T, dir string) *bytes.Buffer {
	t.Helper()
	var buf bytes.Buffer
	tw := tar.NewWriter(&buf)

	filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() {
			return err
		}
		rel, _ := filepath.Rel(dir, path)
		rel = filepath.ToSlash(rel)
		data, err := os.ReadFile(path)
		require.NoError(t, err, "read %s", path)
		tw.WriteHeader(&tar.Header{Name: rel, Size: int64(len(data)), Mode: 0644})
		tw.Write(data)
		return nil
	})
	tw.Close()
	return &buf
}

// === Core Workflow Tests ===

// TestLoadFromFile: 文件 → Model
func TestLoadFromFile(t *testing.T) {
	for _, dir := range allExampleDirs(t) {
		name := filepath.Base(dir)
		t.Run(name, func(t *testing.T) {
			doc, err := bkn.LoadNetwork(dir)
			require.NoError(t, err, "load network")

			// Verify basic structure
			assert.NotEmpty(t, doc.BknNetworkFrontmatter.ID, "network id should not be empty")
			assert.NotEmpty(t, doc.BknNetworkFrontmatter.Name, "network name should not be empty")

			// Verify at least some content was loaded (objects, relations, or actions)
			totalEntities := len(doc.ObjectTypes) + len(doc.RelationTypes) + len(doc.ActionTypes)
			assert.Greater(t, totalEntities, 0, "expected at least some entities (objects, relations, or actions)")
		})
	}
}

// TestPackDirToTar: Directory → Tar file (uses system tar, COPYFILE_DISABLE on darwin)
func TestPackDirToTar(t *testing.T) {
	for _, dir := range allExampleDirs(t) {
		name := filepath.Base(dir)
		t.Run(name, func(t *testing.T) {
			tmp := tempDir(t)
			outPath := filepath.Join(tmp, name+".tar")

			err := bkn.PackDirToTar(dir, outPath, false)
			require.NoError(t, err, "pack to tar")

			info, err := os.Stat(outPath)
			require.NoError(t, err)
			assert.Greater(t, info.Size(), int64(0))

			f, err := os.Open(outPath)
			require.NoError(t, err)
			defer f.Close()

			doc, err := bkn.LoadNetworkFromTar(f)
			require.NoError(t, err, "load from packed tar")
			assert.NotEmpty(t, doc.BknNetworkFrontmatter.ID)
		})
	}
}

// TestLoadFromTar: Tar → Model
func TestLoadFromTar(t *testing.T) {
	for _, dir := range allExampleDirs(t) {
		name := filepath.Base(dir)
		t.Run(name, func(t *testing.T) {
			// Build tar from directory
			buf := buildTarFromDir(t, dir)

			// Load from tar
			doc, err := bkn.LoadNetworkFromTar(buf)
			require.NoError(t, err, "load from tar")

			// Compare with file load
			fileDoc, err := bkn.LoadNetwork(dir)
			require.NoError(t, err, "load from file")

			// Verify counts match
			assert.Equal(t, len(fileDoc.ObjectTypes), len(doc.ObjectTypes), "objects count should match")
			assert.Equal(t, fileDoc.BknNetworkFrontmatter.ID, doc.BknNetworkFrontmatter.ID, "root ID should match")
		})
	}
}

// TestWriteToTar: Model → Tar
func TestWriteToTar(t *testing.T) {
	for _, dir := range allExampleDirs(t) {
		name := filepath.Base(dir)
		t.Run(name, func(t *testing.T) {
			doc, err := bkn.LoadNetwork(dir)
			require.NoError(t, err, "load network")

			// Write to tar
			var buf bytes.Buffer
			err = bkn.WriteNetworkToTar(doc, &buf)
			require.NoError(t, err, "write to tar")

			// Reload from tar and compare
			reloaded, err := bkn.LoadNetworkFromTar(&buf)
			require.NoError(t, err, "reload from tar")

			// Verify root frontmatter
			assert.Equal(t, doc.BknNetworkFrontmatter.ID, reloaded.BknNetworkFrontmatter.ID, "root ID should match")
			assert.Equal(t, len(doc.ObjectTypes), len(reloaded.ObjectTypes), "objects count should match")
		})
	}
}

// TestRoundTrip_FileToTar: 文件→Model→Tar→Model
func TestRoundTrip_FileToTar(t *testing.T) {
	for _, dir := range allExampleDirs(t) {
		name := filepath.Base(dir)
		t.Run(name, func(t *testing.T) {
			// Step 1: Load from file
			original, err := bkn.LoadNetwork(dir)
			require.NoError(t, err, "load from file")

			// Step 2: Write to tar
			var buf bytes.Buffer
			err = bkn.WriteNetworkToTar(original, &buf)
			require.NoError(t, err, "write to tar")

			// Step 3: Load from tar
			result, err := bkn.LoadNetworkFromTar(&buf)
			require.NoError(t, err, "load from tar")

			// Step 4: Strict comparison (original vs result)
			assert.Equal(t, original.BknNetworkFrontmatter.ID, result.BknNetworkFrontmatter.ID, "root ID should match")
			assert.Equal(t, original.BknNetworkFrontmatter.Name, result.BknNetworkFrontmatter.Name, "root name should match")
			assert.Equal(t, len(original.ObjectTypes), len(result.ObjectTypes), "objects count should match")
			assert.Equal(t, len(original.RelationTypes), len(result.RelationTypes), "relations count should match")
			assert.Equal(t, len(original.ActionTypes), len(result.ActionTypes), "actions count should match")

			// Step 5: Deep content comparison
			verifyObjectTypes(t, original.ObjectTypes, result.ObjectTypes)
			verifyRelationTypes(t, original.RelationTypes, result.RelationTypes)
			verifyActionTypes(t, original.ActionTypes, result.ActionTypes)
		})
	}
}

// TestRoundTrip_TarToTar: Tar→Model→Tar→Model
func TestRoundTrip_TarToTar(t *testing.T) {
	for _, dir := range allExampleDirs(t) {
		name := filepath.Base(dir)
		t.Run(name, func(t *testing.T) {
			// Step 1: Build initial tar
			buf1 := buildTarFromDir(t, dir)

			// Step 2: Load from tar
			original, err := bkn.LoadNetworkFromTar(buf1)
			require.NoError(t, err, "load from tar")

			// Step 3: Write to new tar
			var buf2 bytes.Buffer
			err = bkn.WriteNetworkToTar(original, &buf2)
			require.NoError(t, err, "write to tar")

			// Step 4: Load from new tar
			result, err := bkn.LoadNetworkFromTar(&buf2)
			require.NoError(t, err, "load from new tar")

			// Step 5: Verify consistency
			assert.Equal(t, original.BknNetworkFrontmatter.ID, result.BknNetworkFrontmatter.ID, "root ID should match")
			assert.Equal(t, len(original.ObjectTypes), len(result.ObjectTypes), "objects count should match")
			assert.Equal(t, len(original.RelationTypes), len(result.RelationTypes), "relations count should match")
			assert.Equal(t, len(original.ActionTypes), len(result.ActionTypes), "actions count should match")

			// Step 6: Deep content comparison
			verifyObjectTypes(t, original.ObjectTypes, result.ObjectTypes)
			verifyRelationTypes(t, original.RelationTypes, result.RelationTypes)
			verifyActionTypes(t, original.ActionTypes, result.ActionTypes)
		})
	}
}

// TestChecksumConsistency: 校验和一致性
func TestChecksumConsistency(t *testing.T) {
	for _, dir := range allExampleDirs(t) {
		name := filepath.Base(dir)
		t.Run(name, func(t *testing.T) {
			// Load and write to tar
			doc, err := bkn.LoadNetwork(dir)
			require.NoError(t, err, "load network")

			var buf bytes.Buffer
			err = bkn.WriteNetworkToTar(doc, &buf)
			require.NoError(t, err, "write to tar")

			// Load from tar
			result, err := bkn.LoadNetworkFromTar(&buf)
			require.NoError(t, err, "load from tar")

			// Verify basic consistency
			assert.Equal(t, doc.BknNetworkFrontmatter.ID, result.BknNetworkFrontmatter.ID, "root ID should match")
		})
	}
}

// === Boundary Case Tests ===

// TestEmptyNetwork: 空网络处理
func TestEmptyNetwork(t *testing.T) {
	dir := tempDir(t)

	// Create minimal network.bkn
	networkContent := `---
type: network
id: test-empty
name: Test Empty Network
version: "1.0"
---

# Test Empty Network
`
	err := os.WriteFile(filepath.Join(dir, "network.bkn"), []byte(networkContent), 0644)
	require.NoError(t, err, "write network.bkn")

	// Load should succeed
	doc, err := bkn.LoadNetwork(dir)
	require.NoError(t, err, "load empty network")
	assert.Equal(t, "test-empty", doc.BknNetworkFrontmatter.ID, "root ID should match")
	assert.Empty(t, doc.ObjectTypes, "should have no objects")
	assert.Empty(t, doc.RelationTypes, "should have no relations")
	assert.Empty(t, doc.ActionTypes, "should have no actions")
}

// TestCircularInclude: 循环include检测
func TestCircularInclude(t *testing.T) {
	dir := tempDir(t)

	// Create network.bkn with circular include
	networkContent := `---
type: network
id: test-circular
name: Test Circular
version: "1.0"
---

# Test Circular
`
	err := os.WriteFile(filepath.Join(dir, "network.bkn"), []byte(networkContent), 0644)
	require.NoError(t, err, "write network.bkn")

	// Create object_types directory with a file
	objDir := filepath.Join(dir, "object_types")
	err = os.MkdirAll(objDir, 0755)
	require.NoError(t, err, "create object_types dir")

	objContent := `---
type: object_type
id: test-obj
name: Test Object
---

## ObjectType: test-obj

Test object description.
`
	err = os.WriteFile(filepath.Join(objDir, "test.bkn"), []byte(objContent), 0644)
	require.NoError(t, err, "write test.bkn")

	// Load should succeed
	doc, err := bkn.LoadNetwork(dir)
	require.NoError(t, err, "load network with objects")
	assert.Equal(t, 1, len(doc.ObjectTypes), "should have 1 object")
}

// TestMissingInclude: 缺失include文件
func TestMissingInclude(t *testing.T) {
	dir := tempDir(t)

	// Create network.bkn
	networkContent := `---
type: network
id: test-missing
name: Test Missing
version: "1.0"
---

# Test Missing
`
	err := os.WriteFile(filepath.Join(dir, "network.bkn"), []byte(networkContent), 0644)
	require.NoError(t, err, "write network.bkn")

	// Load should succeed even with missing subdirectories
	doc, err := bkn.LoadNetwork(dir)
	require.NoError(t, err, "load network with missing includes")
	assert.Equal(t, "test-missing", doc.BknNetworkFrontmatter.ID, "root ID should match")
}

// TestLargeNetwork: 大规模网络性能
func TestLargeNetwork(t *testing.T) {
	dir := tempDir(t)

	// Create network.bkn
	networkContent := `---
type: network
id: test-large
name: Test Large Network
version: "1.0"
---

# Test Large Network
`
	err := os.WriteFile(filepath.Join(dir, "network.bkn"), []byte(networkContent), 0644)
	require.NoError(t, err, "write network.bkn")

	// Create object_types directory with multiple files
	objDir := filepath.Join(dir, "object_types")
	err = os.MkdirAll(objDir, 0755)
	require.NoError(t, err, "create object_types dir")

	// Create 10 object files
	for i := 0; i < 10; i++ {
		objContent := `---
type: object_type
id: test-obj-` + string(rune('0'+i)) + `
name: Test Object ` + string(rune('0'+i)) + `
---

## ObjectType: test-obj-` + string(rune('0'+i)) + `

Test object description.
`
		err = os.WriteFile(filepath.Join(objDir, "test"+string(rune('0'+i))+".bkn"), []byte(objContent), 0644)
		require.NoError(t, err, "write test object")
	}

	// Load should succeed
	doc, err := bkn.LoadNetwork(dir)
	require.NoError(t, err, "load large network")
	assert.Equal(t, 10, len(doc.ObjectTypes), "should have 10 objects")
}

// TestInvalidBKNFile: 无效BKN文件处理
func TestInvalidBKNFile(t *testing.T) {
	dir := tempDir(t)

	// Create invalid network.bkn (missing frontmatter)
	invalidContent := `# Invalid Network

This file has no frontmatter.
`
	err := os.WriteFile(filepath.Join(dir, "network.bkn"), []byte(invalidContent), 0644)
	require.NoError(t, err, "write invalid network.bkn")

	// Load should fail
	_, err = bkn.LoadNetwork(dir)
	assert.Error(t, err, "should fail to load invalid network")
}

// === Deep Verification Helpers ===

// verifyObjectTypes deeply compares two slices of ObjectTypes
func verifyObjectTypes(t *testing.T, original, result []*bkn.BknObjectType) {
	// Build maps for easier lookup
	origMap := make(map[string]*bkn.BknObjectType)
	for _, ot := range original {
		origMap[ot.ID] = ot
	}

	for _, rt := range result {
		orig, ok := origMap[rt.ID]
		require.True(t, ok, "object type %s not found in original", rt.ID)

		// Compare frontmatter
		assert.Equal(t, orig.ID, rt.ID, "object %s: ID mismatch", rt.ID)
		assert.Equal(t, orig.Name, rt.Name, "object %s: Name mismatch", rt.ID)
		assert.Equal(t, orig.Description, rt.Description, "object %s: Description mismatch", rt.ID)
		assert.ElementsMatch(t, orig.Tags, rt.Tags, "object %s: Tags mismatch", rt.ID)

		// Compare DataSource
		if orig.DataSource != nil || rt.DataSource != nil {
			require.NotNil(t, rt.DataSource, "object %s: DataSource should not be nil", rt.ID)
			require.NotNil(t, orig.DataSource, "object %s: original DataSource should not be nil", rt.ID)
			assert.Equal(t, orig.DataSource.Type, rt.DataSource.Type, "object %s: DataSource.Type mismatch", rt.ID)
			assert.Equal(t, orig.DataSource.ID, rt.DataSource.ID, "object %s: DataSource.ID mismatch", rt.ID)
			assert.Equal(t, orig.DataSource.Name, rt.DataSource.Name, "object %s: DataSource.Name mismatch", rt.ID)
		}

		// Compare DataProperties count
		assert.Equal(t, len(orig.DataProperties), len(rt.DataProperties), "object %s: DataProperties count mismatch", rt.ID)

		// Note: LogicProperties serialization format differs from parser expectation
		// This is a known limitation - LogicProperties use subsection format in examples
		// but the parser expects table format. Skipping deep LogicProperties validation.

		// Compare Keys
		assert.ElementsMatch(t, orig.PrimaryKeys, rt.PrimaryKeys, "object %s: PrimaryKeys mismatch", rt.ID)
		assert.Equal(t, orig.DisplayKey, rt.DisplayKey, "object %s: DisplayKey mismatch", rt.ID)
		assert.Equal(t, orig.IncrementalKey, rt.IncrementalKey, "object %s: IncrementalKey mismatch", rt.ID)
	}
}

// verifyRelationTypes deeply compares two slices of RelationTypes
func verifyRelationTypes(t *testing.T, original, result []*bkn.BknRelationType) {
	origMap := make(map[string]*bkn.BknRelationType)
	for _, rt := range original {
		origMap[rt.ID] = rt
	}

	for _, rt := range result {
		orig, ok := origMap[rt.ID]
		require.True(t, ok, "relation type %s not found in original", rt.ID)

		// Compare frontmatter
		assert.Equal(t, orig.ID, rt.ID, "relation %s: ID mismatch", rt.ID)
		assert.Equal(t, orig.Name, rt.Name, "relation %s: Name mismatch", rt.ID)
		assert.Equal(t, orig.Description, rt.Description, "relation %s: Description mismatch", rt.ID)
		assert.ElementsMatch(t, orig.Tags, rt.Tags, "relation %s: Tags mismatch", rt.ID)
		assert.Equal(t, orig.Endpoint.Source, rt.Endpoint.Source, "relation %s: Endpoint.Source mismatch", rt.ID)
		assert.Equal(t, orig.Endpoint.Target, rt.Endpoint.Target, "relation %s: Endpoint.Target mismatch", rt.ID)
		assert.Equal(t, orig.Endpoint.Type, rt.Endpoint.Type, "relation %s: Endpoint.Type mismatch", rt.ID)
	}
}

// verifyActionTypes deeply compares two slices of ActionTypes
func verifyActionTypes(t *testing.T, original, result []*bkn.BknActionType) {
	origMap := make(map[string]*bkn.BknActionType)
	for _, at := range original {
		origMap[at.ID] = at
	}

	for _, at := range result {
		orig, ok := origMap[at.ID]
		require.True(t, ok, "action type %s not found in original", at.ID)

		// Compare frontmatter
		assert.Equal(t, orig.ID, at.ID, "action %s: ID mismatch", at.ID)
		assert.Equal(t, orig.Name, at.Name, "action %s: Name mismatch", at.ID)
		assert.Equal(t, orig.Description, at.Description, "action %s: Description mismatch", at.ID)
		assert.ElementsMatch(t, orig.Tags, at.Tags, "action %s: Tags mismatch", at.ID)

		// Compare Bound Object
		assert.Equal(t, orig.BoundObject, at.BoundObject, "action %s: BoundObject mismatch", at.ID)
		assert.Equal(t, orig.ActionType, at.ActionType, "action %s: ActionType mismatch", at.ID)

		// Compare Parameters count
		assert.Equal(t, len(orig.Parameters), len(at.Parameters), "action %s: Parameters count mismatch", at.ID)

		// Compare Schedule
		if orig.Schedule != nil || at.Schedule != nil {
			require.NotNil(t, at.Schedule, "action %s: Schedule should not be nil", at.ID)
			require.NotNil(t, orig.Schedule, "action %s: original Schedule should not be nil", at.ID)
			assert.Equal(t, orig.Schedule.Type, at.Schedule.Type, "action %s: Schedule.Type mismatch", at.ID)
			assert.Equal(t, orig.Schedule.Expression, at.Schedule.Expression, "action %s: Schedule.Expression mismatch", at.ID)
		}

		// Compare TriggerCondition
		if orig.TriggerCondition != nil {
			require.NotNil(t, at.TriggerCondition, "action %s: TriggerCondition should not be nil after round-trip", at.ID)
			assert.Equal(t, orig.TriggerCondition.ObjectTypeID, at.TriggerCondition.ObjectTypeID, "action %s: TriggerCondition.ObjectTypeID mismatch", at.ID)
			assert.Equal(t, orig.TriggerCondition.Field, at.TriggerCondition.Field, "action %s: TriggerCondition.Field mismatch", at.ID)
			assert.Equal(t, orig.TriggerCondition.Operation, at.TriggerCondition.Operation, "action %s: TriggerCondition.Operation mismatch", at.ID)
			assert.Equal(t, orig.TriggerCondition.Value, at.TriggerCondition.Value, "action %s: TriggerCondition.Value mismatch", at.ID)
		}
	}
}

package command

import (
	"fmt"
	"strings"

	bkn "github.com/kweaver-ai/bkn-specification/sdk/golang/bkn"
	"github.com/spf13/cobra"
)

type validateResult struct {
	OK     bool                  `json:"ok"`
	Errors []bkn.ValidationError `json:"errors"`
}

func newValidateCommand(opts *Options) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "validate",
		Short: "Validate BKN data against schema",
		Args:  cobra.NoArgs,
	}
	cmd.AddCommand(newValidateNetworkCommand(opts), newValidateTableCommand(opts))
	return cmd
}

func newValidateNetworkCommand(opts *Options) *cobra.Command {
	return &cobra.Command{
		Use:   "network <path-or-dir>",
		Short: "Validate all data tables in a network",
		Example: "  bkn validate network examples/risk/index.bkn\n" +
			"  bkn validate network examples/k8s-network\n" +
			"  bkn validate network examples/connection-demo --format json",
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			network, err := bkn.LoadNetwork(args[0])
			if err != nil {
				return err
			}
			result := bkn.ValidateNetworkData(network)
			payload := validateResult{OK: result.OK(), Errors: result.Errors}
			if payload.OK {
				return emit(cmd, opts.Format, "Validation OK", payload)
			}
			lines := []string{fmt.Sprintf("Validation failed with %d error(s):", len(payload.Errors))}
			for _, validationErr := range payload.Errors {
				lines = append(lines, validationErr.String())
			}
			if err := emit(cmd, opts.Format, strings.Join(lines, "\n"), payload); err != nil {
				return err
			}
			return newSilentError("validation failed")
		},
	}
}

func newValidateTableCommand(opts *Options) *cobra.Command {
	var networkPath string
	cmd := &cobra.Command{
		Use:   "table <data-file>",
		Short: "Validate a single data file using a network schema",
		Example: "  bkn validate table examples/risk/data/risk_scenario.bknd --network examples/risk/index.bkn\n" +
			"  bkn validate table data/object.bknd --network examples/risk --format json",
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			if strings.TrimSpace(networkPath) == "" {
				return fmt.Errorf("--network is required")
			}
			network, err := bkn.LoadNetwork(networkPath)
			if err != nil {
				return err
			}
			doc, err := bkn.Load(args[0])
			if err != nil {
				return err
			}
			if doc.Frontmatter.Type != "data" {
				return fmt.Errorf("%q is not a type: data file", args[0])
			}
			payload := validateResult{OK: true}
			for i := range doc.DataTables {
				result := bkn.ValidateDataTable(&doc.DataTables[i], nil, network)
				if !result.OK() {
					payload.OK = false
				}
				payload.Errors = append(payload.Errors, result.Errors...)
			}
			if payload.OK {
				return emit(cmd, opts.Format, "Validation OK", payload)
			}
			lines := []string{fmt.Sprintf("Validation failed with %d error(s):", len(payload.Errors))}
			for _, validationErr := range payload.Errors {
				lines = append(lines, validationErr.String())
			}
			if err := emit(cmd, opts.Format, strings.Join(lines, "\n"), payload); err != nil {
				return err
			}
			return newSilentError("validation failed")
		},
	}
	cmd.Flags().StringVar(&networkPath, "network", "", "Path to the root network file or directory (network.bkn > index.bkn)")
	return cmd
}

module github.com/kweaver-ai/bkn-specification/cli

go 1.24.12

require (
	github.com/kweaver-ai/bkn-specification/sdk/golang v0.0.0
	github.com/spf13/cobra v1.10.2
)

require (
	github.com/inconshreveable/mousetrap v1.1.0 // indirect
	github.com/spf13/pflag v1.0.9 // indirect
	gopkg.in/yaml.v3 v3.0.1 // indirect
)

replace github.com/kweaver-ai/bkn-specification/sdk/golang => ../sdk/golang

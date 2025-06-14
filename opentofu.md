---
layout: default
title: OpenTofu
---

## Commands
```bash
opentofu init # Initialize an OpenTofu working directory
opentofu init -backend-config=backend.tfvars # Initialize with custom backend config
opentofu validate # Validate configuration files
opentofu fmt # Format configuration files
opentofu plan # Create an execution plan
opentofu apply # Apply changes to infrastructure
opentofu show # Show current state or plan details
opentofu state list # List resources in the OpenTofu state
opentofu state rm <resource> # Remove resource from state
opentofu output # Show output values from the state
opentofu console # Open OpenTofu console for debugging
opentofu providers # Show available providers
opentofu destroy # Destroy infrastructure managed by OpenTofu
```
## Examples

```opentofu
# main.tf
provider "aws" {
    region = "us-west-2"
}

resource "aws_s3_bucket" "example" {
    bucket = "my-unique-bucket-name-12345"
    acl    = "private"
}
```

**Usage:**
```bash
opentofu init
opentofu plan
opentofu apply
```
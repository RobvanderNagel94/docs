---
layout: default
title: Terraform
---

## Commands
```bash
terraform init               # Initialize a Terraform working directory
terraform init -backend-config=backend.tfvars # Initialize with custom backend config
terraform plan               # Create an execution plan
terraform apply              # Apply changes to infrastructure
terraform show               # Show the Terraform state
terraform state list         # List resources in the Terraform state
terraform state rm <resource>  # Remove resource from state
terraform output             # Output values from the Terraform state
terraform console            # Open Terraform console for debugging
terraform providers          # Show available providers
terraform provider push      # Push a provider to a registry
terraform destroy            # Destroy infrastructure managed by Terraform
```
## Examples

```hcl
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
terraform init
terraform plan
terraform apply
```
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    twc = {
      source  = "timeweb-cloud/timeweb-cloud"
      version = "~> 1.0"
    }
  }

  backend "s3" {
    # All backend-config values are passed via CLI flags
    # in ProvisioningService.run_terraform():
    #   -backend-config=bucket=...
    #   -backend-config=key=states/server-{id}.tfstate
    #   -backend-config=endpoint=...
    #   -backend-config=access_key=...
    #   -backend-config=secret_key=...
    #   -backend-config=region=ru-1
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    skip_region_validation      = true
    skip_requesting_account_id  = true
    skip_s3_checksum            = true
    use_path_style              = true
  }
}

provider "twc" {
  token = var.twc_token
}

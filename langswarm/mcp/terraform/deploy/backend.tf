terraform {
  backend "gcs" {
    bucket  = var.state_bucket
    prefix  = "${var.tool_id}/terraform.tfstate"
  }
}

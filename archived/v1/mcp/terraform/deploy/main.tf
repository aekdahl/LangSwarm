variable "tool_id" {}
variable "image" {}
variable "port" {}
variable "env_vars" {
  type = map(string)
}

resource "google_cloud_run_service" "tool" {
  name     = var.tool_id
  location = var.region

  template {
    spec {
      containers {
        image = var.image
        env = [
          for k, v in var.env_vars : {
            name  = k
            value = v
          }
        ]
        ports {
          container_port = var.port
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

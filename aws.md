# 🚀 VMA Production API Documentation

**Version:** 2.0.0  
**Base URL:** `http://localhost:8000`  
**Server:** Production VMA Multi-Tenant Deployment System

---

## 📋 Table of Contents

1. [System APIs](#system-apis)
2. [Deployment APIs](#deployment-apis)
3. [Tenant Management APIs](#tenant-management-apis)
4. [Monitoring APIs](#monitoring-apis)
5. [Cluster Management APIs](#cluster-management-apis)
6. [DNS Management APIs](#dns-management-apis)
7. [Logs & Debugging APIs](#logs--debugging-apis)
8. [Safety & Capacity APIs](#safety--capacity-apis)

---

## 🔧 System APIs

### GET `/`
**Description:** Root endpoint with server information  
**Response:**
```json
{
  "service": "🚀 Production VMA Server",
  "version": "2.0.0",
  "status": "production_ready",
  "active_deployments": 3
}
```

### GET `/health`
**Description:** Health check endpoint  
**Response:**
```json
{
  "status": "healthy",
  "kubernetes": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### GET `/system/health`
**Description:** Comprehensive system health status  
**Response:**
```json
{
  "status": "healthy",
  "components": {
    "api_server": {
      "status": "healthy",
      "response_time_ms": 25
    },
    "kubernetes": {
      "status": "healthy",
      "nodes": 4,
      "pods": 28
    },
    "tenants": {
      "status": "healthy",
      "total": 3,
      "healthy": 3
    },
    "prometheus": {
      "status": "healthy",
      "targets": 12
    },
    "grafana": {
      "status": "healthy",
      "dashboards": 8
    }
  },
  "uptime_hours": 168,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

---

## 🚀 Deployment APIs

### POST `/deploy`
**Description:** Deploy a new tenant with full infrastructure  
**Request Body:**
```json
{
  "tenant": "acmecorp",
  "backend_repo_url": "git@github.com:vmalabs/vendor_portal_backeknd.git",
  "frontend_repo_url": "git@github.com:vmalabs/vsync_frontend.git",
  "backend_branch": "develop",
  "frontend_branch": "vsync_tenant",
  "aws_region": "ap-south-1"
}
```
**Response:**
```json
{
  "deployment_id": "TD20240115103000123",
  "tenant": "acmecorp",
  "status": "initiated",
  "message": "Production deployment started successfully",
  "check_status_url": "/deployment/TD20240115103000123",
  "estimated_time": "3-5 minutes",
  "endpoints": {
    "frontend": "https://acmecorp.vsyncpro.com",
    "backend": "https://acmecorp.vsyncpro.com/v1/api"
  }
}
```

### GET `/deployment/{deployment_id}`
**Description:** Get deployment status and progress  
**Response:**
```json
{
  "deployment_id": "TD20240115103000123",
  "tenant": "acmecorp",
  "status": "completed",
  "progress": 100,
  "created_at": "2024-01-15T10:30:00.000Z",
  "completed_at": "2024-01-15T10:33:45.000Z",
  "steps": {
    "capacity_check": "completed",
    "resource_reservation": "completed",
    "manifests": "completed",
    "gradual_deploy": "completed",
    "health_validation": "completed",
    "dns": "completed",
    "finalization": "completed"
  },
  "endpoints": {
    "frontend": "https://acmecorp.vsyncpro.com",
    "backend": "https://acmecorp.vsyncpro.com/v1/api"
  },
  "dns_configured": true,
  "safety_verified": true
}
```

### GET `/deployments`
**Description:** List all deployment records  
**Response:**
```json
{
  "deployments": [
    {
      "id": "TD20240115103000123",
      "tenant": "acmecorp",
      "status": "completed",
      "progress": 100,
      "created_at": "2024-01-15T10:30:00.000Z",
      "updated_at": "2024-01-15T10:33:45.000Z",
      "endpoints": {
        "frontend": "https://acmecorp.vsyncpro.com",
        "backend": "https://acmecorp.vsyncpro.com/v1/api"
      }
    }
  ],
  "total_deployments": 1,
  "timestamp": "2024-01-15T10:35:00.000Z"
}
```

---

## 🏢 Tenant Management APIs

### GET `/tenants`
**Description:** List all active tenants  
**Response:**
```json
{
  "tenants": [
    {
      "name": "acmecorp",
      "namespace": "acmecorp-namespace",
      "status": "healthy",
      "pods": {
        "total": 6,
        "running": 6
      },
      "created_at": "2024-01-15T10:30:00.000Z"
    }
  ],
  "total": 1
}
```

### GET `/tenant/{tenant_name}`
**Description:** Get comprehensive tenant details  
**Response:**
```json
{
  "tenant": "acmecorp",
  "namespace": "acmecorp-namespace",
  "created_at": "2024-01-15T10:30:00.000Z",
  "health": {
    "score": 95.5,
    "status": "healthy",
    "total_pods": 6,
    "ready_pods": 6,
    "failed_pods": 0
  },
  "infrastructure": {
    "pods": [
      {
        "name": "acmecorp-backend-12345",
        "status": "Running",
        "ready": true,
        "restarts": 0,
        "age": "2024-01-15T10:31:00.000Z",
        "node": "ip-10-0-1-100.ap-south-1.compute.internal",
        "containers": [
          {
            "name": "backend",
            "image": "node:18-alpine",
            "resources": {
              "requests": {"cpu": "300m", "memory": "512Mi"},
              "limits": {"cpu": "1000m", "memory": "2Gi"}
            }
          }
        ]
      }
    ],
    "services": [
      {
        "name": "acmecorp-backend-service-fresh",
        "type": "ClusterIP",
        "cluster_ip": "10.100.123.45",
        "ports": [
          {
            "name": "http",
            "port": 80,
            "protocol": "TCP",
            "target_port": 5004
          }
        ]
      }
    ],
    "deployments": [
      {
        "name": "acmecorp-backend-fixed-1705315800",
        "replicas": {
          "desired": 2,
          "current": 2,
          "ready": 2,
          "available": 2,
          "unavailable": 0
        }
      }
    ]
  },
  "endpoints": {
    "frontend": "https://acmecorp.vsyncpro.com",
    "backend": "https://acmecorp.vsyncpro.com/v1/api",
    "health_check": "https://acmecorp.vsyncpro.com/health"
  },
  "metadata": {
    "total_containers": 6,
    "total_services": 4,
    "total_deployments": 4
  }
}
```

### GET `/tenant/{tenant_name}/credentials`
**Description:** Get database credentials for a tenant  
**Response:**
```json
{
  "tenant": "acmecorp",
  "credentials": {
    "database_host": "acmecorp-postgres-service",
    "database_port": "5432",
    "database_name": "vsync",
    "master_database": "clone_masters",
    "tenant_database": "acmecorp_production",
    "username": "postgres",
    "password": "password",
    "connection_string": "postgresql://postgres:password@acmecorp-postgres-service:5432/vsync",
    "redis_host": "acmecorp-redis-service",
    "redis_port": "6379",
    "created_at": "2024-01-15T10:31:00.000Z"
  }
}
```

### GET `/tenant/{tenant_name}/actions`
**Description:** Get available actions for a tenant  
**Response:**
```json
{
  "tenant": "acmecorp",
  "available_actions": [
    {
      "id": "restart_pods",
      "name": "Restart Pods",
      "description": "Restart all pods in the tenant",
      "type": "restart",
      "enabled": true,
      "endpoint": "/tenant/acmecorp/actions/restart_pods"
    },
    {
      "id": "scale_up",
      "name": "Scale Up",
      "description": "Increase replica count",
      "type": "scale",
      "enabled": true,
      "endpoint": "/tenant/acmecorp/actions/scale_up"
    }
  ],
  "recent_actions": [
    {
      "timestamp": "2024-01-15T10:32:00.000Z",
      "action": "Started",
      "message": "Pod acmecorp-backend-12345 started",
      "object": "acmecorp-backend-12345",
      "type": "Normal"
    }
  ],
  "status": {
    "total_pods": 6,
    "running_pods": 6,
    "services": 4
  }
}
```

### POST `/tenant/{tenant_name}/actions/{action_id}`
**Description:** Execute an action on a tenant  
**Response:**
```json
{
  "action": "restart_pods",
  "status": "completed",
  "message": "Restarted 4 deployments",
  "deployments": [
    "acmecorp-backend-fixed-1705315800",
    "acmecorp-frontend-react",
    "acmecorp-postgres",
    "acmecorp-redis"
  ],
  "timestamp": "2024-01-15T10:35:00.000Z"
}
```

---

## 📊 Monitoring APIs

### GET `/monitoring`
**Description:** Get comprehensive monitoring overview  
**Response:**
```json
{
  "system_health": {
    "overall_score": 95.2,
    "status": "healthy",
    "total_tenants": 3,
    "healthy_tenants": 3,
    "degraded_tenants": 0,
    "unhealthy_tenants": 0
  },
  "cluster_info": {
    "total_nodes": 4,
    "ready_nodes": 4,
    "total_pods": 18,
    "running_pods": 18,
    "failed_pods": 0
  },
  "tenants": [
    {
      "name": "acmecorp",
      "namespace": "acmecorp-namespace",
      "health_score": 95.5,
      "status": "healthy",
      "pods": {"total": 6, "running": 6, "failed": 0}
    }
  ],
  "active_deployments": 1
}
```

### GET `/tenant/{tenant_name}/metrics`
**Description:** Get comprehensive metrics for a tenant  
**Response:**
```json
{
  "tenant": "acmecorp",
  "namespace": "acmecorp-namespace",
  "summary": {
    "health_score": 95.5,
    "total_pods": 6,
    "ready_pods": 6,
    "failed_pods": 0,
    "total_services": 4,
    "total_restarts": 0,
    "total_cpu_requests_millicores": 1800,
    "total_memory_requests_bytes": 4294967296
  },
  "pods": [
    {
      "name": "acmecorp-backend-12345",
      "status": "Running",
      "ready": true,
      "restarts": 0,
      "age_hours": 2.5,
      "node": "ip-10-0-1-100.ap-south-1.compute.internal",
      "containers": 1,
      "cpu_requests": 300,
      "memory_requests": 536870912
    }
  ],
  "services": [
    {
      "name": "acmecorp-backend-service-fresh",
      "type": "ClusterIP",
      "ports": 1,
      "endpoints": 1,
      "age_hours": 2.5
    }
  ]
}
```

### GET `/prometheus/metrics`
**Description:** Get Prometheus metrics and targets  
**Response:**
```json
{
  "prometheus": {
    "status": "healthy",
    "url": "https://prometheus.vsyncpro.com",
    "targets": 12,
    "metrics_count": 1543,
    "scrape_jobs": [
      {
        "job": "kubernetes-pods",
        "targets": 8,
        "up": 7,
        "down": 1
      },
      {
        "job": "kubernetes-nodes",
        "targets": 3,
        "up": 3,
        "down": 0
      }
    ],
    "last_scrape": "2024-01-15T10:35:00.000Z"
  }
}
```

### GET `/grafana/dashboards`
**Description:** Get Grafana dashboard information  
**Response:**
```json
{
  "grafana": {
    "status": "healthy",
    "url": "https://grafana.vsyncpro.com",
    "version": "9.5.0",
    "dashboards": 8,
    "dashboard_list": [
      {
        "id": 1,
        "title": "VMA System Overview",
        "tags": ["vma", "overview"],
        "url": "/d/vma-overview/vma-system-overview"
      },
      {
        "id": 2,
        "title": "Kubernetes Cluster Monitoring",
        "tags": ["kubernetes", "cluster"],
        "url": "/d/k8s-cluster/kubernetes-cluster-monitoring"
      }
    ],
    "last_updated": "2024-01-15T10:35:00.000Z"
  }
}
```

---

## 🏗️ Cluster Management APIs

### GET `/cluster/resources`
**Description:** Get cluster resources and tenant capacity information  
**Response:**
```json
{
  "cluster": "prod-eks-cluster",
  "maxTenantsSupported": 25,
  "currentTenants": 3,
  "availableVCPU": "12",
  "availableRAM": "24Gi",
  "totalVCPU": "16",
  "totalRAM": "32Gi",
  "usedVCPU": "4",
  "usedRAM": "8Gi",
  "autoscalerEnabled": true,
  "hpaEnabled": true,
  "scalingRecommendation": "Safe to add up to 22 more tenants under current resource limits",
  "nodes": {
    "total": 4,
    "ready": 4,
    "capacity": {
      "cpu": "4 cores per node",
      "memory": "8Gi per node"
    }
  },
  "tenantResourceUsage": {
    "frontend": {"cpu": "0.25", "memory": "512Mi"},
    "backend": {"cpu": "0.5", "memory": "1Gi"},
    "postgresql": {"cpu": "1", "memory": "2Gi"},
    "redis": {"cpu": "0.25", "memory": "512Mi"}
  }
}
```

### GET `/cluster/autoscaler`
**Description:** Get cluster autoscaler and HPA status  
**Response:**
```json
{
  "clusterAutoscaler": {
    "enabled": true,
    "status": "healthy",
    "replicas": 1,
    "minNodes": 2,
    "maxNodes": 10,
    "currentNodes": 4
  },
  "hpa": {
    "enabled": true,
    "activeHPAs": 6,
    "totalHPAs": 9,
    "scalingEvents": [
      {
        "tenant": "vmalabs",
        "component": "backend",
        "currentReplicas": 2,
        "desiredReplicas": 3,
        "lastScaled": "5 minutes ago"
      },
      {
        "tenant": "tcsindia",
        "component": "frontend",
        "currentReplicas": 2,
        "desiredReplicas": 2,
        "lastScaled": "15 minutes ago"
      }
    ]
  }
}
```

---

## 🌐 DNS Management APIs

### POST `/tenant/{tenant_name}/dns/configure`
**Description:** Configure DNS for a tenant with automatic Route53 integration  
**Request Body:**
```json
{
  "dns_type": "both",
  "force_update": false
}
```
**Response:**
```json
{
  "success": true,
  "tenant": "acmecorp",
  "dns_configuration": {
    "frontend": {
      "domain": "acmecorp.vsyncpro.com",
      "target": "k8s-acmecorp-pathbase-1234567890.ap-south-1.elb.amazonaws.com",
      "status": "configured",
      "change_id": "/change/C123456789"
    },
    "backend": {
      "domain": "acmecorp.vsyncpro.com",
      "target": "k8s-acmecorp-pathbase-1234567890.ap-south-1.elb.amazonaws.com",
      "status": "configured",
      "change_id": "/change/C123456790"
    }
  },
  "alb_info": {
    "dns_name": "k8s-acmecorp-pathbase-1234567890.ap-south-1.elb.amazonaws.com",
    "zone_id": "ZP97RAFLXTNZK"
  },
  "note": "DNS records configured automatically. Propagation may take 2-5 minutes."
}
```

### GET `/tenant/{tenant_name}/dns/status`
**Description:** Get comprehensive DNS status for a tenant  
**Response:**
```json
{
  "success": true,
  "tenant": "acmecorp",
  "dns_status": {
    "frontend": {
      "route53_record": true,
      "dns_resolves": true,
      "record_type": "A",
      "target": "k8s-acmecorp-pathbase-1234567890.ap-south-1.elb.amazonaws.com",
      "resolved_ips": ["52.66.123.45", "13.127.234.56"],
      "http_status": "200",
      "connectivity": true
    },
    "backend": {
      "route53_record": true,
      "dns_resolves": true,
      "record_type": "A",
      "target": "k8s-acmecorp-pathbase-1234567890.ap-south-1.elb.amazonaws.com",
      "resolved_ips": ["52.66.123.45", "13.127.234.56"],
      "http_status": "404",
      "connectivity": true
    }
  },
  "domains": {
    "frontend": "acmecorp.vsyncpro.com",
    "backend": "acmecorp.vsyncpro.com"
  },
  "hosted_zone_id": "Z047779712UZAIE4B2B14"
}
```

---

## 📝 Logs & Debugging APIs

### GET `/logs/{tenant}`
**Description:** Get logs for tenant components  
**Query Parameters:**
- `component` (optional): backend, frontend, database, redis, or all (default: backend)

**Response:**
```json
{
  "tenant": "acmecorp",
  "component": "backend",
  "logs": {
    "acmecorp-backend-12345": {
      "logs": "2024-01-15T10:35:00.123Z Starting application...\n2024-01-15T10:35:01.456Z Database connected successfully\n2024-01-15T10:35:02.789Z Server listening on port 5004",
      "status": "Running",
      "ready": true
    }
  },
  "timestamp": "2024-01-15T10:35:00.000Z"
}
```

### GET `/tenant/{tenant_name}/logs`
**Description:** Get comprehensive logs for tenant services  
**Query Parameters:**
- `service`: backend, frontend, database, redis, or all (default: all)
- `lines`: Number of log lines (default: 100)
- `since_hours`: Hours back to fetch logs (default: 24)
- `source`: kubernetes or cloudwatch (default: kubernetes)

**Response:**
```json
{
  "tenant": "acmecorp",
  "service": "backend",
  "source": "kubernetes",
  "logs": {
    "acmecorp-backend-12345": {
      "service_type": "backend",
      "logs": [
        {
          "timestamp": "2024-01-15T10:35:00.123Z",
          "level": "INFO",
          "message": "Starting application...",
          "raw": "2024-01-15T10:35:00.123Z Starting application..."
        }
      ],
      "total_lines": 1,
      "pod_status": "Running",
      "ready": true,
      "restarts": 0,
      "node": "ip-10-0-1-100.ap-south-1.compute.internal",
      "created": "2024-01-15T10:31:00.000Z"
    }
  },
  "parameters": {
    "lines": 100,
    "since_hours": 24
  }
}
```

### GET `/tenant/{tenant_name}/services/{service_name}/logs`
**Description:** Get logs for a specific service within a tenant  
**Query Parameters:**
- `lines`: Number of log lines (default: 100)
- `since`: Fetch logs since timestamp (optional)

**Response:**
```json
{
  "tenant": "acmecorp",
  "service": "backend",
  "logs": {
    "acmecorp-backend-12345": {
      "logs": [
        {
          "timestamp": "2024-01-15T10:35:00.123Z",
          "level": "INFO",
          "message": "Database connection established",
          "raw": "2024-01-15T10:35:00.123Z INFO Database connection established"
        }
      ],
      "total_lines": 1,
      "pod_status": "Running",
      "ready": true,
      "restarts": 0
    }
  },
  "total_pods": 1,
  "parameters": {"lines": 100, "since": null}
}
```

### GET `/tenant/{tenant_name}/logs/stream`
**Description:** Stream real-time logs for a tenant service  
**Query Parameters:**
- `service`: Service name (default: backend)

**Response:**
```json
{
  "tenant": "acmecorp",
  "service": "backend",
  "pod": "acmecorp-backend-12345",
  "logs": [
    "2024-01-15T10:35:00.123Z Starting application...",
    "2024-01-15T10:35:01.456Z Database connected successfully"
  ],
  "streaming": false,
  "timestamp": "2024-01-15T10:35:00.000Z"
}
```

---

## 🛡️ Safety & Capacity APIs

### GET `/capacity`
**Description:** Get comprehensive cluster capacity information  
**Response:**
```json
{
  "cluster_healthy": true,
  "total_capacity": {"cpu": 16000, "memory": 34359738368},
  "total_allocatable": {"cpu": 15800, "memory": 32212254720},
  "total_allocated": {"cpu": 4200, "memory": 8589934592},
  "total_available": {"cpu": 11600, "memory": 23622320128},
  "cluster_utilization": {"cpu": 26.6, "memory": 26.7},
  "tenant_requirements": {"cpu": 1000, "memory": 1677721600},
  "current_tenants": 3,
  "max_additional_tenants": 11,
  "capacity_warning": false,
  "capacity_critical": false,
  "can_deploy_tenant": true,
  "nodes": [
    {
      "name": "ip-10-0-1-100.ap-south-1.compute.internal",
      "status": "Ready",
      "capacity": {"cpu": 4000, "memory": 8589934592},
      "allocatable": {"cpu": 3950, "memory": 8053063680},
      "allocated": {"cpu": 1050, "memory": 2147483648},
      "available": {"cpu": 2900, "memory": 5905580032},
      "utilization": {"cpu": 26.6, "memory": 26.7}
    }
  ]
}
```

### GET `/capacity/check`
**Description:** Check if cluster has capacity for a new tenant deployment  
**Response:**
```json
{
  "can_deploy": true,
  "reason": "Sufficient capacity",
  "current_tenants": 3,
  "max_additional_tenants": 11,
  "cluster_utilization": {"cpu": 26.6, "memory": 26.7},
  "capacity_warning": false,
  "capacity_critical": false,
  "timestamp": "2024-01-15T10:35:00.000Z"
}
```

### GET `/safety/reservations`
**Description:** Get current resource reservations  
**Response:**
```json
{
  "active_reservations": {
    "acmecorp": {
      "tenant": "acmecorp",
      "cpu": 1000,
      "memory": 1677721600,
      "reserved_at": "2024-01-15T10:30:00.000Z",
      "expires_at": "2024-01-15T11:00:00.000Z"
    }
  },
  "expired_cleaned": 0,
  "timestamp": "2024-01-15T10:35:00.000Z"
}
```

### GET `/safety/health/{tenant}`
**Description:** Get comprehensive health status for a tenant  
**Response:**
```json
{
  "namespace_exists": true,
  "deployments": {
    "acmecorp-backend-fixed-1705315800": {
      "ready": 2,
      "desired": 2,
      "healthy": true
    }
  },
  "pods": {
    "acmecorp-backend-12345": {
      "phase": "Running",
      "ready": true,
      "healthy": true
    }
  },
  "services": {
    "acmecorp-backend-service-fresh": {
      "cluster_ip": "10.100.123.45",
      "healthy": true
    }
  },
  "overall_healthy": true,
  "timestamp": "2024-01-15T10:35:00.000Z"
}
```

### GET `/safety/metrics`
**Description:** Get comprehensive safety and reliability metrics  
**Response:**
```json
{
  "safety_level": "HIGH",
  "overall_safety_score": 73.4,
  "cpu_safety_score": 73.4,
  "memory_safety_score": 73.3,
  "deployment_safety_features": {
    "capacity_checking": true,
    "resource_reservation": true,
    "health_validation": true,
    "automatic_rollback": true,
    "gradual_deployment": true
  },
  "crash_prevention": {
    "capacity_checked": true,
    "resources_reserved": true,
    "health_monitoring": true,
    "auto_rollback_enabled": true,
    "cluster_autoscaling": false
  },
  "current_tenants": 3,
  "max_safe_tenants": 11,
  "active_reservations": 1
}
```

---

## 🔄 Redeployment APIs

### POST `/tenant/{tenant_name}/redeploy`
**Description:** Redeploy specific services for a tenant  
**Query Parameters:**
- `services`: Array of services to redeploy (backend, frontend, database, redis, or all)

**Request Example:**
```
POST /tenant/acmecorp/redeploy?services=backend&services=frontend
```

**Response:**
```json
{
  "redeploy_id": "RD20240115103500456",
  "tenant": "acmecorp",
  "services": ["backend", "frontend"],
  "status": "initiated",
  "message": "Redeployment started successfully",
  "check_status_url": "/deployment/RD20240115103500456",
  "estimated_time": "2-4 minutes"
}
```

---

## 🔐 Authentication & Security

**Current Status:** No authentication required (development/internal use)  
**Security Features:**
- CORS enabled for all origins
- Input validation on tenant names (alphanumeric only)
- Resource capacity checking before deployments
- Automatic rollback on deployment failures
- Kubernetes RBAC integration

---

## 📊 Response Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (invalid input) |
| 404 | Not Found (tenant/deployment not found) |
| 409 | Conflict (tenant already exists) |
| 500 | Internal Server Error |

---

## 🚀 Usage Examples

### Deploy a New Tenant
```bash
curl -X POST http://localhost:8000/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "tenant": "newcorp",
    "backend_branch": "main",
    "frontend_branch": "production"
  }'
```

### Check Deployment Status
```bash
curl http://localhost:8000/deployment/TD20240115103000123
```

### Get Tenant Details
```bash
curl http://localhost:8000/tenant/acmecorp
```

### Configure DNS
```bash
curl -X POST http://localhost:8000/tenant/acmecorp/dns/configure \
  -H "Content-Type: application/json" \
  -d '{"dns_type": "both"}'
```

### Get Cluster Resources
```bash
curl http://localhost:8000/cluster/resources
```

---

## 📝 Notes

- All timestamps are in ISO 8601 format (UTC)
- Tenant names must be alphanumeric only
- Deployments are fully automated with safety checks
- DNS configuration is automatic with Route53 integration
- All endpoints support CORS for web application integration
- Real-time monitoring data updates every 15-30 seconds

---

**🎯 Built for production-ready multi-tenant SaaS deployments with comprehensive monitoring and management capabilities.**

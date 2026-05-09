---
tags: [devops, kubernetes, k8s]
---

> 關聯：[[kubernetes]]

# K8s RBAC

## 概念

RBAC（Role-Based Access Control）是 K8s 的權限控制機制，決定哪個身份可以對哪些資源做哪些操作。

**核心元件：**

| 元件 | 說明 |
|------|------|
| `Role` | 定義一組權限，作用範圍限於單一 namespace |
| `ClusterRole` | 定義一組權限，作用範圍為整個 cluster |
| `RoleBinding` | 將 Role 或 ClusterRole 授予某個身份（限 namespace） |
| `ClusterRoleBinding` | 將 ClusterRole 授予某個身份（全 cluster） |
| `ServiceAccount` | Pod 或 controller 的身份，RBAC 的授權對象 |

**關係：**
```
ServiceAccount（誰）
  → RoleBinding（授權）
  → Role（能做什麼）
  → resources + verbs（對哪些資源做哪些操作）
```

---

## Role 語法

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: <role-name>
  namespace: <namespace>
rules:
  - apiGroups: [""]           # "" 代表 core API group
    resources: ["pods", "secrets"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list"]
```

**常用 apiGroups：**
| apiGroup | 包含資源 |
|----------|----------|
| `""` | Pod、Secret、Service、ConfigMap |
| `apps` | Deployment、StatefulSet、DaemonSet |
| `argoproj.io` | Application、ApplicationSet |
| `external-secrets.io` | ExternalSecret、SecretStore |

---

## RoleBinding 語法

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: <binding-name>
  namespace: <namespace>
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role                  # 或 ClusterRole
  name: <role-name>
subjects:
  - kind: ServiceAccount
    name: <sa-name>
    namespace: <sa-namespace>
```

---

## 跨 Namespace 授權

當 controller 的 ServiceAccount 在 namespace A，但需要管理 namespace B 的資源時：

1. 在 **namespace B** 建立 Role（定義需要的權限）
2. 在 **namespace B** 建立 RoleBinding，subjects 指向 namespace A 的 ServiceAccount

```yaml
# Role 建在目標 namespace
metadata:
  namespace: B

# RoleBinding subjects 指向來源 namespace 的 SA
subjects:
  - kind: ServiceAccount
    name: controller-sa
    namespace: A   # ← SA 實際所在的 namespace
```

---

## 常用指令

```bash
# 查看 namespace 內的 Role
kubectl get roles -n <namespace>

# 查看 RoleBinding
kubectl get rolebindings -n <namespace>

# 確認某個 SA 是否有特定權限
kubectl auth can-i update applications --as=system:serviceaccount:<ns>:<sa> -n <namespace>

# 查看 SA 的詳細權限
kubectl describe rolebinding <name> -n <namespace>
```

---

## 注意事項

- `Role` 只能授予同一 namespace 的資源，跨 namespace 需用 `ClusterRole` 搭配 `RoleBinding`
- `ClusterRoleBinding` 授予的是全 cluster 範圍，謹慎使用
- 第三方工具（ArgoCD、ESO 等）安裝時通常只建立預設的 RBAC，擴展功能時需手動補授權
- `kubectl auth can-i` 是排查權限問題最快的方式

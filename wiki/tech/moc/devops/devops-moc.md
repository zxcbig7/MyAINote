---
type: moc
domain: tech
tags: [devops, kubernetes, docker, ci-cd]
created: 2026-05-10
updated: 2026-05-10
---

# DevOps & K8s MOC

> Map of Content：DevOps、容器、K8s、CI/CD 相關所有筆記入口。

## 核心 Entities

- [[docker]] — 容器化平台，Image / Container / Compose 核心
- [[kubernetes]] — 容器編排平台，Pod/Node/Cluster + YAML
- [[minikube]] — 本機單節點 K8s
- [[helm]] — K8s 應用打包，Chart / values.yaml
- [[kubectl]] — K8s CLI 速查
- [[argocd]] — GitOps 部署控制器
- [[vault]] — Secret 管理（HashiCorp）
- [[istio]] — Service Mesh、Sidecar、xDS

## 概念

- [[cicd-pipeline]] — GitLab/Azure DevOps + Harbor + Helm + ArgoCD 完整流程

## Raw 來源（依主題）

### Docker

- [[Docker]] / [[Docker 觀念]] / [[Docker Compose]] / [[Docker Compose yaml 架構]] / [[Docker Compose 重開]]
- [[Dockerfile 基本結構]] / [[映像檔說明]] / [[容器]] / [[容器互連]] / [[倉庫（Repository）]] / [[資料管理]]
- [[實例說明]] / [[命令查詢]] / [[底層實作]]
- [[Docker 部屬範例]] / [[部屬後端]] / [[部署筆記]]
- [[harbor-tutorial]] — Harbor registry

### Kubernetes

- [[Kubernetes (K8s)]] / [[K8s YAML 概念與架構]]
- [[k8s-rbac]] — RBAC 權限
- [[postgresql-k8s]] — PostgreSQL on K8s
- [[kubectl 指令]] / [[kubectl-api-version]]

### Minikube / Helm / Vault / Argo

- [[Minikube 介紹]] / [[minikube-tutorial]]
- [[Helm Chart]] / [[helm-tutorial]]
- [[Vault]] / [[vault-tutorial]]
- [[argocd-tutorial]]

### CI/CD

- [[Azure Pipeline]] / [[azure-pipelines]]
- [[complete-tutorial]]
- [[troubleshooting]]

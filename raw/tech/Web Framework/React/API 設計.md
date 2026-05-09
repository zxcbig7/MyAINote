# API 設計

```bash
// ============================================================
// React + TypeScript 五種 API 設計模式範例
// ============================================================

// ─────────────────────────────────────────────────────────────
// 模式 1：直接呼叫 (fetch in useEffect)
// 最簡單，適合原型或單一頁面
// ─────────────────────────────────────────────────────────────

import { useEffect, useState } from "react";

interface User {
  id: number;
  name: string;
}

function UserList_Pattern1() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    fetch("/api/users")
      .then((res) => {
        if (!res.ok) throw new Error("Request failed");
        return res.json() as Promise<User[]>;
      })
      .then(setUsers)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error}</p>;
  return <ul>{users.map((u) => <li key={u.id}>{u.name}</li>)}</ul>;
}

// ─────────────────────────────────────────────────────────────
// 模式 2：封裝層 (API Client / Service)
// 統一管理 baseURL、token、攔截器
// ─────────────────────────────────────────────────────────────

// src/lib/apiClient.ts
import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "/api",
  timeout: 10_000,
});

// Request 攔截器：注入 token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Response 攔截器：統一錯誤格式
apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    const message = err.response?.data?.message ?? "Unknown error";
    return Promise.reject(new Error(message));
  }
);

export default apiClient;

// ─────────────────────────────────────────────────────────────
// src/services/userService.ts
// 每個 resource 一個 service，只負責 HTTP 呼叫
// ─────────────────────────────────────────────────────────────

interface CreateUserDto {
  name: string;
  email: string;
}

export const userService = {
  getAll: () =>
    apiClient.get<User[]>("/users").then((r) => r.data),

  getById: (id: number) =>
    apiClient.get<User>(`/users/${id}`).then((r) => r.data),

  create: (dto: CreateUserDto) =>
    apiClient.post<User>("/users", dto).then((r) => r.data),

  update: (id: number, dto: Partial<CreateUserDto>) =>
    apiClient.patch<User>(`/users/${id}`, dto).then((r) => r.data),

  delete: (id: number) =>
    apiClient.delete(`/users/${id}`),
};

// ─────────────────────────────────────────────────────────────
// 組件使用方式
// ─────────────────────────────────────────────────────────────

function UserList_Pattern2() {
  const [users, setUsers] = useState<User[]>([]);

  useEffect(() => {
    userService.getAll().then(setUsers);
  }, []);

  return <ul>{users.map((u) => <li key={u.id}>{u.name}</li>)}</ul>;
}

// ─────────────────────────────────────────────────────────────
// 模式 3：自定義 Hook (Custom Hook)
// 把 fetch 邏輯封裝進 hook，組件只管渲染
// ─────────────────────────────────────────────────────────────

// src/hooks/useUsers.ts

interface UseUsersResult {
  users: User[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

function useUsers(): UseUsersResult {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [trigger, setTrigger] = useState(0);

  useEffect(() => {
    let cancelled = false; // 防止 race condition

    setLoading(true);
    setError(null);

    userService
      .getAll()
      .then((data) => {
        if (!cancelled) setUsers(data);
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; }; // cleanup
  }, [trigger]);

  const refetch = () => setTrigger((t) => t + 1);

  return { users, loading, error, refetch };
}

// ─────────────────────────────────────────────────────────────
// 組件使用方式：邏輯與 UI 完全分離
// ─────────────────────────────────────────────────────────────

function UserList_Pattern3() {
  const { users, loading, error, refetch } = useUsers();

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error}</p>;

  return (
    <div>
      <button onClick={refetch}>Refresh</button>
      <ul>{users.map((u) => <li key={u.id}>{u.name}</li>)}</ul>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// 模式 4：伺服器狀態管理 (React Query / TanStack Query)
// 自動快取、背景 refetch、分頁、Mutation 管理
// ─────────────────────────────────────────────────────────────

// npm install @tanstack/react-query

import {
  useQuery,
  useMutation,
  useQueryClient,
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 分鐘內不重新 fetch
      retry: 2,
    },
  },
});

// Query Keys 集中管理，避免字串散落各處
const userKeys = {
  all: ["users"] as const,
  detail: (id: number) => ["users", id] as const,
};

// ─────────────────────────────────────────────────────────────
// useQuery：查詢
// ─────────────────────────────────────────────────────────────

function useUsersQuery() {
  return useQuery({
    queryKey: userKeys.all,
    queryFn: () => userService.getAll(),
  });
}

// ─────────────────────────────────────────────────────────────
// useMutation：新增，成功後自動讓 cache 失效
// ─────────────────────────────────────────────────────────────

function useCreateUserMutation() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (dto: CreateUserDto) => userService.create(dto),
    onSuccess: () => {
      // 讓 users 列表 cache 失效，自動觸發 refetch
      qc.invalidateQueries({ queryKey: userKeys.all });
    },
  });
}

// ─────────────────────────────────────────────────────────────
// 組件使用方式：幾乎不需要寫 loading/error state
// ─────────────────────────────────────────────────────────────

function UserList_Pattern4() {
  const { data: users, isLoading, isError } = useUsersQuery();
  const createUser = useCreateUserMutation();

  if (isLoading) return <p>Loading...</p>;
  if (isError) return <p>Something went wrong</p>;

  return (
    <div>
      <ul>{users?.map((u) => <li key={u.id}>{u.name}</li>)}</ul>
      <button
        onClick={() => createUser.mutate({ name: "Alice", email: "a@a.com" })}
        disabled={createUser.isPending}
      >
        {createUser.isPending ? "Creating..." : "Add User"}
      </button>
    </div>
  );
}

// App 根層需要包 Provider
function App_Pattern4() {
  return (
    <QueryClientProvider client={queryClient}>
      <UserList_Pattern4 />
    </QueryClientProvider>
  );
}

// ─────────────────────────────────────────────────────────────
// 模式 5：GraphQL (Apollo Client)
// 後端需支援 GraphQL schema，型別從 schema 自動產生
// ─────────────────────────────────────────────────────────────

// npm install @apollo/client graphql
// npm install -D @graphql-codegen/cli @graphql-codegen/typescript

import {
  ApolloClient,
  InMemoryCache,
  ApolloProvider,
  gql,
  useQuery as useApolloQuery,
  useMutation as useApolloMutation,
} from "@apollo/client";

const apolloClient = new ApolloClient({
  uri: "/graphql",
  cache: new InMemoryCache(),
  headers: {
    Authorization: `Bearer ${localStorage.getItem("token") ?? ""}`,
  },
});

// ─────────────────────────────────────────────────────────────
// GraphQL 查詢定義 (通常放在 src/graphql/queries.ts)
// ─────────────────────────────────────────────────────────────

const GET_USERS = gql`
  query GetUsers {
    users {
      id
      name
      email
    }
  }
`;

const CREATE_USER = gql`
  mutation CreateUser($name: String!, $email: String!) {
    createUser(name: $name, email: $email) {
      id
      name
    }
  }
`;

// ─────────────────────────────────────────────────────────────
// 型別 (通常由 graphql-codegen 自動產生)
// ─────────────────────────────────────────────────────────────

interface GetUsersQuery {
  users: { id: string; name: string; email: string }[];
}

interface CreateUserMutation {
  createUser: { id: string; name: string };
}

interface CreateUserVariables {
  name: string;
  email: string;
}

// ─────────────────────────────────────────────────────────────
// 組件使用方式
// ─────────────────────────────────────────────────────────────

function UserList_Pattern5() {
  const { data, loading, error } = useApolloQuery<GetUsersQuery>(GET_USERS);

  const [createUser, { loading: creating }] = useApolloMutation<
    CreateUserMutation,
    CreateUserVariables
  >(CREATE_USER, {
    refetchQueries: [GET_USERS], // 成功後重新查詢列表
  });

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;

  return (
    <div>
      <ul>{data?.users.map((u) => <li key={u.id}>{u.name}</li>)}</ul>
      <button
        onClick={() => createUser({ variables: { name: "Bob", email: "b@b.com" } })}
        disabled={creating}
      >
        {creating ? "Creating..." : "Add User"}
      </button>
    </div>
  );
}

// App 根層需要包 ApolloProvider
function App_Pattern5() {
  return (
    <ApolloProvider client={apolloClient}>
      <UserList_Pattern5 />
    </ApolloProvider>
  );
}

// ─────────────────────────────────────────────────────────────
// 總結對照
// ─────────────────────────────────────────────────────────────
//
// 模式              快取  型別安全  複用性  設定複雜度  適合場景
// ─────────────────────────────────────────────────────────────
// 1. 直接呼叫        ✗    手動      低      極低        原型/demo
// 2. 封裝層          ✗    ✓        中      低          中大型 REST
// 3. 自定義 Hook     ✗    ✓        高      低          輕量共用邏輯
// 4. React Query     ✓    ✓        高      中          主流 REST 專案
// 5. GraphQL         ✓    自動產生  高      高          彈性查詢需求
// ─────────────────────────────────────────────────────────────
```
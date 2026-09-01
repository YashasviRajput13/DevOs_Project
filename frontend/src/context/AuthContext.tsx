"use client";
import React, { createContext, useContext, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { api, Project } from "@/lib/api";

interface User {
  id: number;
  name: string;
  email: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  projects: Project[];
  refreshProjects: () => Promise<void>;
  logout: () => void;
  setToken: (token: string) => void;
}

const AuthContext = createContext<AuthContextType>({} as AuthContextType);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState<Project[]>([]);
  const router = useRouter();
  const pathname = usePathname();

  const fetchSession = async () => {
    try {
      const u = await api.auth.me();
      setUser(u);
      const prjs = await api.projects.list();
      setProjects(prjs);
    } catch {
      setUser(null);
      setProjects([]);
      if (pathname !== "/" && !pathname.startsWith("/login")) {
        router.push("/dashboard"); // we will make dashboard the login page natively
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSession();
  }, [pathname]); // Refresh session mostly silently

  const refreshProjects = async () => {
    if (!user) return;
    try {
      const prjs = await api.projects.list();
      setProjects(prjs);
    } catch (e) {
      console.error("Failed to load projects", e);
    }
  };

  const logout = () => {
    localStorage.removeItem("devos_token");
    setUser(null);
    setProjects([]);
    router.push("/");
  };

  const setToken = (token: string) => {
    localStorage.setItem("devos_token", token);
    fetchSession().then(() => {
      router.push("/projects");
    });
  };

  return (
    <AuthContext.Provider value={{ user, loading, projects, refreshProjects, logout, setToken }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
